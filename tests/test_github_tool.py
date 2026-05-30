"""Tests for GitHub tool."""

import pytest
from unittest.mock import Mock, patch

from tools.github_tool import GitHubTool
from models import Issue


@pytest.fixture
def mock_github():
    """Mock GitHub instance."""
    with patch("tools.github_tool.Github") as mock:
        yield mock


def test_github_tool_initialization(mock_github):
    """Test GitHub tool initialization."""
    tool = GitHubTool("fake_token")
    assert tool is not None
    mock_github.assert_called_once_with("fake_token")


def test_get_issue(mock_github):
    """Test fetching a GitHub issue."""
    mock_repo = Mock()
    mock_issue = Mock()
    mock_issue.number = 123
    mock_issue.title = "Test Issue"
    mock_issue.body = "Test body"
    mock_issue.state = "open"
    mock_issue.labels = []
    mock_issue.user.login = "testuser"
    mock_issue.html_url = "https://github.com/test/repo/issues/123"
    
    mock_repo.get_issue.return_value = mock_issue
    mock_github.return_value.get_repo.return_value = mock_repo
    
    tool = GitHubTool("fake_token")
    issue = tool.get_issue("test", "repo", 123)
    
    assert isinstance(issue, Issue)
    assert issue.number == 123
    assert issue.title == "Test Issue"
    assert issue.author == "testuser"


def test_get_repo_info(mock_github):
    """Test getting repository information."""
    mock_repo = Mock()
    mock_repo.name = "test-repo"
    mock_repo.full_name = "test/test-repo"
    mock_repo.description = "Test description"
    mock_repo.language = "Python"
    mock_repo.default_branch = "main"
    mock_repo.get_contents.return_value = []
    
    mock_github.return_value.get_repo.return_value = mock_repo
    
    tool = GitHubTool("fake_token")
    info = tool.get_repo_info("test", "test-repo")
    
    assert info["name"] == "test-repo"
    assert info["language"] == "Python"
    assert info["default_branch"] == "main"
