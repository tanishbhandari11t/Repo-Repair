"""Web interface for RepoRepair - Flask application."""

import os
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from agents.orchestrator import Orchestrator

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

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
jobs = {}


def validate_issue_url(url: str) -> tuple[bool, str, str, int]:
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
        
        # Validate URL
        valid, owner, repo, issue_number = validate_issue_url(issue_url)
        if not valid:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = 'Invalid GitHub issue URL'
            return
        
        jobs[job_id]['progress'] = f'Fetching issue #{issue_number}...'
        
        # Initialize tools
        active_token = github_token or settings.github_token
        github_tool = GitHubTool(active_token)
        git_tool = GitTool(settings.workspace_dir)
        
        # Fetch issue
        issue = github_tool.get_issue(owner, repo, issue_number)
        jobs[job_id]['issue_title'] = issue.title
        jobs[job_id]['progress'] = f'Cloning repository {owner}/{repo}...'
        
        # Clone repository
        repo_path = git_tool.clone_repository(owner, repo, active_token)
        jobs[job_id]['progress'] = 'Running AI analysis...'
        
        # Run orchestrator
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
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 'Complete!'
            jobs[job_id]['pr_url'] = result.pr_url
            jobs[job_id]['branch_name'] = result.branch_name
            jobs[job_id]['files_changed'] = result.files_changed
            jobs[job_id]['reasoning_trace'] = result.reasoning_trace
            jobs[job_id]['dry_run'] = dry_run
        else:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = result.error
            jobs[job_id]['reasoning_trace'] = result.reasoning_trace
            
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/fix', methods=['POST'])
def fix_issue():
    """Start fixing an issue."""
    data = request.json
    issue_url = data.get('issue_url', '').strip()
    skip_tests = data.get('skip_tests', False)
    dry_run = data.get('dry_run', False)
    
    if not issue_url:
        return jsonify({'error': 'Issue URL is required'}), 400
    
    # Validate URL
    valid, owner, repo, issue_number = validate_issue_url(issue_url)
    if not valid:
        return jsonify({'error': 'Invalid GitHub issue URL. Expected format: https://github.com/owner/repo/issues/123'}), 400
    
    github_token = data.get('github_token', '').strip() or None
    
    # Create job
    job_id = f"{owner}_{repo}_{issue_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    jobs[job_id] = {
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'issue_url': issue_url,
        'owner': owner,
        'repo': repo,
        'issue_number': issue_number,
        'skip_tests': skip_tests,
        'dry_run': dry_run,
        'progress': 'Queued...'
    }
    
    # Start background task
    thread = threading.Thread(
        target=run_reporepair_task,
        args=(job_id, issue_url, skip_tests, dry_run, github_token)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'Job started successfully'
    })


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])


@app.route('/api/jobs')
def list_jobs():
    """List all jobs."""
    return jsonify({
        'jobs': [
            {
                'job_id': job_id,
                **job_data
            }
            for job_id, job_data in sorted(
                jobs.items(),
                key=lambda x: x[1].get('created_at', ''),
                reverse=True
            )
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        settings = get_settings()
        return jsonify({
            'status': 'healthy',
            'github_token_configured': bool(settings.github_token),
            'gemini_api_key_configured': bool(settings.gemini_api_key),
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("RepoRepair Web Interface")
    print("=" * 60)
    print()
    print("Starting server at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
