"""Tests for CLI functionality."""

import pytest
from typer import BadParameter

from cli.main import validate_github_url


def test_validate_github_url_valid():
    """Test valid GitHub URL validation."""
    url = "https://github.com/owner/repo/issues/123"
    owner, repo, issue_num = validate_github_url(url)
    
    assert owner == "owner"
    assert repo == "repo"
    assert issue_num == 123


def test_validate_github_url_invalid():
    """Test invalid GitHub URL validation."""
    invalid_urls = [
        "https://github.com/owner/repo",
        "https://gitlab.com/owner/repo/issues/123",
        "not a url",
        "https://github.com/owner/repo/pull/123",
    ]
    
    for url in invalid_urls:
        with pytest.raises(BadParameter):
            validate_github_url(url)


def test_validate_github_url_with_different_numbers():
    """Test URL validation with different issue numbers."""
    url = "https://github.com/test/project/issues/9999"
    owner, repo, issue_num = validate_github_url(url)
    
    assert owner == "test"
    assert repo == "project"
    assert issue_num == 9999
