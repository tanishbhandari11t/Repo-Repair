"""GitHub API operations tool."""

import logging
from typing import Optional

from github import Github, GithubException
from github.Issue import Issue as GHIssue
from github.PullRequest import PullRequest

from models import Issue

logger = logging.getLogger(__name__)


class GitHubTool:
    """Tool for interacting with GitHub API."""
    
    def __init__(self, token: str):
        """
        Initialize GitHub tool.
        
        Args:
            token: GitHub personal access token
        """
        self.github = Github(token)
        self.token = token
        logger.info("GitHub tool initialized")
    
    def get_issue(self, owner: str, repo: str, issue_number: int) -> Issue:
        """
        Fetch a GitHub issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Issue object
            
        Raises:
            GithubException: If issue cannot be fetched
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            gh_issue = repository.get_issue(issue_number)
            
            issue = Issue(
                number=gh_issue.number,
                title=gh_issue.title,
                body=gh_issue.body or "",
                state=gh_issue.state,
                labels=[label.name for label in gh_issue.labels],
                author=gh_issue.user.login,
                url=gh_issue.html_url,
                raw=gh_issue,
            )
            
            logger.info(f"Fetched issue #{issue_number}: {issue.title}")
            return issue
            
        except GithubException as e:
            logger.error(f"Failed to fetch issue: {e}")
            raise
    
    def create_branch(self, owner: str, repo: str, branch_name: str, base_branch: str = "main") -> None:
        """
        Create a new branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch_name: Name for new branch
            base_branch: Base branch to branch from
            
        Raises:
            GithubException: If branch cannot be created
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            try:
                base_ref = repository.get_git_ref(f"heads/{base_branch}")
            except GithubException:
                base_branch = "master"
                base_ref = repository.get_git_ref(f"heads/{base_branch}")
            
            base_sha = base_ref.object.sha
            repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)
            
            logger.info(f"Created branch: {branch_name} from {base_branch}")
            
        except GithubException as e:
            if e.status == 422:
                logger.warning(f"Branch {branch_name} already exists")
            else:
                logger.error(f"Failed to create branch: {e}")
                raise
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = True,
    ) -> str:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            draft: Create as draft PR
            
        Returns:
            PR URL
            
        Raises:
            GithubException: If PR cannot be created
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            try:
                repository.get_git_ref(f"heads/{base_branch}")
            except GithubException:
                base_branch = "master"
            
            pr = repository.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft,
            )
            
            logger.info(f"Created {'draft ' if draft else ''}PR: {pr.html_url}")
            return pr.html_url
            
        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            raise
    
    def add_pr_comment(self, owner: str, repo: str, pr_number: int, comment: str) -> None:
        """
        Add a comment to a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            comment: Comment text
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            pr.create_issue_comment(comment)
            
            logger.info(f"Added comment to PR #{pr_number}")
            
        except GithubException as e:
            logger.error(f"Failed to add comment: {e}")
            raise
    
    def get_repo_info(self, owner: str, repo: str) -> dict:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repo info
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            return {
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "language": repository.language,
                "default_branch": repository.default_branch,
                "has_tests": self._has_tests(repository),
            }
            
        except GithubException as e:
            logger.error(f"Failed to get repo info: {e}")
            raise
    
    def _has_tests(self, repository) -> bool:
        """Check if repository has tests."""
        try:
            contents = repository.get_contents("")
            test_indicators = ["tests", "test", "spec", "__tests__"]
            
            for content in contents:
                if any(indicator in content.name.lower() for indicator in test_indicators):
                    return True
            
            return False
        except:
            return False
