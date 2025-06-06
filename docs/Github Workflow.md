# Git Workflow Guide: Linux Server to Local Machine

This document provides step-by-step instructions for maintaining your code using Git between your Linux server and local machine.

## Linux Server Workflow

### 1. Making Changes on the Linux Server

When you've made changes to your code on the Linux server that you want to push to GitHub:

```bash
# Navigate to your project directory (if not already there)
cd /root/api

# Check which files have been modified
git status

# Add all changed files to staging
git add .

# Alternatively, add specific files
# git add filename1 filename2

# Commit your changes with a descriptive message
git commit -m "Brief description of your changes"

# Push the changes to GitHub
git push origin main
```

### 2. Updating from GitHub to Linux Server

If changes have been made to the GitHub repository from another source (e.g., your local machine), and you want to update the Linux server:

```bash
# Navigate to your project directory
cd /root/api

# Pull the latest changes
git pull origin main
```

## Local Machine Workflow

### 1. Downloading Changes from GitHub to Local Machine

After pushing changes from the Linux server to GitHub, you can download them to your local machine:

```bash
# Navigate to your project directory
cd /Users/davidpepper/Dropbox/NGR/Partners/Ben Angel/Toronto/Data/Database/api-project

# Pull the latest changes
git pull origin main
```

### 2. Making Changes on Local Machine and Uploading to GitHub

If you make changes on your local machine that you want to push to GitHub:

```bash
# Add changes to staging
git add .

# Commit changes
git commit -m "Description of local changes"

# Push to GitHub
git push origin main
```

## Common Git Commands Reference

### Basic Commands
- `git status`: Check the status of your working directory
- `git log`: View commit history
- `git diff`: See the differences between working directory and last commit

### Managing Changes
- `git add .`: Stage all changed files
- `git add <filename>`: Stage a specific file
- `git commit -m "message"`: Commit staged changes
- `git push origin main`: Push to GitHub
- `git pull origin main`: Pull from GitHub

### Branch Management
- `git branch`: List branches
- `git checkout <branch>`: Switch to a branch
- `git checkout -b <new-branch>`: Create and switch to a new branch
- `git merge <branch>`: Merge another branch into current branch

### Undoing Things
- `git restore <file>`: Discard changes in working directory
- `git restore --staged <file>`: Unstage a file
- `git reset HEAD~1`: Undo the last commit (keeping changes)
- `git reset --hard HEAD~1`: Undo the last commit (discarding changes)

## Handling Merge Conflicts

If Git cannot automatically merge changes, you'll encounter merge conflicts. Here's how to resolve them:

1. Git will show which files have conflicts:
   ```
   CONFLICT (content): Merge conflict in filename.py
   ```

2. Open the conflicted files and look for conflict markers:
   ```
   <<<<<<< HEAD
   Your local changes
   =======
   Changes from the remote repository
   >>>>>>> branch-name
   ```

3. Edit the file to resolve the conflict (remove the markers and keep the code you want)

4. After editing, stage the resolved files:
   ```bash
   git add filename.py
   ```

5. Complete the merge:
   ```bash
   git commit -m "Resolve merge conflicts"
   ```

## Best Practices

1. **Pull Before Push**: Always pull the latest changes before pushing to avoid conflicts
2. **Commit Often**: Make small, frequent commits with clear messages
3. **Use Branches**: For major features, create a separate branch
4. **Backup Important Work**: Before complex operations, consider backing up
5. **Review Changes**: Use `git status` and `git diff` to review changes before committing

## Troubleshooting

### Push Rejected
```
! [rejected] main -> main (fetch first)
```
Solution: Pull first, then push
```bash
git pull origin main
git push origin main
```

### Merge Conflicts
Solution: Resolve conflicts as described above

### Accidental Commits
Solution: Undo last commit
```bash
git reset HEAD~1
```

### Changes Not Showing Up
Solution: Check if you're in the right directory and branch
```bash
pwd
git branch
```

## Quick Reference

### Linux Server to GitHub to Local Machine
1. On Linux: `git add .` → `git commit -m "message"` → `git push origin main`
2. On Local: `git pull origin main`

### Local Machine to GitHub to Linux Server
1. On Local: `git add .` → `git commit -m "message"` → `git push origin main`
2. On Linux: `git pull origin main`