// RepoRepair Premium Application Client Interface

let currentJobId = null;
let pollInterval = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initGitHubAuth();
    loadRecentJobs();
    
    document.getElementById('fixForm').addEventListener('submit', handleSubmit);
    document.getElementById('resetBtn').addEventListener('click', resetForm);
});

/* ==========================================================================
   GitHub Auth Connectivity Section
   ========================================================================== */
function initGitHubAuth() {
    const gitTokenInput = document.getElementById('gitToken');
    const btnConnect = document.getElementById('btnConnect');
    const btnDisconnect = document.getElementById('btnDisconnect');
    const togglePass = document.getElementById('togglePass');
    
    // Check if token already exists in localStorage
    const savedToken = localStorage.getItem('reporepair_github_token');
    if (savedToken) {
        gitTokenInput.value = savedToken;
        updateGitStatus(true);
    } else {
        updateGitStatus(false);
    }
    
    // Password visibility toggle
    togglePass.addEventListener('click', () => {
        const type = gitTokenInput.getAttribute('type') === 'password' ? 'text' : 'password';
        gitTokenInput.setAttribute('type', type);
        togglePass.querySelector('i').classList.toggle('fa-eye');
        togglePass.querySelector('i').classList.toggle('fa-eye-slash');
    });
    
    // Connect button click
    btnConnect.addEventListener('click', () => {
        const tokenValue = gitTokenInput.value.trim();
        if (!tokenValue) {
            alert('Please enter a valid GitHub Personal Access Token (PAT).');
            return;
        }
        
        localStorage.setItem('reporepair_github_token', tokenValue);
        updateGitStatus(true);
        alert('GitHub Token saved locally and connected successfully!');
    });
    
    // Disconnect button click
    btnDisconnect.addEventListener('click', () => {
        localStorage.removeItem('reporepair_github_token');
        gitTokenInput.value = '';
        updateGitStatus(false);
        alert('GitHub connection disconnected and token removed.');
    });
}

function updateGitStatus(isConnected) {
    const btnConnect = document.getElementById('btnConnect');
    const btnDisconnect = document.getElementById('btnDisconnect');
    const headerGitStatus = document.getElementById('headerGitStatus');
    const gitTokenInput = document.getElementById('gitToken');
    
    if (isConnected) {
        btnConnect.style.display = 'none';
        btnDisconnect.style.display = 'inline-flex';
        gitTokenInput.disabled = true;
        
        // Update header indicator
        headerGitStatus.innerHTML = `
            <span class="status-dot connected"></span>
            <span class="status-text"><i class="fa-brands fa-github"></i> Connected (PAT Active)</span>
        `;
    } else {
        btnConnect.style.display = 'inline-flex';
        btnDisconnect.style.display = 'none';
        gitTokenInput.disabled = false;
        
        // Update header indicator
        headerGitStatus.innerHTML = `
            <span class="status-dot disconnected"></span>
            <span class="status-text">GitHub Account: Not Connected</span>
        `;
    }
}

/* ==========================================================================
   Form Handling & Execution Loop
   ========================================================================== */
async function handleSubmit(e) {
    e.preventDefault();
    
    const issueUrl = document.getElementById('issueUrl').value.trim();
    
    // Read selections
    const dryRun = document.getElementById('modeDry').checked;
    const skipTests = document.getElementById('valSkip').checked;
    const githubToken = localStorage.getItem('reporepair_github_token') || '';
    
    if (!issueUrl) {
        alert('Please enter a GitHub issue URL.');
        return;
    }
    
    // Validate GitHub Issue URL format
    const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+\/issues\/\d+$/;
    if (!urlPattern.test(issueUrl)) {
        alert('Invalid GitHub issue URL format.\n\nExpected: https://github.com/owner/repo/issues/123');
        return;
    }
    
    // Disable submission trigger
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    document.querySelector('.btn-text').style.display = 'none';
    document.querySelector('.btn-loader').style.display = 'inline-flex';
    
    try {
        // Start background fix task
        const response = await fetch('/api/fix', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                issue_url: issueUrl,
                dry_run: dryRun,
                skip_tests: skipTests,
                github_token: githubToken
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to start job');
        }
        
        currentJobId = data.job_id;
        
        // Initialize status card in DOM
        document.getElementById('statusSection').style.display = 'block';
        document.getElementById('jobId').textContent = `Job: ${currentJobId.slice(-15)}`;
        document.getElementById('statusBadge').textContent = 'Queued';
        document.getElementById('statusBadge').className = 'status-badge queued';
        
        // Reset pipeline step UI styling
        resetPipelineSteps();
        
        // Smooth scroll to tracking terminal
        document.getElementById('statusSection').scrollIntoView({ behavior: 'smooth' });
        
        // Initialize active polling
        pollStatus();
        pollInterval = setInterval(pollStatus, 2500);
        
    } catch (error) {
        alert(`Error triggering job: ${error.message}`);
        resetForm();
    }
}

// Poll job status from endpoint
async function pollStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to retrieve job status');
        }
        
        updateJobStatusUI(data);
        
        // Conclude polling if job is completed or errors
        if (data.status === 'completed' || data.status === 'error') {
            clearInterval(pollInterval);
            pollInterval = null;
            document.getElementById('resetBtn').style.display = 'inline-flex';
            document.getElementById('submitBtn').disabled = false;
            document.querySelector('.btn-text').style.display = 'inline-flex';
            document.querySelector('.btn-loader').style.display = 'none';
            loadRecentJobs();
        }
        
    } catch (error) {
        console.error('Status check polling failed:', error);
    }
}

/* ==========================================================================
   Pipeline Map States & UI Updating
   ========================================================================== */
function resetPipelineSteps() {
    const steps = ['step_plan', 'step_search', 'step_code', 'step_validate', 'step_finalize'];
    steps.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = 'pipeline-step';
    });
    
    // Connectors
    document.querySelectorAll('.pipeline-connector').forEach(el => {
        el.className = 'pipeline-connector';
    });
}

function parsePipelineProgress(progressText, status) {
    const text = (progressText || '').toLowerCase();
    
    resetPipelineSteps();
    
    const stepPlan = document.getElementById('step_plan');
    const stepSearch = document.getElementById('step_search');
    const stepCode = document.getElementById('step_code');
    const stepValidate = document.getElementById('step_validate');
    const stepFinalize = document.getElementById('step_finalize');
    
    const conn1 = document.querySelectorAll('.pipeline-connector')[0];
    const conn2 = document.querySelectorAll('.pipeline-connector')[1];
    const conn3 = document.querySelectorAll('.pipeline-connector')[2];
    const conn4 = document.querySelectorAll('.pipeline-connector')[3];
    
    if (status === 'error') {
        return; // Don't highlight pipeline active steps during error
    }
    
    if (status === 'completed') {
        // All complete
        [stepPlan, stepSearch, stepCode, stepValidate, stepFinalize].forEach(el => {
            if (el) el.className = 'pipeline-step completed';
        });
        [conn1, conn2, conn3, conn4].forEach(el => {
            if (el) el.className = 'pipeline-connector active';
        });
        return;
    }
    
    // Queued
    if (text.includes('queued')) {
        if (stepPlan) stepPlan.className = 'pipeline-step active';
        return;
    }
    
    // Plan
    if (text.includes('initializing') || text.includes('fetching issue')) {
        if (stepPlan) stepPlan.className = 'pipeline-step active';
        return;
    }
    
    // Search
    if (text.includes('cloning repository') || text.includes('running ai analysis') || text.includes('search') || text.includes('indexing')) {
        if (stepPlan) stepPlan.className = 'pipeline-step completed';
        if (conn1) conn1.className = 'pipeline-connector active';
        if (stepSearch) stepSearch.className = 'pipeline-step active';
        return;
    }
    
    // Code
    if (text.includes('code') || text.includes('generation') || text.includes('applying changes') || text.includes('writing')) {
        if (stepPlan) stepPlan.className = 'pipeline-step completed';
        if (stepSearch) stepSearch.className = 'pipeline-step completed';
        if (conn1) conn1.className = 'pipeline-connector active';
        if (conn2) conn2.className = 'pipeline-connector active';
        if (stepCode) stepCode.className = 'pipeline-step active';
        return;
    }
    
    // Validate
    if (text.includes('validation') || text.includes('running tests') || text.includes('docker') || text.includes('testing')) {
        if (stepPlan) stepPlan.className = 'pipeline-step completed';
        if (stepSearch) stepSearch.className = 'pipeline-step completed';
        if (stepCode) stepCode.className = 'pipeline-step completed';
        if (conn1) conn1.className = 'pipeline-connector active';
        if (conn2) conn2.className = 'pipeline-connector active';
        if (conn3) conn3.className = 'pipeline-connector active';
        if (stepValidate) stepValidate.className = 'pipeline-step active';
        return;
    }
    
    // Finalize
    if (text.includes('finalize') || text.includes('committing') || text.includes('pushing') || text.includes('pull request')) {
        if (stepPlan) stepPlan.className = 'pipeline-step completed';
        if (stepSearch) stepSearch.className = 'pipeline-step completed';
        if (stepCode) stepCode.className = 'pipeline-step completed';
        if (stepValidate) stepValidate.className = 'pipeline-step completed';
        if (conn1) conn1.className = 'pipeline-connector active';
        if (conn2) conn2.className = 'pipeline-connector active';
        if (conn3) conn3.className = 'pipeline-connector active';
        if (conn4) conn4.className = 'pipeline-connector active';
        if (stepFinalize) stepFinalize.className = 'pipeline-step active';
        return;
    }
    
    // Fallback default running: plan active
    if (stepPlan) stepPlan.className = 'pipeline-step active';
}

function updateJobStatusUI(data) {
    // 1. Update Badge
    const badge = document.getElementById('statusBadge');
    badge.textContent = data.status;
    badge.className = `status-badge ${data.status}`;
    
    // 2. Update issue visual headers
    if (data.issue_title) {
        document.getElementById('issueInfo').style.display = 'block';
        document.getElementById('issueTitle').textContent = data.issue_title;
        document.getElementById('issueRepo').innerHTML = `
            <i class="fa-solid fa-code-branch"></i> Repository: <strong>${data.owner}/${data.repo}</strong> #${data.issue_number}
        `;
    }
    
    // 3. Update Progress log text
    if (data.progress) {
        document.getElementById('progressText').innerHTML = `
            <span style="color: #10b981;">&gt;</span> ${data.progress}
        `;
        
        // Update bar fill percentage
        const progressFill = document.getElementById('progressFill');
        if (data.status === 'queued') {
            progressFill.style.width = '10%';
        } else if (data.status === 'running') {
            progressFill.style.width = '65%';
        } else if (data.status === 'completed') {
            progressFill.style.width = '100%';
            progressFill.style.background = 'var(--success)';
        } else if (data.status === 'error') {
            progressFill.style.width = '100%';
            progressFill.style.background = 'var(--error)';
        }
        
        // Dynamically shift visual map steps
        parsePipelineProgress(data.progress, data.status);
    }
    
    // 4. Render Outcomes
    if (data.status === 'completed') {
        showSuccessOutcome(data);
    } else if (data.status === 'error') {
        showErrorOutcome(data);
    }
}

// Show success result details
function showSuccessOutcome(data) {
    document.getElementById('resultContainer').style.display = 'block';
    document.getElementById('successResult').style.display = 'flex';
    document.getElementById('errorResult').style.display = 'none';
    
    let html = '<div style="display: flex; flex-direction: column; gap: 0.65rem;">';
    
    if (data.dry_run) {
        html += `<p><i class="fa-solid fa-flask text-accent"></i> <strong>Execution Mode:</strong> Dry Run (No pull request was created)</p>`;
    }
    
    if (data.pr_url) {
        html += `<p><i class="fa-solid fa-code-pull-request text-primary"></i> <strong>Pull Request Created:</strong> <a href="${data.pr_url}" target="_blank">${data.pr_url} <i class="fa-solid fa-up-right-from-square" style="font-size: 0.75rem;"></i></a></p>`;
    }
    
    if (data.branch_name) {
        html += `<p><i class="fa-solid fa-code-fork text-muted"></i> <strong>Feature Branch Name:</strong> <code>${data.branch_name}</code></p>`;
    }
    
    if (data.files_changed && data.files_changed.length > 0) {
        html += `<p><i class="fa-solid fa-file-pen text-muted"></i> <strong>Files Patched:</strong> ${data.files_changed.length}</p>`;
        html += '<ul style="margin-left: 1.5rem; color: var(--text-muted); list-style-type: square; font-size: 0.85rem;">';
        data.files_changed.slice(0, 5).forEach(file => {
            html += `<li>${file}</li>`;
        });
        if (data.files_changed.length > 5) {
            html += `<li>... and ${data.files_changed.length - 5} more files</li>`;
        }
        html += '</ul>';
    }
    
    if (data.pr_url) {
        html += `
            <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; font-size: 0.85rem;">
                <i class="fa-solid fa-circle-exclamation text-primary"></i> <strong>PR Safety Audit:</strong> This pull request was pushed as a <strong>Draft</strong>. Please navigate to GitHub to review the diffs prior to merging.
            </div>
        `;
    }
    
    html += '</div>';
    document.getElementById('successDetails').innerHTML = html;
}

// Show error result details
function showErrorOutcome(data) {
    document.getElementById('resultContainer').style.display = 'block';
    document.getElementById('errorResult').style.display = 'flex';
    document.getElementById('successResult').style.display = 'none';
    
    document.getElementById('errorDetails').innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            <p><strong>Termination Status:</strong></p>
            <p style="color: var(--error); font-family: monospace; background: rgba(0,0,0,0.4); padding: 0.75rem; border: 1px solid rgba(244,63,94,0.15); border-radius: 8px; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all;">${data.error || 'Connection failed or RAG timeout'}</p>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;"><i class="fa-solid fa-circle-info"></i> Detailed stack logs are recorded in your server directory at <code>webapp.log</code>.</p>
        </div>
    `;
}

// Reset form to clear tracking
function resetForm() {
    currentJobId = null;
    
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    // Reset Form fields
    document.getElementById('fixForm').reset();
    document.getElementById('modeDry').checked = true;
    document.getElementById('valSkip').checked = true;
    
    // Enable submit button
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = false;
    document.querySelector('.btn-text').style.display = 'inline-flex';
    document.querySelector('.btn-loader').style.display = 'none';
    
    // Hide status panel
    document.getElementById('statusSection').style.display = 'none';
    document.getElementById('issueInfo').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('resetBtn').style.display = 'none';
    
    // Reset bar fill
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressFill').style.background = 'linear-gradient(90deg, var(--primary), var(--accent))';
    
    // Scroll to dashboard top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ==========================================================================
   Execution History Section
   ========================================================================== */
async function loadRecentJobs() {
    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();
        
        const jobsList = document.getElementById('jobsList');
        
        if (!data.jobs || data.jobs.length === 0) {
            jobsList.innerHTML = '<p class="empty-state">No jobs run yet. Initialize the fix engine to start auditing repositories!</p>';
            return;
        }
        
        let html = '<div class="jobs-list">';
        
        data.jobs.slice(0, 5).forEach(job => {
            const date = new Date(job.created_at).toLocaleString();
            const statusClass = job.status;
            
            html += `
                <div class="job-item ${statusClass}" onclick="selectJob('${job.job_id}')" title="Click to view details and status of this run">
                    <div class="job-header">
                        <div class="job-title"><i class="fa-solid fa-clipboard-list text-muted"></i> ${job.issue_title || 'Running Analysis...'}</div>
                        <span class="job-status ${statusClass}">${job.status}</span>
                    </div>
                    <div class="job-meta">
                        Repository: <strong>${job.owner}/${job.repo}</strong> #${job.issue_number} • Run at ${date}
                    </div>
                    ${job.pr_url ? `<div class="job-meta" style="margin-top: 0.5rem;" onclick="event.stopPropagation();"><a href="${job.pr_url}" target="_blank"><i class="fa-solid fa-square-arrow-up-right"></i> View Draft PR</a></div>` : ''}
                </div>
            `;
        });
        
        html += '</div>';
        jobsList.innerHTML = html;
        
    } catch (error) {
        console.error('Failed to load past jobs list:', error);
    }
}

// Select a job to load into tracking interface
async function selectJob(jobId) {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    currentJobId = jobId;
    
    try {
        const response = await fetch(`/api/status/${jobId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to retrieve job details');
        }
        
        // Ensure status section terminal is visible
        document.getElementById('statusSection').style.display = 'block';
        document.getElementById('jobId').textContent = `Job: ${currentJobId.slice(-15)}`;
        
        // Reset outcomes
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('successResult').style.display = 'none';
        document.getElementById('errorResult').style.display = 'none';
        
        updateJobStatusUI(data);
        
        // If the job is still active (queued/running), restart the polling loop
        if (data.status === 'queued' || data.status === 'running') {
            document.getElementById('resetBtn').style.display = 'none';
            document.getElementById('submitBtn').disabled = true;
            document.querySelector('.btn-text').style.display = 'none';
            document.querySelector('.btn-loader').style.display = 'inline-flex';
            
            pollInterval = setInterval(pollStatus, 2500);
        } else {
            document.getElementById('resetBtn').style.display = 'inline-flex';
            document.getElementById('submitBtn').disabled = false;
            document.querySelector('.btn-text').style.display = 'inline-flex';
            document.querySelector('.btn-loader').style.display = 'none';
        }
        
        // Smoothly scroll down to terminal progress box
        document.getElementById('statusSection').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        alert(`Failed to load job details: ${error.message}`);
    }
}

