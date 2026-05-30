# Contributing to RepoRepair

Thank you for your interest in contributing to RepoRepair! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/RepoRepair/issues)
2. If not, create a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs from `reporepair.log`

### Suggesting Features

1. Check if the feature has been suggested in [Discussions](https://github.com/yourusername/RepoRepair/discussions)
2. Create a new discussion explaining:
   - The problem you're trying to solve
   - Your proposed solution
   - Any alternatives you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Update documentation if needed
7. Commit with clear message: `git commit -m "Add feature: X"`
8. Push to your fork: `git push origin feature/my-feature`
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/RepoRepair.git
cd RepoRepair

# Add upstream remote
git remote add upstream https://github.com/yourusername/RepoRepair.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use meaningful variable names
- Write docstrings for public functions

### Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .

# Run all checks
black . && ruff check . && mypy .
```

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest for testing
- Mock external services (GitHub, Gemini)

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
RepoRepair/
├── cli/              # CLI interface
├── agents/           # AI agents (planner, searcher, coder, validator)
├── tools/            # External tools (GitHub, Git, Docker, search)
├── indexer/          # Code indexing and search
├── tests/            # Test suite
├── config.py         # Configuration management
└── models.py         # Data models
```

## Component Guidelines

### Adding a New Agent

1. Create file in `agents/` directory
2. Inherit from base agent pattern
3. Implement required methods
4. Add to orchestrator workflow
5. Write tests in `tests/test_agents.py`

Example:

```python
class NewAgent:
    def __init__(self, config):
        self.config = config
    
    def process(self, state: AgentState) -> AgentState:
        # Process state
        return state
```

### Adding a New Tool

1. Create file in `tools/` directory
2. Follow existing tool patterns
3. Handle errors gracefully
4. Add logging
5. Write tests

### Modifying LangGraph Workflow

1. Update `agents/orchestrator.py`
2. Add new nodes/edges as needed
3. Update state model if required
4. Test the complete workflow

## Documentation

- Update README.md for user-facing changes
- Update USAGE.md for new features
- Add docstrings to all public functions
- Include examples in documentation

## Commit Message Guidelines

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes (formatting)
- `chore`: Maintenance tasks

Examples:
```
feat: Add support for GitLab issues
fix: Handle null pointer in file reader
docs: Update installation instructions
test: Add tests for GitHub tool
```

## Release Process

1. Update version in `__init__.py` and `setup.py`
2. Update CHANGELOG.md with changes
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push --tags`
5. GitHub Actions will create release

## Questions?

- Open a discussion on GitHub
- Check existing issues and PRs
- Review USAGE.md for usage questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to RepoRepair! 🎉
