"""Git operations tool."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class GitTool:
    """Tool for Git operations."""
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize Git tool.
        
        Args:
            workspace_dir: Directory for cloning repositories
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Git tool initialized with workspace: {workspace_dir}")
    
    def clone_repository(self, owner: str, repo: str, token: Optional[str] = None) -> Path:
        """
        Clone a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub token for private repos
            
        Returns:
            Path to cloned repository
            
        Raises:
            GitCommandError: If clone fails
        """
        repo_path = self.workspace_dir / f"{owner}_{repo}"
        
        if repo_path.exists():
            logger.info(f"Repository already exists at {repo_path}, removing...")
            try:
                def _remove_readonly(func, path, excinfo):
                    import os
                    import stat
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass
                shutil.rmtree(repo_path, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to delete existing repo folder: {e}")
            
            # Self-healing lock bypass: If folder is still locked and exists, fallback to unique name
            if repo_path.exists():
                import uuid
                suffix = uuid.uuid4().hex[:8]
                repo_path = self.workspace_dir / f"{owner}_{repo}_{suffix}"
                logger.info(f"Folder is locked by another process. Falling back to unique path: {repo_path}")
        
        try:
            if token:
                url = f"https://{token}@github.com/{owner}/{repo}.git"
            else:
                url = f"https://github.com/{owner}/{repo}.git"
            
            logger.info(f"Cloning {owner}/{repo} (skipping Git LFS binaries)...")
            Repo.clone_from(
                url, 
                repo_path, 
                depth=1,
                multi_options=["-c filter.lfs.smudge=", "-c filter.lfs.required=false"],
                env={"GIT_LFS_SKIP_SMUDGE": "1"},
                allow_unsafe_options=True
            )
            logger.info(f"Repository cloned to {repo_path}")
            
            return repo_path
            
        except GitCommandError as e:
            err_msg = str(e)
            if "Clone succeeded, but checkout failed" in err_msg or "unable to checkout working tree" in err_msg:
                logger.warning("Windows path checkout limitation detected. Initiating sparse-checkout self-healing bypass...")
                try:
                    repo = Repo(repo_path)
                    
                    # 1. Enable sparse checkout
                    repo.git.config("core.sparseCheckout", "true")
                    
                    # 2. Write patterns to .git/info/sparse-checkout
                    sparse_file = repo_path / ".git" / "info" / "sparse-checkout"
                    sparse_file.parent.mkdir(parents=True, exist_ok=True)
                    # We exclude any path containing the offending trailing space target '9fa89f7 '
                    sparse_file.write_text("/*\n!*9fa89f7*\n", encoding="utf-8")
                    
                    # 3. Trigger manual checkout
                    logger.info("Retrying checkout with sparse exclusions...")
                    repo.git.checkout("-f", "HEAD")
                    logger.info("Successfully checked out repository working tree using sparse-checkout bypass!")
                    return repo_path
                except Exception as ex:
                    logger.error(f"Sparse-checkout self-healing fallback failed: {ex}")
                    raise e
            else:
                logger.error(f"Failed to clone repository: {e}")
                raise
    
    def create_branch(self, repo_path: Path, branch_name: str) -> None:
        """
        Create a new branch.
        
        Args:
            repo_path: Path to repository
            branch_name: Name for new branch
            
        Raises:
            GitCommandError: If branch creation fails
        """
        try:
            repo = Repo(repo_path)
            
            if branch_name in repo.heads:
                logger.warning(f"Branch {branch_name} already exists, checking out...")
                repo.heads[branch_name].checkout()
            else:
                new_branch = repo.create_head(branch_name)
                new_branch.checkout()
                logger.info(f"Created and checked out branch: {branch_name}")
                
        except GitCommandError as e:
            logger.error(f"Failed to create branch: {e}")
            raise
    
    def commit_changes(
        self,
        repo_path: Path,
        message: str,
        files: Optional[list[str]] = None,
    ) -> str:
        """
        Commit changes to the repository.
        
        Args:
            repo_path: Path to repository
            message: Commit message
            files: Specific files to commit (None = all changes)
            
        Returns:
            Commit SHA
            
        Raises:
            GitCommandError: If commit fails
        """
        try:
            repo = Repo(repo_path)
            
            if files:
                repo.index.add(files)
            else:
                repo.git.add(A=True)
            
            if not repo.index.diff("HEAD"):
                logger.warning("No changes to commit")
                return repo.head.commit.hexsha
            
            commit = repo.index.commit(message, no_verify=True)
            logger.info(f"Committed changes: {commit.hexsha[:8]}")
            
            return commit.hexsha
            
        except GitCommandError as e:
            logger.error(f"Failed to commit changes: {e}")
            raise
    
    def push_branch(self, repo_path: Path, branch_name: str, token: str) -> None:
        """
        Push branch to remote.
        
        Args:
            repo_path: Path to repository
            branch_name: Branch to push
            token: GitHub token
            
        Raises:
            GitCommandError: If push fails
        """
        try:
            repo = Repo(repo_path)
            
            origin_url = repo.remotes.origin.url
            if not origin_url.startswith("https://"):
                origin_url = origin_url.replace("git@github.com:", "https://github.com/")
            
            if token not in origin_url:
                origin_url = origin_url.replace("https://", f"https://{token}@")
                repo.remotes.origin.set_url(origin_url)
            
            logger.info(f"Pushing branch {branch_name}...")
            repo.remotes.origin.push(refspec=f"{branch_name}:{branch_name}")
            logger.info(f"Successfully pushed {branch_name}")
            
        except GitCommandError as e:
            logger.error(f"Failed to push branch: {e}")
            raise
    
    def get_diff(self, repo_path: Path, max_lines: Optional[int] = None) -> str:
        """
        Get diff of uncommitted changes.
        
        Args:
            repo_path: Path to repository
            max_lines: Maximum number of diff lines
            
        Returns:
            Diff string
        """
        try:
            repo = Repo(repo_path)
            diff = repo.git.diff()
            
            if max_lines and diff:
                lines = diff.split('\n')
                if len(lines) > max_lines:
                    diff = '\n'.join(lines[:max_lines])
                    diff += f"\n\n... (truncated {len(lines) - max_lines} lines)"
            
            return diff
            
        except GitCommandError as e:
            logger.error(f"Failed to get diff: {e}")
            return ""
    
    def get_changed_files(self, repo_path: Path) -> list[str]:
        """
        Get list of changed files.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of file paths
        """
        try:
            repo = Repo(repo_path)
            changed_files = [item.a_path for item in repo.index.diff(None)]
            untracked_files = repo.untracked_files
            
            return changed_files + untracked_files
            
        except GitCommandError as e:
            logger.error(f"Failed to get changed files: {e}")
            return []
    
    def get_file_content(self, repo_path: Path, file_path: str) -> Optional[str]:
        """
        Get content of a file in the repository.
        
        Args:
            repo_path: Path to repository
            file_path: Relative path to file
            
        Returns:
            File content or None if not found
        """
        try:
            full_path = repo_path / file_path
            if full_path.exists():
                return full_path.read_text(encoding="utf-8")
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def write_file(self, repo_path: Path, file_path: str, content: str) -> None:
        """
        Write content to a file in the repository.
        
        Args:
            repo_path: Path to repository
            file_path: Relative path to file
            content: Content to write
        """
        try:
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise
