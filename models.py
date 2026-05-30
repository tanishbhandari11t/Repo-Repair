"""Shared data models for RepoRepair."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Issue:
    """Represents a GitHub issue."""
    
    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    author: str
    url: str
    raw: Any = None


@dataclass
class SearchResult:
    """Code search result."""
    
    file_path: str
    content: str
    relevance_score: float
    line_numbers: Optional[tuple[int, int]] = None


@dataclass
class CodeChange:
    """Represents a code change."""
    
    file_path: str
    original_content: str
    new_content: str
    explanation: str


@dataclass
class TestResult:
    """Test execution result."""
    
    success: bool
    output: str
    exit_code: int
    duration: float


@dataclass
class WorkflowResult:
    """Final result of the workflow."""
    
    success: bool
    branch_name: Optional[str] = None
    files_changed: list[str] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
    reasoning: dict = None
    
    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []
        if self.reasoning is None:
            self.reasoning = {}


@dataclass
class AgentState:
    """State passed between agents in the workflow."""
    
    owner: str
    repo: str
    issue_number: int
    issue: Issue
    repo_path: str
    
    # Planner outputs
    strategy: Optional[str] = None
    search_queries: Optional[list[str]] = None
    
    # Searcher outputs
    relevant_files: Optional[list[SearchResult]] = None
    
    # Coder outputs
    changes: Optional[list[CodeChange]] = None
    branch_name: Optional[str] = None
    
    # Validator outputs
    test_result: Optional[TestResult] = None
    validation_passed: bool = False
    
    # Final result
    pr_url: Optional[str] = None
    error: Optional[str] = None
    
    # Reasoning logs for UI
    reasoning: dict = None
    
    # Retry tracking
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = {}
