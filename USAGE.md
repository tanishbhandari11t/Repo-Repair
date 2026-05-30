# RepoRepair Usage Guide

Complete guide for using RepoRepair to convert GitHub issues into pull requests.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Installation

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (for running tests)
- GitHub Personal Access Token
- Gemini API Key

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/RepoRepair.git
cd RepoRepair

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Configuration

### Step 1: Get GitHub Token

1. Go to GitHub Settings → [Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "RepoRepair"
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `read:org` (Optional: Read org and team membership)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### Step 2: Get Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new project or select existing one
5. Copy your API key

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your tokens
# On Windows:
notepad .env
# On macOS/Linux:
nano .env
```

Add your credentials:

```env
GITHUB_TOKEN=ghp_your_actual_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Verify Configuration

```bash
python -m cli.main config
```

You should see:

```
RepoRepair Configuration

Workspace: ./workspace
Log Level: INFO
Max Diff Lines: 300
Planning Model: gemini-1.5-pro
Coding Model: gemini-1.5-flash

GitHub Token: ✓ Set
Gemini API Key: ✓ Set
```

## Basic Usage

### Simple Fix Command

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123
```

This will:
1. Fetch the issue from GitHub
2. Clone the repository
3. Analyze the issue with AI
4. Search for relevant code files
5. Generate a code fix
6. Run tests in Docker
7. Create a draft Pull Request

### Dry Run (No PR Creation)

Test the workflow without creating a PR:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 --dry-run
```

### Skip Tests

If tests are slow or you want to skip validation:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 --skip-tests
```

**⚠️ Warning:** Skipping tests is not recommended for production use.

### Verbose Logging

Get detailed logs of what's happening:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 --verbose
```

### Custom Workspace

Use a different workspace directory:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 --workspace ./my-workspace
```

## Advanced Usage

### Combining Options

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 \
    --verbose \
    --skip-tests \
    --workspace ./custom-workspace
```

### Using as a Python Module

```python
from config import get_settings
from tools.github_tool import GitHubTool
from tools.git_tool import GitTool
from agents.orchestrator import Orchestrator

settings = get_settings()

github_tool = GitHubTool(settings.github_token)
git_tool = GitTool(settings.workspace_dir)

orchestrator = Orchestrator(
    github_tool=github_tool,
    git_tool=git_tool,
    settings=settings,
)

issue = github_tool.get_issue("owner", "repo", 123)
repo_path = git_tool.clone_repository("owner", "repo", settings.github_token)

result = orchestrator.run(
    owner="owner",
    repo="repo",
    issue_number=123,
    issue=issue,
    repo_path=repo_path,
    skip_tests=False,
    dry_run=False,
)

if result.success:
    print(f"PR created: {result.pr_url}")
else:
    print(f"Failed: {result.error}")
```

### Environment Variables

Override settings with environment variables:

```bash
# Use different models
export GEMINI_PLANNING_MODEL=gemini-1.5-flash
export GEMINI_CODING_MODEL=gemini-1.5-pro

# Change workspace
export WORKSPACE_DIR=/tmp/reporepair-workspace

# Adjust max diff size
export MAX_DIFF_LINES=500

python -m cli.main fix <issue-url>
```

## Troubleshooting

### "Docker not available"

**Problem:** Tests fail with Docker error.

**Solution:**
1. Install Docker Desktop
2. Start Docker daemon
3. Verify: `docker ps`
4. Or skip tests: `--skip-tests`

### "GitHub token invalid"

**Problem:** Cannot fetch issues or create PRs.

**Solution:**
1. Check token in `.env`
2. Verify token has correct scopes
3. Generate new token if expired

### "Gemini API rate limit"

**Problem:** Too many requests to Gemini.

**Solution:**
1. Wait a few minutes
2. Use `gemini-1.5-flash` instead of `pro` (faster)
3. Check your API quota at Google AI Studio

### "No relevant files found"

**Problem:** Searcher can't find relevant code.

**Solution:**
1. Issue description may be too vague
2. Try rephrasing the issue description
3. Repository may be too small/empty

### "Tests failed after fix"

**Problem:** Generated code breaks tests.

**Solution:**
1. Review the PR diff manually
2. The agent will retry up to 3 times automatically
3. May need manual intervention for complex issues

### "Permission denied" on Windows

**Problem:** Can't clone repository or write files.

**Solution:**
1. Run as administrator
2. Check antivirus isn't blocking
3. Use different workspace directory

## Best Practices

### Writing Good Issues

For best results, issues should:

1. **Be specific**: "Button doesn't respond to clicks" > "App broken"
2. **Include context**: Where the bug occurs, what should happen
3. **Have examples**: Steps to reproduce, error messages
4. **Be single-purpose**: One bug per issue

### Good Issue Example

```
Title: Login button doesn't work on mobile Safari

Description:
When clicking the login button on the /login page using Safari on iOS,
nothing happens. The button should submit the form and redirect to /dashboard.

Steps to reproduce:
1. Open app on iPhone Safari
2. Navigate to /login
3. Enter credentials
4. Click "Login" button
5. Nothing happens

Expected: Should redirect to /dashboard
Actual: Button click does nothing

Browser: Safari iOS 16.5
```

### When to Use RepoRepair

**Good use cases:**
- Simple bug fixes (null checks, typos, logic errors)
- Adding missing error handling
- Fixing deprecated API usage
- Small feature additions
- Documentation updates

**Not recommended for:**
- Major architecture changes
- Security-critical code
- Performance optimization (needs profiling)
- Complex business logic
- Breaking changes

### Reviewing AI-Generated PRs

Always review the PR before merging:

1. **Read the diff** - Understand what changed
2. **Run tests locally** - Don't just trust CI
3. **Check for edge cases** - AI might miss them
4. **Verify style** - Ensure it matches your codebase
5. **Test manually** - Run the app yourself

### Security Considerations

1. **Never commit secrets** - RepoRepair won't, but double-check
2. **Review all changes** - Don't blindly merge
3. **Use draft PRs** - Default behavior, good practice
4. **Limit token scopes** - Only give necessary permissions
5. **Rotate tokens** - Regenerate periodically

## Workflow Examples

### Example 1: Simple Bug Fix

```bash
# Issue: "Fix null pointer exception in user profile"
python -m cli.main fix https://github.com/myapp/backend/issues/42 -v
```

Output:
```
✓ Issue fetched: Fix null pointer exception in user profile
✓ Repository cloned
✓ Found 3 relevant files
✓ Generated code changes
✓ Tests passed (12.3s)
✓ Draft PR created: https://github.com/myapp/backend/pull/123
```

### Example 2: Feature Request

```bash
# Issue: "Add dark mode toggle to settings"
python -m cli.main fix https://github.com/myapp/frontend/issues/89
```

Output:
```
✓ Issue fetched: Add dark mode toggle to settings
✓ Repository cloned
✓ Found 5 relevant files
✓ Generated code changes
✓ Tests passed (8.1s)
✓ Draft PR created: https://github.com/myapp/frontend/pull/90
```

### Example 3: Quick Test

```bash
# Test without creating PR
python -m cli.main fix https://github.com/test/repo/issues/1 --dry-run --verbose
```

## Getting Help

- **Logs**: Check `reporepair.log` for detailed execution logs
- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/RepoRepair/issues)
- **Discussions**: Ask questions in [Discussions](https://github.com/yourusername/RepoRepair/discussions)
- **Documentation**: See main [README.md](README.md)

## Next Steps

After successful setup:

1. Try a simple issue first
2. Review the generated PR
3. Adjust settings if needed
4. Integrate into your workflow
5. Star the repo if you find it useful! ⭐
