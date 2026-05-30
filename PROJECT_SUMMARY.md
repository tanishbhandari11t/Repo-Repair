# RepoRepair - Project Summary

## 📋 Overview

**Project Name:** RepoRepair  
**Purpose:** AI-powered tool that converts GitHub issues into tested draft Pull Requests  
**Status:** ✅ MVP Complete  
**Language:** Python 3.10+  
**Architecture:** Multi-agent system using LangGraph  

## 🏗️ Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| CLI | Typer | Professional command-line interface |
| Orchestration | LangGraph | Multi-agent workflow management |
| LLM | Gemini 1.5 Flash/Pro | AI reasoning and code generation |
| GitHub | PyGithub | GitHub API integration |
| Git | GitPython | Repository operations |
| Search | ChromaDB + grep | Hybrid code search |
| Embeddings | sentence-transformers | Local semantic embeddings |
| Testing | Docker | Safe test execution |
| Config | pydantic-settings | Environment management |

### Multi-Agent System

```
┌─────────────┐
│  Planner    │  Analyzes issue, creates strategy
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Searcher   │  Finds relevant code files (RAG + grep)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Coder     │  Generates code fixes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validator  │  Runs tests, validates changes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Draft PR   │  Safe, reviewable pull request
└─────────────┘
```

## 📁 Project Structure

```
RepoRepair/
│
├── cli/
│   ├── __init__.py
│   └── main.py                    # CLI entry point (Typer)
│
├── agents/
│   ├── __init__.py
│   ├── planner.py                 # Issue analysis agent
│   ├── searcher.py                # Code search agent
│   ├── coder.py                   # Code generation agent
│   ├── validator.py               # Test validation agent
│   └── orchestrator.py            # LangGraph workflow
│
├── tools/
│   ├── __init__.py
│   ├── github_tool.py             # GitHub API operations
│   ├── git_tool.py                # Git operations
│   ├── search_tool.py             # Hybrid search (RAG + grep)
│   └── docker_tool.py             # Docker test runner
│
├── indexer/
│   ├── __init__.py
│   └── code_indexer.py            # ChromaDB indexing
│
├── tests/
│   ├── __init__.py
│   ├── test_github_tool.py        # GitHub tool tests
│   ├── test_models.py             # Model tests
│   └── test_cli.py                # CLI tests
│
├── .github/
│   └── workflows/
│       └── tests.yml              # CI/CD pipeline
│
├── __init__.py                    # Package metadata
├── config.py                      # Configuration management
├── models.py                      # Data models
├── requirements.txt               # Dependencies
├── pyproject.toml                 # Project config
├── setup.py                       # Setup script
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── LICENSE                        # MIT License
│
├── README.md                      # Main documentation
├── USAGE.md                       # Usage guide
├── QUICKSTART.md                  # Quick start guide
├── CONTRIBUTING.md                # Contribution guidelines
├── PROJECT_SUMMARY.md             # This file
│
├── install.bat                    # Windows install script
└── install.sh                     # Unix install script
```

## 🎯 Core Features

### ✅ Implemented

1. **CLI Interface**
   - Beautiful rich terminal output
   - Progress indicators
   - Verbose logging mode
   - Configuration management

2. **GitHub Integration**
   - Issue fetching
   - Repository cloning
   - Branch creation
   - Draft PR creation
   - PR description generation

3. **Multi-Agent Workflow**
   - Planner: Issue analysis and strategy
   - Searcher: Hybrid code search (RAG + grep)
   - Coder: AI-powered code generation
   - Validator: Docker-based test execution
   - Orchestrator: LangGraph workflow management

4. **Code Search**
   - ChromaDB vector database
   - Semantic search with embeddings
   - Keyword search with grep
   - Hybrid search combining both

5. **Safety Features**
   - Always creates draft PRs
   - Never auto-merges
   - Docker-isolated test execution
   - Retry logic (up to 3 attempts)
   - Diff size limits (300 lines)

6. **Testing & Quality**
   - Unit tests with pytest
   - GitHub Actions CI/CD
   - Code formatting (black)
   - Linting (ruff)
   - Type checking (mypy)

## 🔄 Workflow

### End-to-End Process

1. **User Input**
   ```bash
   python -m cli.main fix https://github.com/owner/repo/issues/123
   ```

2. **Issue Fetching**
   - Validate URL
   - Fetch issue via GitHub API
   - Extract title, body, labels

3. **Repository Setup**
   - Clone repository locally
   - Create new branch: `ai-fix/issue-123`

4. **Planning Phase**
   - Analyze issue with Gemini
   - Identify bug/feature type
   - Generate search queries
   - Create fix strategy

5. **Search Phase**
   - Index repository with ChromaDB
   - Semantic search for relevant files
   - Keyword search for specific terms
   - Combine and rank results

6. **Coding Phase**
   - Load relevant files
   - Generate code fixes with Gemini
   - Apply changes to files
   - Commit changes

7. **Validation Phase**
   - Build Docker image
   - Run tests in container
   - Parse test results
   - Retry if failed (max 3 times)

8. **Finalization**
   - Push branch to GitHub
   - Create draft Pull Request
   - Add detailed PR description
   - Return PR URL

## 📊 Key Metrics

- **Files:** 40+ source files
- **Lines of Code:** ~3,500 lines
- **Test Coverage:** Basic unit tests
- **Dependencies:** 15 production packages
- **Python Version:** 3.10+
- **License:** MIT

## 🔐 Security

- Environment-based configuration
- No hardcoded secrets
- Draft PRs by default
- Token scope validation
- Docker isolation for tests

## 🚀 Usage Examples

### Basic Fix

```bash
python -m cli.main fix https://github.com/myapp/backend/issues/42
```

### Dry Run

```bash
python -m cli.main fix https://github.com/myapp/backend/issues/42 --dry-run
```

### Skip Tests

```bash
python -m cli.main fix https://github.com/myapp/backend/issues/42 --skip-tests
```

### Verbose Mode

```bash
python -m cli.main fix https://github.com/myapp/backend/issues/42 --verbose
```

## 📈 Roadmap

### Week 1 - MVP ✅
- [x] CLI skeleton
- [x] GitHub integration
- [x] Basic workflow

### Week 2 - Intelligence ⏳
- [ ] Enhanced search ranking
- [ ] Better error recovery
- [ ] Multi-file diff analysis

### Week 3 - Automation ⏳
- [ ] Batch processing
- [ ] Webhook integration
- [ ] Automatic issue detection

### Week 4 - Polish ⏳
- [ ] Web dashboard
- [ ] Analytics and metrics
- [ ] Advanced configuration

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/RepoRepair.git
cd RepoRepair

# Install
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Lint
ruff check .

# Format
black .
```

### Code Quality

- Type hints everywhere
- Comprehensive logging
- Modular architecture
- Error handling
- Docstrings

## 📚 Documentation

- **README.md** - Project overview and architecture
- **USAGE.md** - Detailed usage instructions
- **QUICKSTART.md** - 5-minute setup guide
- **CONTRIBUTING.md** - Contribution guidelines
- **PROJECT_SUMMARY.md** - This document

## 🎓 Learning Resources

### Technologies Used

- **LangGraph** - https://langchain-ai.github.io/langgraph/
- **Gemini API** - https://ai.google.dev/
- **PyGithub** - https://pygithub.readthedocs.io/
- **Typer** - https://typer.tiangolo.com/
- **ChromaDB** - https://docs.trychroma.com/

## 🏆 Success Criteria

✅ User runs command with issue URL  
✅ System fetches and analyzes issue  
✅ System finds relevant code files  
✅ System generates code fix  
✅ System runs tests automatically  
✅ System creates draft Pull Request  
✅ Process completes end-to-end  

## 💡 Key Design Decisions

1. **Python** - Best ecosystem for AI/LLM tooling
2. **LangGraph** - Robust multi-agent orchestration
3. **Gemini** - High quality, cost-effective LLM
4. **Draft PRs** - Safety first, always require review
5. **Docker Tests** - Isolated, reproducible test execution
6. **Hybrid Search** - Combines semantic and keyword search
7. **CLI First** - Simple, scriptable interface

## 🌟 Highlights

- **Production-grade** - Proper error handling, logging, tests
- **Safe by design** - Draft PRs, never auto-merge
- **Intelligent search** - RAG + grep hybrid approach
- **Fully automated** - One command, complete workflow
- **Extensible** - Modular architecture, easy to extend
- **Well documented** - Comprehensive guides and examples

## 📞 Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Documentation:** README.md, USAGE.md
- **Examples:** QUICKSTART.md

---

**Built with ❤️ using Python, LangGraph, and Gemini AI**

Last Updated: May 4, 2026
