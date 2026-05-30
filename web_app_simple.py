"""Simplified Web interface for RepoRepair - Flask application."""

import os
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

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

# Store job status in memory
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
        'progress': 'Please use CLI for now: py -m cli.main fix ' + issue_url + (' --dry-run' if dry_run else '') + (' --skip-tests' if skip_tests else ''),
        'error': 'Full web interface requires additional packages. Use CLI: py -m cli.main fix <url>'
    }
    
    # Mark as error (instructing to use CLI)
    jobs[job_id]['status'] = 'error'
    
    return jsonify({
        'job_id': job_id,
        'status': 'error',
        'message': 'Please use the CLI version for now'
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
        from config import get_settings
        settings = get_settings()
        return jsonify({
            'status': 'healthy',
            'note': 'Simplified version - use CLI for full features',
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
    print("RepoRepair Web Interface (Simplified)")
    print("=" * 60)
    print()
    print("Note: Some packages are still installing.")
    print("For full functionality, use CLI:")
    print("  py -m cli.main fix <issue-url>")
    print()
    print("Web server at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
