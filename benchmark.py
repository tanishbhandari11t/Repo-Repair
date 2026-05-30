"""SWE-bench Evaluation Runner for RepoRepair."""

import json
import logging
import argparse
import time
from pathlib import Path

from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from agents.orchestrator import Orchestrator
from models import Issue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_path: str):
    """Load SWE-bench dataset (JSON format)."""
    with open(dataset_path, 'r') as f:
        return json.load(f)

def run_evaluation(dataset_path: str, limit: int = 10, dry_run: bool = True):
    """Run agent against SWE-bench dataset."""
    logger.info(f"Starting SWE-bench evaluation on {dataset_path} (Limit: {limit})")
    
    settings = get_settings()
    if not settings.github_token:
        logger.error("GITHUB_TOKEN not found in environment.")
        return
        
    github_tool = GitHubTool(settings.github_token)
    git_tool = GitTool(settings.workspace_dir)
    orchestrator = Orchestrator(github_tool, git_tool, settings)
    
    dataset = load_dataset(dataset_path)
    
    results = {
        "total": min(len(dataset), limit),
        "resolved": 0,
        "failed": 0,
        "success_rate": 0.0,
        "details": []
    }
    
    count = 0
    for item in dataset:
        if count >= limit:
            break
            
        instance_id = item.get("instance_id", f"task_{count}")
        repo = item.get("repo", "unknown/repo")
        problem_statement = item.get("problem_statement", "")
        
        logger.info(f"\n[{count+1}/{results['total']}] Evaluating instance: {instance_id}")
        
        # Mocking an Issue object since SWE-bench doesn't use live GitHub issues
        issue = Issue(
            number=9999,
            title=f"SWE-bench: {instance_id}",
            body=problem_statement,
            state="open",
            labels=[],
            author="swe-bench",
            url=f"https://github.com/{repo}/issues/9999"
        )
        
        owner, repo_name = repo.split("/") if "/" in repo else ("unknown", repo)
        
        try:
            # Note: For real SWE-bench, we'd need to checkout the base_commit. 
            # This requires adding base_commit checkout to git_tool, but we simulate for the portfolio MVP.
            repo_path = git_tool.clone_repository(owner, repo_name, settings.github_token)
            
            result = orchestrator.run(
                owner=owner,
                repo=repo_name,
                issue_number=issue.number,
                issue=issue,
                repo_path=repo_path,
                skip_tests=False,
                dry_run=dry_run
            )
            
            if result.success and result.validation_passed:
                results["resolved"] += 1
                status = "RESOLVED"
            else:
                results["failed"] += 1
                status = "FAILED"
                
            results["details"].append({
                "instance_id": instance_id,
                "status": status,
                "error": result.error
            })
            
        except Exception as e:
            logger.error(f"Evaluation crashed on {instance_id}: {e}")
            results["failed"] += 1
            results["details"].append({
                "instance_id": instance_id,
                "status": "CRASHED",
                "error": str(e)
            })
            
        count += 1
        
    results["success_rate"] = (results["resolved"] / results["total"]) * 100
    
    logger.info("\n=== EVALUATION RESULTS ===")
    logger.info(f"Total Evaluated: {results['total']}")
    logger.info(f"Resolved: {results['resolved']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Success Rate: {results['success_rate']:.1f}%")
    
    with open("swe_bench_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    logger.info("Detailed results saved to swe_bench_results.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RepoRepair against SWE-bench dataset")
    parser.add_argument("--dataset", type=str, required=True, help="Path to SWE-bench json dataset")
    parser.add_argument("--limit", type=int, default=10, help="Max instances to evaluate")
    parser.add_argument("--live", action="store_true", help="Actually create PRs (turns off dry_run)")
    args = parser.parse_args()
    
    run_evaluation(args.dataset, args.limit, dry_run=not args.live)
