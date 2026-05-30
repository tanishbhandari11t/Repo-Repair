"""Coder agent for generating code fixes."""

import logging
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from tools.git_tool import GitTool
from models import AgentState, CodeChange

logger = logging.getLogger(__name__)


class CoderAgent:
    """Agent that generates code fixes."""
    
    SYSTEM_PROMPT = """You are an expert software engineer writing code fixes for GitHub issues.

Your task:
1. Analyze the issue and the relevant code files
2. Generate precise code changes to fix the issue
3. Ensure changes are minimal and focused
4. Maintain code style and best practices

CRITICAL RULES:
- Only modify files that directly fix the issue
- Keep changes under 300 lines total
- Preserve existing code style
- Add comments only where necessary
- Ensure backwards compatibility

Output format for EACH file to modify:
FILE: <file_path>
EXPLANATION: <one line explaining the change>
ORIGINAL:
<original code that needs to be changed>
NEW:
<new code to replace it>
---

If no changes needed, output: NO_CHANGES_NEEDED
"""
    
    def __init__(self, api_key: str, git_tool: GitTool, model_name: str = "gemini-1.5-flash"):
        """
        Initialize coder agent.
        
        Args:
            api_key: Gemini, OpenAI, Anthropic, or Groq API key
            git_tool: Git tool instance
            model_name: Model to use
        """
        import os
        
        # 1. Groq Support (Key starts with gsk_)
        if api_key and api_key.startswith("gsk_"):
            from langchain_groq import ChatGroq
            actual_model = "llama-3.3-70b-specdec" if any(x in model_name.lower() for x in ["gemini", "gpt", "claude"]) else model_name
            self.llm = ChatGroq(
                model=actual_model,
                groq_api_key=api_key,
                temperature=0.2,
            )
            
        # 2. Anthropic (Claude) Support (Key starts with sk-ant-)
        elif api_key and api_key.startswith("sk-ant-"):
            from langchain_anthropic import ChatAnthropic
            actual_model = "claude-3-5-sonnet-latest" if any(x in model_name.lower() for x in ["gemini", "gpt", "llama"]) else model_name
            self.llm = ChatAnthropic(
                model=actual_model,
                api_key=api_key,
                temperature=0.2,
            )
            
        # 3. OpenRouter Support (Key starts with sk-or-)
        elif api_key and api_key.startswith("sk-or-"):
            from langchain_openai import ChatOpenAI
            base_url = "https://openrouter.ai/api/v1"
            actual_model = model_name
            if "gemini-2.5-flash" in model_name:
                actual_model = "google/gemini-2.5-flash"
            elif "gemini-1.5-flash" in model_name:
                actual_model = "google/gemini-1.5-flash"
            elif "gemini-2.5-pro" in model_name:
                actual_model = "google/gemini-2.5-pro"
            elif "gemini-1.5-pro" in model_name:
                actual_model = "google/gemini-1.5-pro"
            elif "/" not in model_name:
                actual_model = "google/gemini-2.5-flash"
            
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
                max_tokens=4096,
            )

        # 3.5. OpenAI / Custom Endpoint Support (Key starts with sk-)
        elif api_key and api_key.startswith("sk-"):
            from langchain_openai import ChatOpenAI
            base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or None
            actual_model = "gpt-4o-mini" if any(x in model_name.lower() for x in ["gemini", "llama", "claude"]) else model_name
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
            )
            
        # 4. Standard Gemini Fallback
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )
        
        self.git_tool = git_tool
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", """Repository: {repo_name}
Issue #{issue_number}: {issue_title}

Issue Description:
{issue_body}

Strategy:
{strategy}

Relevant Files:
{files_content}

Generate code changes to fix this issue."""),
        ])
        
        self.chain = self.prompt | self.llm
        
        logger.info(f"Coder agent initialized with model: {model_name}")
    
    def code(self, state: AgentState) -> AgentState:
        """
        Generate code changes.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with code changes
        """
        logger.info("Generating code changes")
        
        if not state.relevant_files:
            logger.error("No relevant files available")
            state.error = "No relevant files from searcher"
            return state
        
        try:
            files_content = self._prepare_files_content(state)
            
            response = self.chain.invoke({
                "repo_name": f"{state.owner}/{state.repo}",
                "issue_number": state.issue_number,
                "issue_title": state.issue.title,
                "issue_body": state.issue.body,
                "strategy": state.strategy,
                "files_content": files_content,
            })
            
            content = response.content
            
            if "NO_CHANGES_NEEDED" in content:
                logger.warning("No changes generated")
                state.error = "Agent determined no changes are needed"
                return state
            
            changes = self._parse_changes(content)
            
            if not changes:
                logger.error("Failed to parse any changes")
                state.error = "Failed to parse code changes from LLM response"
                return state
            
            branch_name = f"ai-fix/issue-{state.issue_number}"
            self.git_tool.create_branch(Path(state.repo_path), branch_name)
            
            for change in changes:
                self.git_tool.write_file(
                    Path(state.repo_path),
                    change.file_path,
                    change.new_content,
                )
            
            state.changes = changes
            state.branch_name = branch_name
            
            logger.info(f"Generated {len(changes)} code changes on branch {branch_name}")
            
            return state
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def _prepare_files_content(self, state: AgentState) -> str:
        """Prepare file contents for LLM prompt."""
        content_parts = []
        
        for result in state.relevant_files[:5]:
            file_path = result.file_path
            full_content = self.git_tool.get_file_content(
                Path(state.repo_path),
                file_path,
            )
            
            if full_content:
                content_parts.append(f"File: {file_path}\n```\n{full_content}\n```\n")
        
        return "\n".join(content_parts)
    
    def _parse_changes(self, content: str) -> list[CodeChange]:
        """Parse code changes from LLM response."""
        changes = []
        sections = content.split("---")
        
        for section in sections:
            if not section.strip():
                continue
            
            try:
                file_path = self._extract_field(section, "FILE:")
                explanation = self._extract_field(section, "EXPLANATION:")
                original = self._extract_code_block(section, "ORIGINAL:")
                new = self._extract_code_block(section, "NEW:")
                
                if file_path and new:
                    changes.append(CodeChange(
                        file_path=file_path,
                        original_content=original,
                        new_content=new,
                        explanation=explanation or "Code fix",
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to parse change section: {e}")
                continue
        
        return changes
    
    def _extract_field(self, content: str, marker: str) -> str:
        """Extract single-line field from content."""
        for line in content.split("\n"):
            if marker in line:
                return line.replace(marker, "").strip()
        return ""
    
    def _extract_code_block(self, content: str, marker: str) -> str:
        """Extract code block from content."""
        lines = content.split("\n")
        result = []
        capturing = False
        
        for line in lines:
            if marker in line:
                capturing = True
                continue
            elif capturing:
                if line.strip() in ["FILE:", "EXPLANATION:", "ORIGINAL:", "NEW:", "---"]:
                    break
                result.append(line)
        
        code = "\n".join(result).strip()
        
        if code.startswith("```"):
            code = "\n".join(code.split("\n")[1:])
        if code.endswith("```"):
            code = "\n".join(code.split("\n")[:-1])
        
        return code.strip()
