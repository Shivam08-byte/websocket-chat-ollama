# GitHub Repository Setup Guide

## 🔴 IMPORTANT SECURITY NOTICE
**You shared your Personal Access Token (PAT) in the chat!**

Please immediately:
1. Go to https://github.com/settings/tokens
2. Find and revoke the token: `github_pat_11AQLOTLQ0e5kb...`
3. Generate a new token when needed

---

## Repository Setup Instructions

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name**: `websocket-chat-ollama`
   - **Description**: `Real-time WebSocket chat with AI using FastAPI, Ollama, and multiple LLM models`
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

### Step 2: Push Your Code

After creating the repository, run these commands:

```bash
cd /Users/shivam/Desktop/workspace/poc/websockets

# Add the remote repository (replace with your actual repo URL)
git remote add origin https://github.com/Shivam08-byte/websocket-chat-ollama.git

# Push to GitHub
git push -u origin main
```

You'll be prompted for credentials:
- **Username**: Shivam08-byte
- **Password**: Use your Personal Access Token (generate a new one!)

### Step 3: Generate New Personal Access Token

1. Go to https://github.com/settings/tokens/new
2. Give it a name: "WebSocket Chat Repo"
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
4. Click "Generate token"
5. **Copy the token immediately** (you won't see it again)

### Step 4: Push Using Token

```bash
# When prompted for password, paste your NEW token
git push -u origin main
```

**Alternative: Using GitHub CLI**

If you have GitHub CLI installed:
```bash
gh auth login
gh repo create websocket-chat-ollama --public --source=. --remote=origin
git push -u origin main
```

---

## What's Already Done ✅

- ✅ Git repository initialized
- ✅ All files added and committed
- ✅ Branch renamed to `main`
- ✅ `.gitignore` configured (excludes .env, __pycache__, etc.)
- ✅ Initial commit created with 19 files

## What Needs to Be Done

- [ ] Create repository on GitHub (manually at github.com/new)
- [ ] Add remote origin
- [ ] Push to GitHub
- [ ] (Optional) Add topics/tags to your repo

---

## Current Git Status

```bash
# Check status
git status

# View commit history
git log --oneline

# View remote
git remote -v
```

---

## Recommended Repository Settings (After Push)

### Topics to Add:
- `websocket`
- `fastapi`
- `ollama`
- `llm`
- `ai-chat`
- `docker`
- `python`
- `real-time-chat`
- `gemma`
- `phi3`

### Create GitHub Pages (Optional)
Enable GitHub Pages from repository settings to host documentation.

---

## Repository Structure Preview

Once pushed, your repository will contain:

```
websocket-chat-ollama/
├── 📄 README.md (with architecture diagram)
├── 📄 SETUP.md (complete setup guide)
├── 📄 PROJECT_SUMMARY.md (project details)
├── 📄 QUICK_REFERENCE.md (commands cheat sheet)
├── 📄 MODEL_SELECTION.md (model features)
├── 🐳 docker-compose.yml
├── 🐳 Dockerfile
├── 🐍 app.py
├── 📦 requirements.txt
├── ⚙️ .env.example
├── 🚫 .gitignore
├── 🚫 .dockerignore
├── 🔧 verify.sh
├── 🔧 pull-all-models.sh
├── 🔧 pull-model.sh
└── 📁 static/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## After Pushing, Add These Files (Optional)

### LICENSE
Add an open-source license (MIT, Apache 2.0, etc.)

### CONTRIBUTING.md
Guidelines for contributors

### .github/workflows/
Add GitHub Actions for CI/CD

---

## Need Help?

If you encounter issues:
1. Check git status: `git status`
2. Check remote: `git remote -v`
3. Check logs: `git log --oneline`
4. Force push (if needed): `git push -f origin main`

---

**Remember to revoke the old token immediately!**
