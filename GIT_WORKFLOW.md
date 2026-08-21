# Git Workflow - Cyber Tools MCP

## Branch Strategy

```
main (master) ────────────────────────────── STABLE v1.0.0 (FROZEN)
              │
              └─────── develop ─────────────── DEVELOPMENT (ACTIVE)
                        │
                        ├─ feature/add-ml-detection
                        ├─ feature/remote-analysis
                        └─ feature/database-storage
```

---

## 🔒 Main Branch (STABLE v1.0.0)

**Status**: FROZEN - Production Release  
**Protection**: Do not modify directly  
**Purpose**: Always maintain a working version  

### Main Branch Characteristics
- ✅ v1.0.0 tag frozen at commit `6924c8e`
- ✅ All 90+ tools tested and verified
- ✅ Complete documentation
- ✅ Production ready
- ✅ Fallback point if develop breaks

### Access Main
```bash
# Switch to main
git checkout master

# View release commits
git log --oneline

# Verify v1.0.0 tag
git tag -l v1.0.0

# View main branch
git branch -v
```

---

## 🚀 Develop Branch (ACTIVE)

**Status**: ACTIVE - Current Development  
**Protection**: Pull request reviews recommended  
**Purpose**: All new features and improvements  

### Develop Branch Characteristics
- 🚧 New features in progress
- 🧪 Testing and experiments
- 📝 Documentation updates
- 🐛 Bug fixes
- 🎯 Version 1.1.0+ work

### Current Branch Status
```
On branch develop
All features in development go here
```

---

## 📋 Workflow Steps

### 1️⃣ Creating a New Feature

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Stage and commit
git add .
git commit -m "Add your feature description"

# Push feature branch
git push origin feature/your-feature-name
```

### 2️⃣ Committing Changes

```bash
# Check status
git status

# Stage files
git add .
git add specific-file.js

# Commit with descriptive message
git commit -m "Brief description of changes

- Feature detail 1
- Feature detail 2
- Related issue fix"

# Push to remote
git push origin develop
```

### 3️⃣ Merging to Main (Release)

```bash
# Only after thorough testing
git checkout master
git merge develop

# Tag new version
git tag -a v1.1.0 -m "Release v1.1.0"

# Push changes
git push origin master --tags
```

### 4️⃣ Emergency Hotfix (if needed)

```bash
# Create hotfix from main
git checkout master
git checkout -b hotfix/critical-bug

# Make fix
# ... edit files ...

# Commit and merge back
git commit -m "Fix: critical security issue"
git checkout master
git merge hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"

# Also merge to develop
git checkout develop
git merge hotfix/critical-bug

# Push all
git push origin master develop --tags
```

---

## 📊 Branch Comparison

| Aspect | Main (v1.0.0) | Develop |
|--------|---------------|---------|
| **Status** | 🔒 FROZEN | 🚀 ACTIVE |
| **Tools** | 90+ (v1.0.0) | 90+ + new features |
| **Stability** | ✅ Production | 🧪 Testing |
| **Protection** | No direct commits | PR reviews recommended |
| **Purpose** | Stable fallback | Feature development |
| **Tag** | v1.0.0 | Latest development |

---

## 🔄 Branching Model

### For v1.1.0 Development

```bash
# Start develop
git checkout develop

# Create feature branches
git checkout -b feature/v1.1-ml-detection
git checkout -b feature/v1.1-remote-analysis
git checkout -b feature/v1.1-database

# After features tested and working
git merge feature/v1.1-ml-detection
git merge feature/v1.1-remote-analysis
git merge feature/v1.1-database

# Prepare release
git checkout master
git merge develop
git tag -a v1.1.0 -m "Release v1.1.0"
```

---

## 📝 Commit Message Guide

### Format
```
Type: Brief description (50 chars max)

Detailed explanation if needed:
- What changed
- Why it changed
- Impact of change

Fixes #123
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **refactor**: Code refactoring
- **test**: Test additions
- **chore**: Maintenance

### Examples
```bash
# Feature
git commit -m "feat: Add ML-based anomaly detection

- Implement neural network model
- Add training dataset
- Integrate with hunting tools"

# Bug fix
git commit -m "fix: Handle missing event logs gracefully

- Add null check for event queries
- Return empty list on error
- Log warning message"

# Documentation
git commit -m "docs: Update threat hunting guide

- Add new hunting examples
- Document IOC detection
- Update tool parameters"
```

---

## 🏷️ Tagging Strategy

### Version Tags
```bash
# Format: v[MAJOR].[MINOR].[PATCH]

v1.0.0  # Initial release
v1.0.1  # Hotfix
v1.1.0  # Minor update
v2.0.0  # Major release
```

### Creating Tags
```bash
# Annotated tag (recommended)
git tag -a v1.1.0 -m "Release v1.1.0 - New features"

# List tags
git tag -l

# View tag details
git show v1.0.0

# Delete tag if needed
git tag -d v1.0.0
```

---

## 📊 Current Status

### Main Branch (v1.0.0)
```
✅ Frozen at commit: 6924c8e
✅ Tag: v1.0.0
✅ Status: Production Ready
✅ Tools: 90+
✅ Last update: 2026-08-21
```

### Develop Branch
```
🚀 Active development
📝 Ready for new features
🔗 Based on: v1.0.0
⚡ Next version: v1.1.0
```

---

## 🔐 Protection Rules

### Main Branch Protection
- [x] Require pull request review
- [x] Require code owners review
- [x] Require branches up to date
- [x] Require status checks to pass
- [x] Dismiss stale pull requests
- [x] Restrict who can push to matching branches

### Develop Branch Guidelines
- [x] Use feature branches for new work
- [x] Create pull requests for review
- [x] Require passing tests
- [x] Keep up to date with main
- [x] Squash commits before merge (optional)

---

## 💡 Best Practices

### ✅ DO
- Create feature branches from develop
- Write descriptive commit messages
- Test thoroughly before merging
- Keep branches up to date
- Use pull requests for review
- Tag releases in main
- Document changes

### ❌ DON'T
- Commit directly to main
- Skip testing before merge
- Force push to shared branches
- Mix multiple features in one commit
- Use vague commit messages
- Delete production tags
- Ignore merge conflicts

---

## 🚨 Rollback Procedure

If develop breaks and main is needed:

```bash
# Switch to main (v1.0.0)
git checkout master

# Create hotfix branch
git checkout -b hotfix/emergency

# Make fix
# ... edit files ...

# Test thoroughly
npm install
node server.js

# Merge back to main
git commit -m "Hotfix: Fix critical issue"
git checkout master
git merge hotfix/emergency

# Tag hotfix
git tag -a v1.0.1 -m "Hotfix v1.0.1"

# Also merge to develop
git checkout develop
git merge hotfix/emergency

# Clean up
git branch -d hotfix/emergency
```

---

## 📚 Useful Commands

### View branches
```bash
git branch           # Local branches
git branch -a        # All branches (local + remote)
git branch -v        # Verbose with commits
```

### View history
```bash
git log --oneline                    # Simple log
git log --graph --oneline --decorate # Visual graph
git log --author="name"              # Filter by author
git log --since="2 weeks ago"        # Filter by date
```

### Switch branches
```bash
git checkout develop     # Switch to develop
git checkout -b feature  # Create and switch to new branch
git checkout master      # Switch to main
```

### Merge strategies
```bash
git merge develop                    # Create merge commit
git merge --no-ff develop           # Force merge commit
git merge --squash develop          # Squash commits
git rebase develop                  # Rebase (rewrite history)
```

### Stash changes
```bash
git stash              # Stash current changes
git stash list         # List stashed changes
git stash pop          # Apply and remove stashed changes
git stash drop         # Delete stashed changes
```

---

## 🎯 Release Checklist

Before releasing new version:

- [ ] All features tested
- [ ] Documentation updated
- [ ] RELEASE_NOTES created
- [ ] VERSION.txt updated
- [ ] Tests passing
- [ ] No breaking changes (or documented)
- [ ] Performance verified
- [ ] Security review complete
- [ ] Create pull request to main
- [ ] Merge to main
- [ ] Tag new version
- [ ] Update release page

---

## 📞 Help & Support

### Undo last commit
```bash
git reset --soft HEAD~1  # Undo commit, keep changes
git reset --hard HEAD~1  # Undo commit, discard changes
```

### Fix commit message
```bash
git commit --amend -m "New message"
```

### Discard changes
```bash
git restore filename         # Discard changes in file
git restore .               # Discard all changes
git clean -fd               # Remove untracked files
```

### Resolve conflicts
```bash
# After merge conflict
git status              # Show conflicts
# Edit conflicted files
git add resolved-file
git commit -m "Resolve merge conflict"
```

---

**Git Workflow v1.0 | Status: ACTIVE**
Last Updated: 2026-08-21
