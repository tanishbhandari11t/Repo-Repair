# 🌐 RepoRepair Web Interface Guide

## 🎉 You Now Have a Web App!

I've created a beautiful web interface for RepoRepair. No more command line needed!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Web Server

**Double-click** `start_web.bat` or run in Command Prompt:

```cmd
cd C:\Users\tanis\Desktop\RepoRepair
start_web.bat
```

### Step 2: Open Your Browser

The server will start and show:
```
============================================
  Web Interface: http://localhost:5000
============================================
```

**Open your browser** and go to: **http://localhost:5000**

### Step 3: Start Fixing Issues!

1. Paste a GitHub issue URL
2. Choose your options (Dry Run recommended for first test)
3. Click "Start Fixing Issue"
4. Watch the magic happen in real-time! ✨

---

## 📸 What the Web Interface Looks Like

### Main Page
- **Header:** Big RepoRepair logo
- **Input Form:** Paste your GitHub issue URL
- **Options:** 
  - ✅ Dry Run (recommended - doesn't create PR)
  - ✅ Skip Tests (faster for testing)
- **Recent Jobs:** See your past runs

### Progress Page
- **Real-time updates** as RepoRepair works
- **Progress bar** showing status
- **Issue details** displayed
- **Live progress messages**

### Results Page
- **✅ Success:** Shows PR URL, branch, files changed
- **❌ Error:** Shows what went wrong
- **Recent jobs list** updated automatically

---

## 🎯 Create Your First Test Issue

Since you got an error with that repository URL, let's create a proper test issue:

### Option 1: Use a Test Repository (Easiest)

1. **Go to:** https://github.com/new
2. **Create repository:**
   - Name: `test-reporepair`
   - ✅ Public
   - ✅ Add README
   - Click "Create repository"

3. **Add a buggy file:**
   - Click "Add file" → "Create new file"
   - Name: `calculator.py`
   - Content:
     ```python
     def add(a, b):
         """Add two numbers."""
         return a - b  # BUG: This subtracts!
     
     def multiply(a, b):
         """Multiply two numbers."""
         return a + b  # BUG: This adds!
     
     if __name__ == "__main__":
         print("2 + 3 =", add(2, 3))  # Should be 5, will show -1
         print("2 * 3 =", multiply(2, 3))  # Should be 6, will show 5
     ```
   - Commit the file

4. **Create an issue:**
   - Click "Issues" tab → "New issue"
   - **Title:** `Fix calculator functions`
   - **Description:**
     ```
     The calculator has two bugs:
     
     1. The `add` function subtracts instead of adding (a - b should be a + b)
     2. The `multiply` function adds instead of multiplying (a + b should be a * b)
     
     Both functions need to be fixed to work correctly.
     ```
   - Click "Submit new issue"

5. **Copy the issue URL** (looks like):
   ```
   https://github.com/YOUR_USERNAME/test-reporepair/issues/1
   ```

6. **Use in RepoRepair:**
   - Go to http://localhost:5000
   - Paste the URL
   - ✅ Check "Dry Run"
   - ✅ Check "Skip Tests"
   - Click "Start Fixing Issue"

---

## 🎮 Using the Web Interface

### Input Form Options

#### **Dry Run Mode** (Recommended First)
- ✅ **Checked:** Analyzes and generates fix, but DOESN'T create a PR
- ❌ **Unchecked:** Creates an actual draft Pull Request
- **Use for:** Testing, seeing what will happen

#### **Skip Tests**
- ✅ **Checked:** Doesn't run tests (faster, for simple fixes)
- ❌ **Unchecked:** Runs full test suite in Docker
- **Use for:** Simple fixes, or if you don't have Docker running

### Real-Time Progress

You'll see updates like:
```
✓ Fetching issue #1...
✓ Cloning repository...
✓ Running AI analysis...
✓ Found 1 relevant files
✓ Generating code changes...
✓ Complete!
```

### Results

**Success:**
- Shows branch name
- Lists files changed
- Displays PR URL (if not dry run)
- "Fix Another Issue" button

**Error:**
- Shows error message
- Suggests checking logs
- "Fix Another Issue" button

---

## 📊 Features

### ✨ What the Web App Can Do

1. **Real-Time Progress** - See what's happening as it happens
2. **Beautiful UI** - Modern, responsive design
3. **Recent Jobs** - View history of your fixes
4. **Error Handling** - Clear error messages
5. **Safe by Default** - Dry run mode checked by default
6. **No Command Line** - Everything in your browser!

### 🛡️ Safety Features

- ✅ **Dry Run default** - Test without creating PRs
- ✅ **Always draft PRs** - Never auto-merges
- ✅ **URL validation** - Won't accept invalid URLs
- ✅ **Progress tracking** - See exactly what's happening

---

## 🆘 Troubleshooting

### "Server won't start"

**Check:**
1. Virtual environment activated?
2. Flask installed? (`pip install flask flask-cors`)
3. Port 5000 not already in use?

**Fix:**
```cmd
cd C:\Users\tanis\Desktop\RepoRepair
venv\Scripts\activate
pip install flask flask-cors
python web_app.py
```

### "Can't access http://localhost:5000"

**Check:**
1. Server running? Look for "Running on http://..."
2. Try: http://127.0.0.1:5000
3. Firewall blocking?

### "Invalid GitHub issue URL"

**The URL MUST look like:**
```
https://github.com/OWNER/REPO/issues/NUMBER
                                ^^^^^^^^^^^^^^
                                This part is required!
```

**NOT like:**
- ❌ `https://github.com/owner/repo` (missing /issues/NUMBER)
- ❌ `https://github.com/owner/repo/pulls/1` (pulls, not issues)
- ❌ `github.com/owner/repo/issues/1` (missing https://)

### "Job stuck on 'Running'"

**Check:**
1. Look at server console for errors
2. Check `webapp.log` file
3. Refresh the page
4. May need to restart server

---

## 🎯 Example Workflow

### Complete Example: Testing RepoRepair

1. **Start Server:**
   ```cmd
   start_web.bat
   ```

2. **Open Browser:**
   - Go to http://localhost:5000

3. **Create Test Issue:**
   - Follow "Option 1" above to create test repository with bug

4. **Use RepoRepair:**
   - Paste issue URL: `https://github.com/YOU/test-reporepair/issues/1`
   - ✅ Dry Run
   - ✅ Skip Tests
   - Click "Start Fixing Issue"

5. **Watch Progress:**
   - See real-time updates
   - Wait ~1-2 minutes

6. **View Results:**
   - ✅ Success! 
   - See what changes it made
   - Branch created: `ai-fix/issue-1`

7. **Try Real PR (Optional):**
   - Click "Fix Another Issue"
   - Same URL
   - ❌ Uncheck "Dry Run"
   - Click "Start Fixing Issue"
   - Check GitHub for draft PR!

---

## 📁 Web App Files

| File | What It Does |
|------|--------------|
| `web_app.py` | Flask backend server |
| `templates/index.html` | Web page HTML |
| `static/css/style.css` | Beautiful styling |
| `static/js/app.js` | Interactive functionality |
| `start_web.bat` | Easy startup script |
| `webapp.log` | Web app logs |

---

## 🔧 Advanced Usage

### Running on Different Port

Edit `web_app.py` (last line):
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change 5000 to 8080
```

### Accessing from Other Devices

The server binds to `0.0.0.0`, so you can access it from other devices:
```
http://YOUR_COMPUTER_IP:5000
```

Find your IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)

---

## 💡 Tips & Tricks

1. **Always dry run first** - See what will happen
2. **Keep server running** - No need to restart between jobs
3. **Check recent jobs** - See history at bottom of page
4. **Create simple test issues** - Easy to verify AI works
5. **Review all PRs** - Never auto-merge AI code!

---

## 🎉 You're Ready!

**Start your web server:**
```cmd
start_web.bat
```

**Open your browser:**
```
http://localhost:5000
```

**Fix some issues!** 🚀

---

## 📚 More Help

- **CLI Version:** See `TEST_GUIDE.md`
- **Setup Issues:** See `YOUR_SETUP_IS_COMPLETE.md`
- **Advanced Features:** See `USAGE.md`
- **Architecture:** See `README.md`

---

**Have fun with your new web interface!** 🌐✨
