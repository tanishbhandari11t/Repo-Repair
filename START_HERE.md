# 🚀 START HERE - RepoRepair

Welcome to RepoRepair! This is your production-grade AI tool for converting GitHub issues into Pull Requests.

## 🎯 What is RepoRepair?

RepoRepair is an intelligent CLI tool that:
1. Takes a GitHub issue URL
2. Analyzes the problem with AI
3. Finds relevant code in your repository
4. Generates a fix
5. Runs tests to validate
6. Creates a draft Pull Request for review

**Safety First:** RepoRepair NEVER auto-merges code. It always creates draft PRs for human review.

## ⚡ Quick Start (5 Minutes)

### Step 1: Install

**Windows:**
```cmd
install.bat
```

**macOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

### Step 2: Configure

Edit `.env` file with your API keys:

```env
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_key_here
```

**Get your tokens:**
- GitHub: https://github.com/settings/tokens (needs `repo`, `workflow` scopes)
- Gemini: https://ai.google.dev/

### Step 3: Activate Environment

**Windows:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Test Configuration

```bash
python -m cli.main config
```

Should show: ✓ GitHub Token Set, ✓ Gemini API Key Set

### Step 5: Fix Your First Issue!

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123
```

## 📚 Documentation

- **[README.md](README.md)** - Architecture and overview
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup guide
- **[USAGE.md](USAGE.md)** - Complete usage guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical details
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

## 🎓 Example Workflow

```bash
# 1. Activate environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 2. Fix an issue
python -m cli.main fix https://github.com/myproject/app/issues/42

# Output:
# ✓ Issue fetched: Fix login bug
# ✓ Repository cloned
# ✓ Found 3 relevant files
# ✓ Generated code changes
# ✓ Tests passed (8.2s)
# ✓ Draft PR created: https://github.com/myproject/app/pull/123

# 3. Review the PR on GitHub
# 4. Merge when satisfied!
```

## 🔧 Common Commands

```bash
# Basic fix
python -m cli.main fix <issue-url>

# Test without creating PR
python -m cli.main fix <issue-url> --dry-run

# Skip tests (not recommended)
python -m cli.main fix <issue-url> --skip-tests

# Verbose logging
python -m cli.main fix <issue-url> --verbose

# Check version
python -m cli.main version

# Show configuration
python -m cli.main config
```

## 🆘 Troubleshooting

### "Module not found"
**Fix:** Activate virtual environment first
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### "Docker not available"
**Fix:** Either install Docker Desktop, or skip tests:
```bash
python -m cli.main fix <issue-url> --skip-tests
```

### "GitHub token invalid"
**Fix:** Check `.env` file, verify token has `repo` and `workflow` scopes

### Need more help?
See [USAGE.md](USAGE.md) for detailed troubleshooting

## 🌟 Features

✅ Multi-agent AI system (Planner, Searcher, Coder, Validator)  
✅ Hybrid code search (RAG + grep)  
✅ Docker-based test execution  
✅ Always creates draft PRs (safe by default)  
✅ Beautiful CLI with progress indicators  
✅ Retry logic for failed fixes  
✅ Comprehensive logging  

## 🏗️ Architecture

```
GitHub Issue
     ↓
Planner Agent (analyzes issue)
     ↓
Searcher Agent (finds relevant files)
     ↓
Coder Agent (generates fix)
     ↓
Validator Agent (runs tests)
     ↓
Draft Pull Request
```

## 📊 Project Stats

- **Language:** Python 3.10+
- **Files:** 36 source files
- **Lines:** ~3,500 lines
- **Tests:** pytest with basic coverage
- **License:** MIT

## 🎯 Use Cases

**Good for:**
- Simple bug fixes
- Missing error handling
- Adding small features
- Fixing typos and deprecations

**Not recommended for:**
- Major architecture changes
- Security-critical code
- Complex business logic
- Breaking changes

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📞 Support

- **Questions:** GitHub Discussions
- **Bugs:** GitHub Issues
- **Documentation:** All markdown files in this repo

## 🎉 You're Ready!

RepoRepair is installed and ready to use. Try fixing an issue:

```bash
python -m cli.main fix <your-github-issue-url>
```

Happy fixing! 🔧

---

**Next Steps:**
1. Read [QUICKSTART.md](QUICKSTART.md) for detailed setup
2. Try [USAGE.md](USAGE.md) for advanced features
3. Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture

**Made with ❤️ using Python, LangGraph, and Gemini AI**
