"""Web interface for RepoRepair - FastAPI application."""

import os
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from agents.orchestrator import Orchestrator

app = FastAPI(title="RepoRepair API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Store job status in memory (use Redis in production)
jobs: Dict[str, Dict[str, Any]] = {}


class FixRequest(BaseModel):
    issue_url: str
    skip_tests: bool = False
    dry_run: bool = False
    github_token: Optional[str] = None


def validate_issue_url(url: str) -> tuple[bool, Optional[str], Optional[str], Optional[int]]:
    """Validate and parse GitHub issue URL."""
    import re
    pattern = r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)"
    match = re.match(pattern, url)
    
    if not match:
        return False, None, None, None
    
    owner, repo, issue_num = match.groups()
    return True, owner, repo, int(issue_num)


def run_reporepair_task(job_id: str, issue_url: str, skip_tests: bool, dry_run: bool, github_token: Optional[str] = None):
    """Run RepoRepair in background thread."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 'Initializing...'
        
        settings = get_settings()
        
        valid, owner, repo, issue_number = validate_issue_url(issue_url)
        if not valid:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = 'Invalid GitHub issue URL'
            return
        
        jobs[job_id]['progress'] = f'Fetching issue #{issue_number}...'
        
        active_token = github_token or settings.github_token
        github_tool = GitHubTool(active_token)
        git_tool = GitTool(settings.workspace_dir)
        
        issue = github_tool.get_issue(owner, repo, issue_number)
        jobs[job_id]['issue_title'] = issue.title
        jobs[job_id]['progress'] = f'Cloning repository {owner}/{repo}...'
        
        repo_path = git_tool.clone_repository(owner, repo, active_token)
        jobs[job_id]['progress'] = 'Running AI analysis...'
        
        orchestrator = Orchestrator(
            github_tool=github_tool,
            git_tool=git_tool,
            settings=settings,
        )
        
        def _progress_callback(node_name: str, state: Any):
            jobs[job_id]['reasoning'] = getattr(state, 'reasoning', {})
            jobs[job_id]['progress'] = f"Agent Phase: {node_name.upper()}..."

        result = orchestrator.run(
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            issue=issue,
            repo_path=repo_path,
            skip_tests=skip_tests,
            dry_run=dry_run,
            progress_callback=_progress_callback,
        )
        
        if result.success:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 'Complete!'
            jobs[job_id]['pr_url'] = getattr(result, 'pr_url', None)
            jobs[job_id]['branch_name'] = result.branch_name
            jobs[job_id]['files_changed'] = result.files_changed
            jobs[job_id]['dry_run'] = dry_run
            jobs[job_id]['reasoning'] = getattr(result, 'reasoning', {})
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = getattr(result, 'error', 'Unknown error')
            
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)


@app.post("/api/fix")
async def fix_issue(request: FixRequest, background_tasks: BackgroundTasks):
    """Start fixing an issue."""
    issue_url = request.issue_url.strip()
    
    if not issue_url:
        raise HTTPException(status_code=400, detail="Issue URL is required")
    
    valid, owner, repo, issue_number = validate_issue_url(issue_url)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid GitHub issue URL. Expected format: https://github.com/owner/repo/issues/123")
    
    github_token = request.github_token.strip() if request.github_token else None
    
    job_id = f"{owner}_{repo}_{issue_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    jobs[job_id] = {
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'issue_url': issue_url,
        'owner': owner,
        'repo': repo,
        'issue_number': issue_number,
        'skip_tests': request.skip_tests,
        'dry_run': request.dry_run,
        'progress': 'Queued...'
    }
    
    # We use threading.Thread instead of background_tasks.add_task to avoid blocking the async event loop with synchronous AI tasks
    thread = threading.Thread(
        target=run_reporepair_task,
        args=(job_id, issue_url, request.skip_tests, request.dry_run, github_token)
    )
    thread.daemon = True
    thread.start()
    
    return {
        'job_id': job_id,
        'status': 'queued',
        'message': 'Job started successfully'
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.post("/api/jobs/{job_id}/approve")
async def approve_job(job_id: str):
    """Approve a job and create the PR."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    if job['status'] != 'completed' or not job.get('dry_run'):
        raise HTTPException(status_code=400, detail="Job is not awaiting approval")
        
    try:
        settings = get_settings()
        github_tool = GitHubTool(settings.github_token)
        
        # Determine the correct branch naming based on fork logic
        # In a full implementation, the orchestrator should store this head_branch in the job state
        # For now, we will construct it simply
        pr_url = github_tool.create_pull_request(
            owner=job['owner'],
            repo=job['repo'],
            title=f"Fix: {job.get('issue_title', 'AI Generated Fix')} (#{job['issue_number']})",
            body="Resolves #" + str(job['issue_number']) + "\n\n### What changed\n\nAI generated patch approved by human.\n\n---\n<sub>*Generated by [RepoRepair](https://github.com/tanishbhandari11t/Repo-Repair) made by Tanish*</sub>",
            head_branch=job['branch_name'],
            draft=True
        )
        
        job['pr_url'] = pr_url
        job['dry_run'] = False # Mark as no longer pending approval
        
        return {"status": "success", "pr_url": pr_url}
        
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    sorted_jobs = sorted(
        jobs.items(),
        key=lambda x: x[1].get('created_at', ''),
        reverse=True
    )
    return {
        'jobs': [
            {'job_id': job_id, **job_data}
            for job_id, job_data in sorted_jobs
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        settings = get_settings()
        return {
            'status': 'healthy',
            'github_token_configured': bool(settings.github_token),
            'gemini_api_key_configured': bool(settings.gemini_api_key),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
