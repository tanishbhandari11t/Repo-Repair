# RepoRepair Quick Start

Get up and running with RepoRepair in 5 minutes!

## 🚀 Installation

### Windows

1. Open PowerShell or Command Prompt in the RepoRepair directory
2. Run the installation script:

```cmd
install.bat
```

### macOS/Linux

1. Open Terminal in the RepoRepair directory
2. Make the install script executable and run it:

```bash
chmod +x install.sh
./install.sh
```

## 🔑 Configuration

1. Edit the `.env` file:

```bash
# Windows
notepad .env

# macOS/Linux
nano .env
```

2. Add your credentials:

```env
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_key_here
```

### Getting Your Tokens

**GitHub Token:**
- Visit: https://github.com/settings/tokens
- Generate new token with `repo`, `workflow` scopes
- Copy and paste into `.env`

**Gemini API Key:**
- Visit: https://ai.google.dev/
- Get API Key
- Copy and paste into `.env`

## ✅ Verify Setup

Activate virtual environment and verify:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Verify configuration
python -m cli.main config
```

You should see: `GitHub Token: ✓ Set` and `Gemini API Key: ✓ Set`

## 🎯 Your First Fix

Try fixing a GitHub issue:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123
```

Or test without creating a PR:

```bash
python -m cli.main fix https://github.com/owner/repo/issues/123 --dry-run
```

## 📚 Next Steps

- Read the [Usage Guide](USAGE.md) for detailed instructions
- Check the [README](README.md) for architecture overview
- See [CONTRIBUTING](CONTRIBUTING.md) to contribute

## 🆘 Common Issues

### "Docker not available"

**Solution:** Install Docker Desktop or skip tests with `--skip-tests`

### "GitHub token invalid"

**Solution:** Check your token in `.env` has correct scopes

### "Module not found"

**Solution:** Make sure virtual environment is activated

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## 🎉 Success!

If you see this output, you're ready:

```
✓ Issue fetched: [Issue Title]
✓ Repository cloned
✓ Generated code changes
✓ Tests passed
✓ Draft PR created: [PR URL]
```

Now go fix some issues! 🔧
