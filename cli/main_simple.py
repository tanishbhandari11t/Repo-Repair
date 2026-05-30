"""Simplified CLI for RepoRepair - works without ChromaDB."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool

app = typer.Typer(
    name="reporepair",
    help="AI GitHub Issue to Pull Request Agent (Simplified)",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    settings = get_settings()
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(settings.log_file)],
    )


@app.command()
def fix(
    issue_url: str = typer.Argument(..., help="GitHub issue URL"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Analyze without creating PR"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """
    Analyze a GitHub issue and generate a fix strategy.
    
    Note: This simplified version shows what RepoRepair would do.
    Full AI-powered fixes require additional packages (ChromaDB, sentence-transformers).
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    console.print(Panel.fit(
        "[bold blue]RepoRepair[/bold blue] - Simplified Mode\n"
        "Analyzing GitHub Issue",
        border_style="blue",
    ))
    
    try:
        # Validate URL
        import re
        pattern = r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)"
        match = re.match(pattern, issue_url)
        
        if not match:
            console.print("[bold red]Error:[/bold red] Invalid GitHub issue URL")
            console.print("Expected: https://github.com/owner/repo/issues/123")
            raise typer.Exit(code=1)
        
        owner, repo, issue_number = match.groups()
        issue_number = int(issue_number)
        
        console.print(f"\n[bold]Repository:[/bold] {owner}/{repo}")
        console.print(f"[bold]Issue:[/bold] #{issue_number}")
        console.print(f"[bold]Mode:[/bold] {'Dry Run' if dry_run else 'Full Run'}\n")
        
        # Initialize tools
        settings = get_settings()
        console.print("[yellow]>[/yellow] Connecting to GitHub...")
        github_tool = GitHubTool(settings.github_token)
        
        # Fetch issue
        console.print("[yellow]>[/yellow] Fetching issue details...")
        issue = github_tool.get_issue(owner, repo, issue_number)
        
        console.print(f"\n[bold green]OK[/bold green] Issue fetched: {issue.title}")
        console.print(f"[dim]Author: {issue.author}[/dim]")
        console.print(f"[dim]State: {issue.state}[/dim]")
        console.print(f"[dim]Labels: {', '.join(issue.labels) if issue.labels else 'None'}[/dim]\n")
        
        console.print("[bold]Issue Description:[/bold]")
        console.print(Panel(issue.body[:500] + ("..." if len(issue.body) > 500 else ""), 
                          border_style="dim"))
        
        # Clone repository
        console.print("\n[yellow]>[/yellow] Cloning repository...")
        git_tool = GitTool(settings.workspace_dir)
        repo_path = git_tool.clone_repository(owner, repo, settings.github_token)
        
        console.print(f"[bold green]OK[/bold green] Repository cloned to {repo_path}\n")
        
        # Show what full version would do
        console.print("[bold cyan]=== What Full RepoRepair Would Do ===[/bold cyan]\n")
        console.print("[bold]1. AI Analysis (Planner Agent)[/bold]")
        console.print("   - Analyze issue with Gemini AI")
        console.print("   - Identify bug type and root cause")
        console.print("   - Create fix strategy")
        console.print("   - Generate search queries\n")
        
        console.print("[bold]2. Code Search (Searcher Agent)[/bold]")
        console.print("   - Index repository with ChromaDB")
        console.print("   - Semantic search for relevant files")
        console.print("   - Keyword search with grep")
        console.print("   - Rank and filter results\n")
        
        console.print("[bold]3. Code Generation (Coder Agent)[/bold]")
        console.print("   - Load relevant files")
        console.print("   - Generate code fix with Gemini")
        console.print("   - Create new branch")
        console.print("   - Apply changes\n")
        
        console.print("[bold]4. Validation (Validator Agent)[/bold]")
        console.print("   - Run tests in Docker")
        console.print("   - Validate changes")
        console.print("   - Retry if needed (max 3 attempts)\n")
        
        console.print("[bold]5. Pull Request Creation[/bold]")
        console.print("   - Commit changes")
        console.print("   - Push to GitHub")
        console.print("   - Create draft PR with detailed description\n")
        
        # Show installation instructions
        console.print("[bold yellow]! To Enable Full Features:[/bold yellow]")
        console.print("\nInstall required packages:")
        console.print("[cyan]pip install chromadb sentence-transformers[/cyan]")
        console.print("\nNote: Requires Visual Studio C++ Build Tools on Windows")
        console.print("Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/\n")
        
        # Summary
        console.print("[bold green]OK Analysis Complete![/bold green]\n")
        console.print(f"[bold]Next Steps:[/bold]")
        console.print(f"1. Review the issue: {issue.url}")
        console.print(f"2. Install full dependencies (see above)")
        console.print(f"3. Run: [cyan]reporepair fix {issue_url}[/cyan]")
        console.print(f"4. Review the generated draft PR")
        console.print(f"5. Merge when satisfied!\n")
        
    except (typer.Exit, typer.Abort):
        raise
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"\n[bold red]ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)


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
        
        console.print("\n[bold yellow]Mode:[/bold yellow] Simplified (missing optional dependencies)")
        console.print("[dim]Install chromadb + sentence-transformers for full features[/dim]\n")
        
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
