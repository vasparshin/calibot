#!/bin/bash

# CaliBOT GitHub Push Script
# Automatically commits changes, pushes to GitHub, and updates release status

set -e  # Exit on any error

PROJECT_ROOT="/workspaces/calibot"
CHANGELOG_FILE="$PROJECT_ROOT/CHANGELOG.md"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"

echo "🚀 CaliBOT GitHub Push Script"
echo "=============================="

# Change to project directory
cd "$PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  No changes to commit"
    echo "✅ Repository is up to date"
    exit 0
fi

# Extract current version from pyproject.toml
CURRENT_VERSION=$(grep -E '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/')
if [ -z "$CURRENT_VERSION" ]; then
    echo "❌ Error: Could not extract version from pyproject.toml"
    exit 1
fi

echo "📋 Current version: $CURRENT_VERSION"

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
    echo "⚠️  No unreleased changes found in CHANGELOG.md"
    COMMIT_MESSAGE="chore: update codebase - version $CURRENT_VERSION"
else
    echo "📝 Latest changes extracted from CHANGELOG.md:"
    echo "$LATEST_CHANGES" | head -5
    echo "..."
    
    # Create commit message from changelog
    COMMIT_MESSAGE="feat: release v$CURRENT_VERSION

$(echo "$LATEST_CHANGES" | head -10)"
fi

echo ""
echo "📤 Preparing to commit and push..."
echo "Commit message preview:"
echo "----------------------"
echo "$COMMIT_MESSAGE" | head -5
echo "----------------------"

# Ask for confirmation
read -p "Continue with commit and push? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user"
    exit 1
fi

# Stage all changes
echo "📦 Staging changes..."
git add .

# Check if there are staged changes
if [ -z "$(git diff --cached --name-only)" ]; then
    echo "ℹ️  No staged changes to commit"
    exit 0
fi

# Show what will be committed
echo "📋 Files to be committed:"
git diff --cached --name-only | sed 's/^/  - /'

# Commit changes
echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

# Push to remote
echo "🌐 Pushing to GitHub..."
if git push origin main; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    
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
            
            echo "📝 Updated CHANGELOG.md release status"
            
            # Commit the changelog update
            git add "$CHANGELOG_FILE"
            git commit -m "docs: update changelog release status for v$CURRENT_VERSION"
            git push origin main
            
            echo "✅ Changelog release status updated and pushed"
        else
            echo "ℹ️  No [Unreleased] section found to update"
        fi
    }
    
    update_changelog_status
    
    echo ""
    echo "🎉 All done! Changes pushed successfully."
    echo "📊 Repository status:"
    echo "   - Version: $CURRENT_VERSION"
    echo "   - Branch: $(git branch --show-current)"
    echo "   - Latest commit: $(git log -1 --pretty=format:'%h - %s')"
    echo "   - Remote: $(git remote get-url origin)"
    
else
    echo "❌ Failed to push to GitHub"
    echo "Please check your network connection and GitHub authentication"
    exit 1
fi
