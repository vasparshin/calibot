# CaliBOT Scripts

This folder contains automation scripts for the CaliBOT project.

## Available Scripts

### 🚀 push_to_github.sh
**Main GitHub push automation script**

Features:
- Automatically extracts latest changes from `CHANGELOG.md` 
- Creates meaningful commit messages from changelog entries
- Commits all staged changes
- Pushes to GitHub main branch
- Updates CHANGELOG.md release status on successful push
- Adds new [Unreleased] section for future changes

Usage:
```bash
./scripts/push_to_github.sh
```

The script will:
1. Check for uncommitted changes
2. Extract current version from `pyproject.toml`
3. Extract latest changes from `[Unreleased]` section in `CHANGELOG.md`
4. Show preview and ask for confirmation
5. Commit and push changes
6. Update changelog release status

### ⚡ quick_push.sh
**Simple wrapper for quick commits**

Usage:
```bash
# Use automated changelog extraction
./scripts/quick_push.sh

# Use custom commit message
./scripts/quick_push.sh "fix: custom commit message"
```

### 📁 organize_files.sh
**File organization automation**

Moves test files and scripts to their proper directories.

Usage:
```bash
./scripts/organize_files.sh
```

## Prerequisites

- Git repository initialized
- GitHub remote configured
- Proper permissions for push to main branch
- Valid `CHANGELOG.md` with `[Unreleased]` sections
- Version specified in `pyproject.toml`

## Workflow Integration

These scripts are designed to work with:
- **Semantic versioning** in `pyproject.toml`
- **Keep a Changelog** format in `CHANGELOG.md`
- **Professional development workflow** with proper documentation

## Examples

### Standard Release Process
```bash
# 1. Make code changes
# 2. Update CHANGELOG.md [Unreleased] section  
# 3. Run push script
./scripts/push_to_github.sh
```

### Quick Fix
```bash
./scripts/quick_push.sh "fix: resolve minor bug in validation"
```

### Check Script Status
```bash
ls -la scripts/
# All scripts should be executable (x permission)
```

## Notes

- Scripts include error handling and confirmation prompts
- Changelog status is automatically updated on successful push
- Scripts work from any directory within the project
- Safe to run multiple times (idempotent operations)
