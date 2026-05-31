"""Orchestrator for the multi-agent workflow."""

import logging
from pathlib import Path
from typing import Optional, Literal, Any, Callable

from langgraph.graph import StateGraph, END

from config import Settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from tools.search_tool import SearchTool
from tools.docker_tool import DockerTool
from agents.planner import PlannerAgent
from agents.searcher import SearcherAgent
from agents.coder import CoderAgent
from agents.validator import ValidatorAgent
from models import AgentState, Issue, WorkflowResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates the multi-agent workflow using LangGraph."""
    
    def __init__(
        self,
        github_tool: GitHubTool,
        git_tool: GitTool,
        settings: Settings,
    ):
        """
        Initialize orchestrator.
        
        Args:
            github_tool: GitHub tool instance
            git_tool: Git tool instance
            settings: Application settings
        """
        self.github_tool = github_tool
        self.git_tool = git_tool
        self.settings = settings
        
        self.search_tool = SearchTool(settings.workspace_dir)
        
        try:
            self.docker_tool = DockerTool()
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_tool = None
        
        self.planner = PlannerAgent(
            settings.gemini_api_key,
            settings.gemini_planning_model,
        )
        self.searcher = SearcherAgent(self.search_tool)
        self.coder = CoderAgent(
            settings.gemini_api_key,
            git_tool,
            settings.gemini_coding_model,
        )
        self.validator = ValidatorAgent(self.docker_tool) if self.docker_tool else None
        
        self.graph = self._build_graph()
        
        logger.info("Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("code", self._code_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("finalize", self._finalize_node)
        
        workflow.set_entry_point("plan")
        
        workflow.add_edge("plan", "search")
        workflow.add_edge("search", "code")
        
        workflow.add_conditional_edges(
            "code",
            self._coder_decision,
            {
                "search": "search",
                "validate": "validate",
                "finalize": "finalize"
            }
        )
        
        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {
                "retry_code": "code",
                "retry_plan": "plan",
                "finalize": "finalize",
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _plan_node(self, state: AgentState) -> AgentState:
        """Planner node."""
        logger.info("=== PLANNING PHASE ===")
        return self.planner.plan(state)
    
    def _search_node(self, state: AgentState) -> AgentState:
        """Searcher node."""
        logger.info("=== SEARCH PHASE ===")
        if state.error:
            return state
        return self.searcher.search(state)
    
    def _code_node(self, state: AgentState) -> AgentState:
        """Coder node."""
        logger.info("=== CODING PHASE ===")
        if state.error:
            return state
        return self.coder.code(state)
    
    def _validate_node(self, state: AgentState) -> AgentState:
        """Validator node."""
        logger.info("=== VALIDATION PHASE ===")
        if state.error or not self.validator:
            state.validation_passed = True
            return state
        return self.validator.validate(state)
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalization node."""
        logger.info("=== FINALIZATION PHASE ===")
        return state
    
    def _coder_decision(self, state: AgentState) -> Literal["search", "validate", "finalize"]:
        """Decide next step after coding."""
        if state.error:
            if "context" in state.error.lower() or "no_changes" in state.error.lower():
                state.error = None
                return "search"
            return "finalize"
        return "validate"
        
    def _should_retry(self, state: AgentState) -> Literal["retry_code", "retry_plan", "finalize"]:
        """Decide whether to retry code generation."""
        if self.validator and self.validator.should_retry(state):
            logger.info("Retrying code generation...")
            if state.retry_count > 1:
                return "retry_plan"
            return "retry_code"
        return "finalize"
    
    def run(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        issue: Issue,
        repo_path: Path,
        skip_tests: bool = False,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """
        Run the complete workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            issue: Issue object
            repo_path: Path to cloned repository
            skip_tests: Skip test execution
            dry_run: Don't create PR
            
        Returns:
            WorkflowResult with outcome
        """
        logger.info("Starting workflow")
        
        try:
            initial_state = AgentState(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                issue=issue,
                repo_path=str(repo_path),
            )
            
            final_dict = self.graph.invoke(initial_state)
            if isinstance(final_dict, dict):
                final_state = AgentState(**final_dict)
            else:
                final_state = final_dict
            
            
            trace_dicts = [
                {"agent": step.agent, "message": step.message, "timestamp": step.timestamp}
                for step in (final_state.reasoning_trace or [])
            ]
            
            if final_state.error:
                logger.error(f"Workflow failed: {final_state.error}")
                return WorkflowResult(
                    success=False,
                    error=final_state.error,
                    reasoning_trace=trace_dicts,
                )
            
            if not final_state.validation_passed:
                logger.error("Validation failed")
                return WorkflowResult(
                    success=False,
                    error="Code changes failed validation tests",
                    reasoning_trace=trace_dicts,
                )
            
            commit_message = f"AI Fix: Resolve issue #{issue_number}\n\n{issue.title}"
            self.git_tool.commit_changes(
                repo_path,
                commit_message,
            )
            
            changed_files = self.git_tool.get_changed_files(repo_path)
            
            if not dry_run:
                # Fork the repository first if not owned by user
                fork_owner, fork_repo = self.github_tool.fork_repository(owner, repo)
                
                if fork_owner.lower() != owner.lower():
                    logger.info(f"Using fork-first push strategy. Pointing local clone to fork: {fork_owner}/{fork_repo}")
                    fork_url = f"https://github.com/{fork_owner}/{fork_repo}.git"
                    from git import Repo as GitRepo
                    git_repo = GitRepo(repo_path)
                    git_repo.remotes.origin.set_url(fork_url)
                
                self.git_tool.push_branch(
                    repo_path,
                    final_state.branch_name,
                    self.github_tool.token,
                )
                
                pr_body = self._generate_pr_body(final_state)
                
                head_branch = f"{fork_owner}:{final_state.branch_name}" if fork_owner.lower() != owner.lower() else final_state.branch_name
                
                pr_url = self.github_tool.create_pull_request(
                    owner,
                    repo,
                    f"Fix: {issue.title} (#{issue_number})",
                    pr_body,
                    head_branch,
                    draft=True,
                )
                
                logger.info(f"Created draft PR: {pr_url}")
                
                return WorkflowResult(
                    success=True,
                    branch_name=final_state.branch_name,
                    files_changed=changed_files,
                    pr_url=pr_url,
                    reasoning_trace=trace_dicts,
                )
            else:
                logger.info("Dry run - skipping PR creation")
                return WorkflowResult(
                    success=True,
                    branch_name=final_state.branch_name,
                    files_changed=changed_files,
                    reasoning_trace=trace_dicts,
                )
            
        except Exception as e:
            logger.exception("Workflow failed with exception")
            return WorkflowResult(
                success=False,
                error=str(e),
            )
    
    def _generate_pr_body(self, state: AgentState) -> str:
        """Generate PR description."""
        body_parts = [
            f"Resolves #{state.issue_number}",
            "",
            "### What changed",
            "",
            state.strategy or "Implemented the requested changes for this issue.",
            "",
            "### Files modified",
            "",
        ]
        
        if state.changes:
            for change in state.changes:
                body_parts.append(f"- `{change.file_path}`: {change.explanation}")
        
        if state.test_result:
            body_parts.extend([
                "",
                "### Testing",
                "",
            ])
            if state.test_result.success:
                body_parts.append(f"✅ All tests passed ({state.test_result.duration:.2f}s)")
            else:
                body_parts.append("❌ Some tests failed during verification - please review.")
        
        body_parts.extend([
            "",
            "---",
            f"<sub>*Generated by [RepoRepair](https://github.com/tanishbhandari11t/Repo-Repair) made by Tanish*</sub>",
        ])
        
        return "\n".join(body_parts)
