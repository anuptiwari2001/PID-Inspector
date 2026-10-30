# GitHub Setup Instructions

This document guides you through pushing your PID-Inspector project to GitHub.

## Prerequisites

You need to install Git on your system. Follow the appropriate steps below:

### Windows Installation

1. **Download Git for Windows**
   - Go to https://git-scm.com/download/win
   - Download the latest installer (64-bit recommended)
   - Run the installer and follow the setup wizard
   - Use the default settings (recommended)

2. **Verify Installation**
   - Close and reopen PowerShell
   - Run: `git --version`
   - Should show: `git version X.XX.X.windows.1` or similar

## Setup Steps (After Git Installation)

Follow these steps in PowerShell from your project root directory:

### 1. Initialize Git Repository
```powershell
cd "C:\Users\Anupam Tiwari\Documents\DEXPI P&ID Inspector"
git init
```

### 2. Configure Git (First time only)
```powershell
git config --global user.name "Anupam Tiwari"
git config --global user.email "your.email@example.com"
```

### 3. Add All Files
```powershell
git add .
```

### 4. Create Initial Commit
```powershell
git commit -m "Initial commit: PID-Inspector project setup"
```

### 5. Add Remote Repository
```powershell
git remote add origin https://github.com/anuptiwari2001/PID-Inspector.git
```

### 6. Rename Branch (if needed)
```powershell
git branch -M main
```

### 7. Push to GitHub
```powershell
git push -u origin main
```

## Add Collaborator on GitHub

1. Go to https://github.com/anuptiwari2001/PID-Inspector
2. Click **Settings** (in the repo navigation)
3. Click **Collaborators** (in the left sidebar)
4. Click **Add people**
5. Enter username: `Poojat2003`
6. Select them from the dropdown
7. Choose role: **Write** (allows pushing) or **Maintain** (more permissions)
8. Click **Add**

The collaborator will receive an invitation email to accept.

## What Gets Pushed

✅ **Included:**
- All source code (src/, server/, migrations/, scripts/)
- Configuration files (package.json, tsconfig.json, vite.config.ts, etc.)
- Documentation (README.md, docs/)
- Assets (public/, attachments/)

❌ **Excluded (in .gitignore):**
- node_modules/ (will be reinstalled via npm install)
- .env files (keep secrets local)
- IDE files (.vs/, .vscode/ config)
- Build outputs
- OS files (.DS_Store, Thumbs.db)

## After First Push

Your collaborator can clone the repository:
```powershell
git clone https://github.com/anuptiwari2001/PID-Inspector.git
cd PID-Inspector
npm install
```

Then follow the setup in README.md to run the project locally.

## Troubleshooting

**"fatal: could not read Username"**
- Make sure you have HTTPS or SSH credentials set up
- Or use: `git config --global credential.helper wincred`

**"fatal: The remote origin already exists"**
- Remove it: `git remote remove origin`
- Then re-add: `git remote add origin https://github.com/anuptiwari2001/PID-Inspector.git`

**"Your branch is ahead of 'origin/main' by X commits"**
- Try push again: `git push -u origin main`
