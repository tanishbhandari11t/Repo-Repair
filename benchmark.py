import os
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List

from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from agents.orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Benchmark")


@dataclass
class BenchmarkIssue:
    owner: str
    repo: str
    issue_number: int


def run_benchmark(issues_file: str):
    """Run SWE-Bench style benchmark."""
    logger.info(f"Loading issues from {issues_file}")
    
    with open(issues_file, 'r') as f:
        data = json.load(f)
        
    issues = [
        BenchmarkIssue(
            owner=item['owner'],
            repo=item['repo'],
            issue_number=item['issue_number']
        )
        for item in data
    ]
    
    settings = get_settings()
    github_tool = GitHubTool(settings.github_token)
    git_tool = GitTool(settings.workspace_dir)
    
    orchestrator = Orchestrator(
        github_tool=github_tool,
        git_tool=git_tool,
        settings=settings
    )
    
    total = len(issues)
    resolved = 0
    start_time = time.time()
    
    logger.info(f"Starting benchmark for {total} issues...")
    
    results = []
    
    for i, issue_data in enumerate(issues, 1):
        logger.info(f"[{i}/{total}] Evaluating {issue_data.owner}/{issue_data.repo}#{issue_data.issue_number}")
        
        try:
            # Fetch issue details
            issue = github_tool.get_issue(
                issue_data.owner, 
                issue_data.repo, 
                issue_data.issue_number
            )
            
            # Clone repo
            repo_path = git_tool.clone_repository(
                issue_data.owner, 
                issue_data.repo, 
                settings.github_token
            )
            
            # Run engine
            result = orchestrator.run(
                owner=issue_data.owner,
                repo=issue_data.repo,
                issue_number=issue_data.issue_number,
                issue=issue,
                repo_path=repo_path,
                skip_tests=False,
                dry_run=True,  # Don't create real PRs!
            )
            
            if result.success:
                logger.info(f"✅ Resolved {issue_data.owner}/{issue_data.repo}#{issue_data.issue_number}")
                resolved += 1
            else:
                logger.error(f"❌ Failed {issue_data.owner}/{issue_data.repo}#{issue_data.issue_number}: {result.error}")
            
            results.append({
                "owner": issue_data.owner,
                "repo": issue_data.repo,
                "issue": issue_data.issue_number,
                "success": result.success,
                "error": result.error,
                "files_changed": result.files_changed
            })
            
        except Exception as e:
            logger.exception(f"Crash evaluating {issue_data.owner}/{issue_data.repo}#{issue_data.issue_number}: {e}")
            results.append({
                "owner": issue_data.owner,
                "repo": issue_data.repo,
                "issue": issue_data.issue_number,
                "success": False,
                "error": f"Crash: {str(e)}"
            })
            
    end_time = time.time()
    duration = end_time - start_time
    
    success_rate = (resolved / total) * 100 if total > 0 else 0
    
    print("\n" + "="*50)
    print("📊 BENCHMARK RESULTS")
    print("="*50)
    print(f"Total Issues : {total}")
    print(f"Resolved     : {resolved}")
    print(f"Success Rate : {success_rate:.1f}%")
    print(f"Duration     : {duration/60:.1f} minutes")
    print("="*50)
    
    with open('benchmark_results.json', 'w') as f:
        json.dump({
            "metrics": {
                "total": total,
                "resolved": resolved,
                "success_rate": success_rate,
                "duration_seconds": duration
            },
            "results": results
        }, f, indent=2)
    
    print("Results saved to benchmark_results.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python benchmark.py <issues.json>")
        sys.exit(1)
        
    run_benchmark(sys.argv[1])
