"""Main CLI entry point for RepoRepair."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import get_settings

app = typer.Typer(
    name="reporepair",
    help="AI GitHub Issue → Pull Request Agent",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich formatting."""
    settings = get_settings()
    log_level = logging.DEBUG if verbose else getattr(logging, settings.log_level.upper())
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, console=console),
            logging.FileHandler(settings.log_file),
        ],
    )


def validate_github_url(url: str) -> tuple[str, str, int]:
    """
    Validate and parse GitHub issue URL.
    
    Args:
        url: GitHub issue URL
        
    Returns:
        Tuple of (owner, repo, issue_number)
        
    Raises:
        typer.BadParameter: If URL is invalid
    """
    import re
    
    pattern = r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)"
    match = re.match(pattern, url)
    
    if not match:
        raise typer.BadParameter(
            "Invalid GitHub issue URL. Expected format: "
            "https://github.com/owner/repo/issues/123"
        )
    
    owner, repo, issue_num = match.groups()
    return owner, repo, int(issue_num)


@app.command()
def fix(
    issue_url: str = typer.Argument(
        ...,
        help="GitHub issue URL (e.g., https://github.com/owner/repo/issues/123)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Analyze and generate fix without creating PR",
    ),
    skip_tests: bool = typer.Option(
        False,
        "--skip-tests",
        help="Skip running tests (not recommended)",
    ),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        help="Custom workspace directory",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Convert a GitHub issue into a tested draft Pull Request.
    
    This command will:
    1. Fetch and analyze the GitHub issue
    2. Clone the repository
    3. Search for relevant code files
    4. Generate a code fix
    5. Run tests in Docker
    6. Create a draft Pull Request
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    console.print(
        Panel.fit(
            "[bold blue]RepoRepair[/bold blue] 🔧\n"
            "AI GitHub Issue → Pull Request Agent",
            border_style="blue",
        )
    )
    
    try:
        owner, repo, issue_number = validate_github_url(issue_url)
        logger.info(f"Processing issue #{issue_number} from {owner}/{repo}")
        
        console.print(f"\n[bold]Repository:[/bold] {owner}/{repo}")
        console.print(f"[bold]Issue:[/bold] #{issue_number}")
        console.print(f"[bold]Dry Run:[/bold] {'Yes' if dry_run else 'No'}\n")
        
        if dry_run:
            console.print("[yellow]⚠ Dry run mode - no PR will be created[/yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Initializing...", total=None)
            
            # Import here to avoid slow startup
            from tools.github_tool import GitHubTool
            from tools.git_tool import GitTool
            from agents.orchestrator import Orchestrator
            
            settings = get_settings()
            workspace_path = workspace or settings.workspace_dir
            
            # Initialize tools
            progress.update(task, description="Connecting to GitHub...")
            github_tool = GitHubTool(settings.github_token)
            git_tool = GitTool(workspace_path)
            
            # Fetch issue
            progress.update(task, description=f"Fetching issue #{issue_number}...")
            issue = github_tool.get_issue(owner, repo, issue_number)
            
            console.print(f"\n[bold green]✓[/bold green] Issue fetched: {issue.title}")
            console.print(f"[dim]{issue.body[:200]}...[/dim]\n")
            
            # Clone repository
            progress.update(task, description="Cloning repository...")
            repo_path = git_tool.clone_repository(owner, repo)
            console.print(f"[bold green]✓[/bold green] Repository cloned to {repo_path}\n")
            
            # Run orchestrator
            progress.update(task, description="Starting AI agent workflow...")
            orchestrator = Orchestrator(
                github_tool=github_tool,
                git_tool=git_tool,
                settings=settings,
            )
            
            result = orchestrator.run(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                issue=issue,
                repo_path=repo_path,
                skip_tests=skip_tests,
                dry_run=dry_run,
            )
            
            if result.success:
                console.print("\n[bold green]✓ Success![/bold green]\n")
                
                if not dry_run and result.pr_url:
                    console.print(f"[bold]Draft PR created:[/bold] {result.pr_url}")
                    console.print("\n[yellow]⚠ Please review the PR before merging[/yellow]")
                else:
                    console.print("[bold]Changes ready:[/bold]")
                    console.print(f"  Branch: {result.branch_name}")
                    console.print(f"  Files changed: {len(result.files_changed)}")
                    
                    if dry_run:
                        console.print("\n[dim]Run without --dry-run to create PR[/dim]")
            else:
                console.print(f"\n[bold red]✗ Failed:[/bold red] {result.error}")
                raise typer.Exit(code=1)
                
    except (typer.Exit, typer.Abort):
        raise
    except typer.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show RepoRepair version."""
    from __init__ import __version__
    console.print(f"RepoRepair v{__version__}")


@app.command()
def config() -> None:
    """Show current configuration."""
    try:
        settings = get_settings()
        
        console.print("\n[bold]RepoRepair Configuration[/bold]\n")
        console.print(f"[bold]Workspace:[/bold] {settings.workspace_dir}")
        console.print(f"[bold]Log Level:[/bold] {settings.log_level}")
        console.print(f"[bold]Max Diff Lines:[/bold] {settings.max_diff_lines}")
        console.print(f"[bold]Planning Model:[/bold] {settings.gemini_planning_model}")
        console.print(f"[bold]Coding Model:[/bold] {settings.gemini_coding_model}")
        console.print(f"\n[bold]GitHub Token:[/bold] {'[green]Set[/green]' if settings.github_token else '[red]Missing[/red]'}")
        console.print(f"[bold]Gemini API Key:[/bold] {'[green]Set[/green]' if settings.gemini_api_key else '[red]Missing[/red]'}")
        
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {e}")
        console.print("\n[yellow]Make sure .env file exists with required keys[/yellow]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
