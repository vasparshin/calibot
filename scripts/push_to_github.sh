#!/bin/bash

# CaliBOT GitHub Push Script
# Automatically commits changes, pushes to GitHub, and ensures version control accuracy

set -e  # Exit on any error

PROJECT_ROOT="/workspaces/calibot"
CHANGELOG_FILE="$PROJECT_ROOT/CHANGELOG.md"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
INIT_FILE="$PROJECT_ROOT/backend/app/__init__.py"

echo "CaliBOT GitHub Push Script"
echo "==========================="

# Change to project directory
cd "$PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

# Function to extract version from different files
extract_pyproject_version() {
    grep -E '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/' || echo ""
}

extract_init_version() {
    grep -E '^__version__ = ' "$INIT_FILE" | sed 's/__version__ = "\(.*\)"/\1/' || echo ""
}

extract_changelog_version() {
    grep -E '^## \[.*\].*2025-' "$CHANGELOG_FILE" | head -1 | sed 's/## \[\(.*\)\] -.*/\1/' || echo ""
}

# Extract versions from all files
PYPROJECT_VERSION=$(extract_pyproject_version)
INIT_VERSION=$(extract_init_version)
CHANGELOG_VERSION=$(extract_changelog_version)

echo "🔍 Version Control Check:"
echo "   pyproject.toml: $PYPROJECT_VERSION"
echo "   __init__.py: $INIT_VERSION"
echo "   CHANGELOG.md: $CHANGELOG_VERSION"

# Validate version consistency
VERSION_MISMATCH=false
if [ "$PYPROJECT_VERSION" != "$INIT_VERSION" ]; then
    echo "❌ ERROR: Version mismatch between pyproject.toml ($PYPROJECT_VERSION) and __init__.py ($INIT_VERSION)"
    VERSION_MISMATCH=true
fi

if [ "$PYPROJECT_VERSION" != "$CHANGELOG_VERSION" ]; then
    echo "❌ ERROR: Version mismatch between pyproject.toml ($PYPROJECT_VERSION) and CHANGELOG.md ($CHANGELOG_VERSION)"
    VERSION_MISMATCH=true
fi

if [ "$VERSION_MISMATCH" = true ]; then
    echo ""
    echo "🛠️  FIXING VERSION MISMATCHES..."
    
    # Use pyproject.toml as the source of truth
    CURRENT_VERSION="$PYPROJECT_VERSION"
    
    if [ -z "$CURRENT_VERSION" ]; then
        echo "ERROR: Could not extract version from pyproject.toml"
        exit 1
    fi
    
    # Fix __init__.py version
    if [ "$INIT_VERSION" != "$CURRENT_VERSION" ]; then
        echo "   Updating __init__.py: $INIT_VERSION → $CURRENT_VERSION"
        sed -i "s/__version__ = \".*\"/__version__ = \"$CURRENT_VERSION\"/" "$INIT_FILE"
    fi
    
    # Fix CHANGELOG.md version if needed
    if [ "$CHANGELOG_VERSION" != "$CURRENT_VERSION" ]; then
        echo "   Updating CHANGELOG.md: $CHANGELOG_VERSION → $CURRENT_VERSION"
        CURRENT_DATE=$(date +%Y-%m-%d)
        sed -i "s/^## \[.*\] - $CURRENT_DATE/## [$CURRENT_VERSION] - $CURRENT_DATE/" "$CHANGELOG_FILE"
    fi
    
    echo "✅ Version synchronization complete"
else
    CURRENT_VERSION="$PYPROJECT_VERSION"
    echo "✅ All versions are synchronized: $CURRENT_VERSION"
fi

echo "Current version: $CURRENT_VERSION"

# Check for uncommitted changes after version sync
if [ -z "$(git status --porcelain)" ]; then
    echo "📡 Checking remote status..."
    
    # Check if local is ahead of remote
    LOCAL_COMMITS=$(git rev-list --count HEAD ^origin/main 2>/dev/null || echo "0")
    
    if [ "$LOCAL_COMMITS" -gt 0 ]; then
        echo "⚠️  Local repository is $LOCAL_COMMITS commit(s) ahead of remote"
        echo "📤 Pushing existing commits to GitHub..."
        
        if git push origin main; then
            echo "✅ Successfully pushed existing commits to GitHub"
            echo "🚀 This should trigger Render deployment to version $CURRENT_VERSION"
            exit 0
        else
            echo "❌ Failed to push to GitHub"
            exit 1
        fi
    else
        echo "✅ Repository is up to date with remote"
        echo "ℹ️  No changes to commit or push"
        exit 0
    fi
fi

# Extract the latest changelog entry (everything under [Unreleased] until next version)
extract_latest_changelog() {
    local changelog_content=""
    local in_unreleased=false
    local line_count=0
    
    while IFS= read -r line; do
        line_count=$((line_count + 1))
        
        # Start capturing after [Unreleased]
        if [[ "$line" =~ ^\#\#\ \[Unreleased\] ]]; then
            in_unreleased=true
            continue
        fi
        
        # Stop at next version header
        if [[ "$in_unreleased" == true && "$line" =~ ^\#\#\ \[.*\] ]]; then
            break
        fi
        
        # Capture content if we're in unreleased section
        if [[ "$in_unreleased" == true ]]; then
            changelog_content+="$line"$'\n'
        fi
        
        # Safety limit
        if [ $line_count -gt 200 ]; then
            break
        fi
    done < "$CHANGELOG_FILE"
    
    # Clean up the changelog content
    changelog_content=$(echo "$changelog_content" | sed '/^$/d' | head -20)
    echo "$changelog_content"
}

# Get the latest changelog for commit message
LATEST_CHANGES=$(extract_latest_changelog)

if [ -z "$LATEST_CHANGES" ]; then
    echo "WARNING: No unreleased changes found in CHANGELOG.md"
    COMMIT_MESSAGE="chore: update codebase - version $CURRENT_VERSION"
else
    echo "INFO: Latest changes extracted from CHANGELOG.md:"
    echo "$LATEST_CHANGES" | head -5
    echo "..."
    
    # Create commit message from changelog
    COMMIT_MESSAGE="feat: release v$CURRENT_VERSION

$(echo "$LATEST_CHANGES" | head -10)"
fi

echo ""
echo "INFO: Preparing to commit and push..."
echo "Commit message preview:"
echo "----------------------"
echo "$COMMIT_MESSAGE" | head -5
echo "----------------------"

# Ask for confirmation
read -p "Continue with commit and push? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "ERROR: Aborted by user"
    exit 1
fi

# Stage all changes
echo "📦 Staging changes..."
git add .

# Check if there are staged changes
if [ -z "$(git diff --cached --name-only)" ]; then
    echo "INFO: No staged changes to commit"
    exit 0
fi

# Show what will be committed
echo "INFO: Files to be committed:"
git diff --cached --name-only | sed 's/^/  - /'

# Commit changes
echo "INFO: Committing changes..."
git commit -m "$COMMIT_MESSAGE"

# Push to remote
echo "INFO: Pushing to GitHub..."
if git push origin main; then
    echo ""
    echo "SUCCESS: Successfully pushed to GitHub!"
    
    # Update CHANGELOG.md to mark as released
    update_changelog_status() {
        local current_date=$(date +%Y-%m-%d)
        
        # Replace [Unreleased] with [version] - date
        if grep -q "## \[Unreleased\]" "$CHANGELOG_FILE"; then
            sed -i "s/## \[Unreleased\]/## [$CURRENT_VERSION] - $current_date/" "$CHANGELOG_FILE"
            
            # Add a new [Unreleased] section at the top
            sed -i "/^## \[$CURRENT_VERSION\] - $current_date/i\\
## [Unreleased]\\
\\
" "$CHANGELOG_FILE"
            
            echo "INFO: Updated CHANGELOG.md release status"
            
            # Commit the changelog update
            git add "$CHANGELOG_FILE"
            git commit -m "docs: update changelog release status for v$CURRENT_VERSION"
            git push origin main
            
            echo "SUCCESS: Changelog release status updated and pushed"
        else
            echo "INFO: No [Unreleased] section found to update"
        fi
    }
    
    update_changelog_status
    
    echo ""
    echo "SUCCESS: All done! Changes pushed successfully."
    echo "INFO: Repository status:"
    echo "   - Version: $CURRENT_VERSION"
    echo "   - Branch: $(git branch --show-current)"
    echo "   - Latest commit: $(git log -1 --pretty=format:'%h - %s')"
    echo "   - Remote: $(git remote get-url origin)"
    
else
    echo "ERROR: Failed to push to GitHub"
    echo "Please check your network connection and GitHub authentication"
    exit 1
fi
