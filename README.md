# RepoRepair 🔧

AI-powered GitHub Issue to Pull Request converter. Automatically analyze issues, generate fixes, run tests, and create draft PRs.

## Features

- 🤖 **Multi-Agent AI System** - Orchestrated workflow with specialized agents
- 🔍 **Intelligent Code Search** - Hybrid RAG + grep for accurate file discovery
- ✅ **Automated Testing** - Docker-based test execution for safety
- 🔄 **Safe PR Creation** - Always creates draft PRs, never auto-merges
- 📊 **Rich CLI Experience** - Beautiful terminal output with progress tracking

## Architecture

```
┌─────────────┐
│   GitHub    │
│   Issue     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Planner   │  ← Analyzes issue, creates strategy
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Searcher   │  ← Finds relevant files in repo
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Coder    │  ← Generates code fix
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validator  │  ← Runs tests, validates changes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Draft PR   │
└─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (for test execution)
- GitHub Personal Access Token
- Gemini API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/RepoRepair.git
cd RepoRepair

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### GitHub Token Setup

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Generate new token (classic) with scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `read:org` (Read org and team membership)
3. Copy token to `.env` as `GITHUB_TOKEN`

### Gemini API Key Setup

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Generate API key
3. Copy to `.env` as `GEMINI_API_KEY`

## Usage

### Basic Command

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123
```

### Options

```bash
# Dry run (no PR creation)
python -m cli.main fix <issue-url> --dry-run

# Verbose logging
python -m cli.main fix <issue-url> --verbose

# Skip tests
python -m cli.main fix <issue-url> --skip-tests

# Custom workspace
python -m cli.main fix <issue-url> --workspace ./custom-workspace
```

## Project Structure

```
RepoRepair/
│
├── cli/
│   └── main.py              # CLI entry point
│
├── agents/
│   ├── planner.py           # Issue analysis & strategy
│   ├── searcher.py          # Code search & discovery
│   ├── coder.py             # Code generation
│   └── validator.py         # Test execution & validation
│
├── tools/
│   ├── github_tool.py       # GitHub API operations
│   ├── git_tool.py          # Git operations
│   ├── search_tool.py       # Code search (RAG + grep)
│   └── docker_tool.py       # Docker test runner
│
├── indexer/
│   └── code_indexer.py      # ChromaDB indexing
│
├── tests/                   # Test suite
├── .env.example            # Environment template
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```

### CI/CD

GitHub Actions workflow automatically runs on push:
- Linting
- Type checking
- Tests

## Safety & Best Practices

- ✅ Always creates **draft** PRs
- ✅ Never auto-merges code
- ✅ Tests run in isolated Docker containers
- ✅ Changes limited to relevant files
- ✅ PR includes AI disclaimer
- ✅ All operations logged

## Limitations

- Maximum diff size: 300 lines
- Requires Docker for test execution
- Works best with repositories that have tests
- English language issues only (for now)

## Roadmap

### Week 1 - MVP ✓
- [x] CLI skeleton
- [x] Fetch issue
- [x] Basic patch generation

### Week 2 - Search & Agent
- [ ] Repo indexing
- [ ] Hybrid search (RAG + grep)
- [ ] Planner agent

### Week 3 - Automation
- [ ] Docker test runner
- [ ] Patch validator
- [ ] Retry loop

### Week 4 - GitHub Automation
- [ ] Branch creation
- [ ] Commit
- [ ] Draft PR creation

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

- 📖 [Documentation](https://github.com/yourusername/RepoRepair/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/RepoRepair/issues)
- 💬 [Discussions](https://github.com/yourusername/RepoRepair/discussions)

---

Built with ❤️ using Python, LangGraph, and Gemini
