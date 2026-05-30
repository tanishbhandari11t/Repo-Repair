"""Tests for data models."""

import pytest

from models import Issue, SearchResult, CodeChange, TestResult, WorkflowResult


def test_issue_creation():
    """Test Issue model creation."""
    issue = Issue(
        number=123,
        title="Test Issue",
        body="Test body",
        state="open",
        labels=["bug"],
        author="testuser",
        url="https://github.com/test/repo/issues/123",
    )
    
    assert issue.number == 123
    assert issue.title == "Test Issue"
    assert "bug" in issue.labels


def test_search_result_creation():
    """Test SearchResult model creation."""
    result = SearchResult(
        file_path="src/main.py",
        content="def main():\n    pass",
        relevance_score=0.95,
    )
    
    assert result.file_path == "src/main.py"
    assert result.relevance_score == 0.95


def test_code_change_creation():
    """Test CodeChange model creation."""
    change = CodeChange(
        file_path="src/main.py",
        original_content="old code",
        new_content="new code",
        explanation="Fixed bug",
    )
    
    assert change.file_path == "src/main.py"
    assert change.explanation == "Fixed bug"


def test_test_result_creation():
    """Test TestResult model creation."""
    result = TestResult(
        success=True,
        output="All tests passed",
        exit_code=0,
        duration=5.2,
    )
    
    assert result.success is True
    assert result.duration == 5.2


def test_workflow_result_creation():
    """Test WorkflowResult model creation."""
    result = WorkflowResult(
        success=True,
        branch_name="ai-fix/issue-123",
        files_changed=["src/main.py"],
        pr_url="https://github.com/test/repo/pull/1",
    )
    
    assert result.success is True
    assert len(result.files_changed) == 1
    assert result.pr_url is not None


def test_workflow_result_with_error():
    """Test WorkflowResult with error."""
    result = WorkflowResult(
        success=False,
        error="Something went wrong",
    )
    
    assert result.success is False
    assert result.error == "Something went wrong"
    assert result.files_changed == []
