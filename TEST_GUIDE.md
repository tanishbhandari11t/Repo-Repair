# RepoRepair Test Guide

## ✅ Configuration Status

Your RepoRepair is now fully set up with:
- ✅ GitHub Token: Configured
- ✅ Gemini API Key: Configured
- ✅ All dependencies installed
- ✅ Ready to test!

## 🧪 How to Test RepoRepair

### Option 1: Test with a Demo Repository (Recommended)

I recommend testing with a simple public repository first. Here are some options:

#### Test Scenario 1: Simple Python Bug Fix

1. **Open your terminal** in the RepoRepair folder
2. **Activate virtual environment:**
   ```cmd
   venv\Scripts\activate
   ```

3. **Run a DRY RUN first** (no actual PR will be created):
   ```cmd
   py -m cli.main fix https://github.com/octocat/Hello-World/issues/1 --dry-run --skip-tests
   ```

   This will:
   - Fetch the issue
   - Clone the repository
   - Analyze the problem
   - Generate a fix
   - Show you what it would do (WITHOUT creating a PR)

#### Test Scenario 2: Use Your Own Repository

If you have your own repository with an open issue:

1. **Create a test issue** in your repository:
   - Go to your GitHub repo
   - Click "Issues" → "New issue"
   - Title: "Fix typo in README"
   - Description: "The word 'teh' should be 'the' in README.md"

2. **Copy the issue URL** (e.g., `https://github.com/yourusername/yourrepo/issues/1`)

3. **Run RepoRepair:**
   ```cmd
   py -m cli.main fix YOUR_ISSUE_URL --dry-run
   ```

### Option 2: Create Draft PR (Real Test)

Once you're comfortable, try creating a real draft PR:

```cmd
py -m cli.main fix YOUR_ISSUE_URL
```

This will:
1. Analyze the issue
2. Generate a code fix
3. Run tests (if available)
4. Create a **DRAFT** Pull Request
5. You can review and approve/reject it

## 📝 Command Reference

### Basic Commands

```cmd
# Activate environment (always do this first!)
venv\Scripts\activate

# Check configuration
py -m cli.main config

# Dry run (no PR created)
py -m cli.main fix <issue-url> --dry-run

# Skip tests (faster for testing)
py -m cli.main fix <issue-url> --skip-tests

# Verbose mode (see what's happening)
py -m cli.main fix <issue-url> --verbose

# Full run (creates draft PR)
py -m cli.main fix <issue-url>
```

### Understanding the Output

```
✓ Issue fetched: [Issue Title]          ← Issue loaded successfully
✓ Repository cloned                      ← Repo downloaded
✓ Found 3 relevant files                 ← AI found where to fix
✓ Generated code changes                 ← Fix created
✓ Tests passed (8.2s)                    ← Validation successful
✓ Draft PR created: [PR URL]             ← Success!
```

## 🎯 Example Test Issues

You can test with these public repositories:

### Easy Test (Recommended for first try):

Create your own test issue in a personal repository:

1. **Create a simple repo:**
   - Go to GitHub → New Repository
   - Name: `test-reporepair`
   - Add README
   - Create repository

2. **Create a test file** (`test.py`):
   ```python
   def add(a, b):
       return a - b  # Bug: should be +
   ```

3. **Create an issue:**
   - Title: "Fix add function"
   - Description: "The add function is subtracting instead of adding. It should return a + b"

4. **Copy issue URL** and test:
   ```cmd
   py -m cli.main fix https://github.com/YOUR_USERNAME/test-reporepair/issues/1 --dry-run
   ```

## ⚠️ Important Notes

### Before Running:

1. **Always activate the virtual environment:**
   ```cmd
   venv\Scripts\activate
   ```

2. **Make sure Docker is running** (if you want to run tests):
   - Open Docker Desktop
   - Or use `--skip-tests` flag

3. **Use `--dry-run` first** to see what will happen

### Safety Features:

- ✅ Always creates **DRAFT** Pull Requests
- ✅ Never auto-merges code
- ✅ You must manually review and approve
- ✅ All changes are logged
- ✅ Tests run in isolated Docker containers

## 🐛 Troubleshooting

### "Module not found"
**Fix:** Activate virtual environment first
```cmd
venv\Scripts\activate
```

### "Docker not available"
**Fix:** Either start Docker Desktop or use:
```cmd
py -m cli.main fix <issue-url> --skip-tests
```

### "GitHub API rate limit"
**Fix:** Wait a few minutes, or use your personal repositories

### "Permission denied"
**Fix:** Make sure your GitHub token has `repo` and `workflow` permissions

## 📊 What to Expect

### Timeline for a typical run:
- **Fetching issue:** 2-5 seconds
- **Cloning repository:** 5-15 seconds (depends on repo size)
- **AI Analysis:** 10-20 seconds
- **Code generation:** 15-30 seconds
- **Running tests:** 30-120 seconds (if enabled)
- **Creating PR:** 3-5 seconds

**Total:** 1-3 minutes for most issues

## 🎓 Next Steps

After your first successful test:

1. ✅ Review the draft PR on GitHub
2. ✅ Check if the fix makes sense
3. ✅ Run tests locally
4. ✅ Approve and merge if good
5. ✅ Try with more complex issues!

## 🆘 Need Help?

- Check `reporepair.log` for detailed logs
- Read `USAGE.md` for advanced features
- See `README.md` for architecture details

## 🎉 Ready to Test!

**Your first command:**

```cmd
# Activate environment
venv\Scripts\activate

# Run a dry-run test
py -m cli.main fix YOUR_GITHUB_ISSUE_URL --dry-run --skip-tests

# Or just check the config
py -m cli.main config
```

Good luck! 🚀

---

**Remember:** RepoRepair is a tool to ASSIST you, not replace you. Always review AI-generated code before merging!
