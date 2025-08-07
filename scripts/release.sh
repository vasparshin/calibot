#!/bin/bash

# CaliBOT Release Script
# Automates version bumping, changelog management, and GitHub releases
# Usage: ./scripts/release.sh [patch|minor|major]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/workspaces/calibot"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
CHANGELOG_FILE="$PROJECT_ROOT/CHANGELOG.md"
INIT_FILE="$PROJECT_ROOT/backend/app/__init__.py"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get current version from pyproject.toml
get_current_version() {
    grep '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/'
}

# Function to increment version
increment_version() {
    local version=$1
    local bump_type=$2
    
    # Split version into components
    IFS='.' read -ra VERSION_PARTS <<< "$version"
    major=${VERSION_PARTS[0]}
    minor=${VERSION_PARTS[1]}
    patch=${VERSION_PARTS[2]}
    
    case $bump_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid bump type: $bump_type. Use patch, minor, or major."
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Function to update version in pyproject.toml
update_pyproject_version() {
    local new_version=$1
    sed -i "s/^version = .*/version = \"$new_version\"/" "$PYPROJECT_FILE"
}

# Function to update version in __init__.py
update_init_version() {
    local new_version=$1
    sed -i "s/__version__ = .*/__version__ = \"$new_version\"/" "$INIT_FILE"
}

# Function to update changelog
update_changelog() {
    local new_version=$1
    local release_date=$(date +"%Y-%m-%d")
    
    # Create temporary file
    local temp_file=$(mktemp)
    
    # Read changelog and update
    awk -v version="$new_version" -v date="$release_date" '
    /^## \[Unreleased\]/ {
        print "## [Unreleased]"
        print ""
        print "## [" version "] - " date
        found_unreleased = 1
        next
    }
    found_unreleased && /^## \[/ {
        print $0
        found_unreleased = 0
        next
    }
    { print }
    ' "$CHANGELOG_FILE" > "$temp_file"
    
    mv "$temp_file" "$CHANGELOG_FILE"
}

# Function to extract changelog for this version
extract_version_changelog() {
    local version=$1
    local temp_file=$(mktemp)
    
    awk -v version="$version" '
    /^## \['"$version"'\]/ { in_section = 1; next }
    /^## \[/ && in_section { exit }
    in_section && NF > 0 { print }
    ' "$CHANGELOG_FILE" > "$temp_file"
    
    echo "$temp_file"
}

# Function to run tests
run_tests() {
    print_status "Running comprehensive test suite..."
    cd "$PROJECT_ROOT"
    
    if python tests/test_all_fixes.py > /dev/null 2>&1; then
        print_success "All tests passed!"
        return 0
    else
        print_error "Tests failed! Please fix issues before releasing."
        return 1
    fi
}

# Function to check git status
check_git_status() {
    if ! git diff --quiet; then
        print_warning "You have uncommitted changes. Please commit or stash them first."
        git status --short
        return 1
    fi
    
    if ! git diff --cached --quiet; then
        print_warning "You have staged changes. Please commit them first."
        git status --short
        return 1
    fi
    
    return 0
}

# Function to create GitHub release
create_github_release() {
    local version=$1
    local changelog_file=$2
    
    print_status "Creating GitHub release v$version..."
    
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found. Please install it to create releases automatically."
        print_status "You can manually create a release at: https://github.com/vasparshin/calibot/releases/new"
        print_status "Tag: v$version"
        print_status "Release notes from: $changelog_file"
        return 1
    fi
    
    # Create release with changelog
    if gh release create "v$version" \
        --title "CaliBOT v$version" \
        --notes-file "$changelog_file" \
        --repo vasparshin/calibot; then
        print_success "GitHub release v$version created successfully!"
        return 0
    else
        print_error "Failed to create GitHub release"
        return 1
    fi
}

# Main script
main() {
    print_status "CaliBOT Release Script Starting..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PYPROJECT_FILE" ]]; then
        print_error "pyproject.toml not found. Please run from project root."
        exit 1
    fi
    
    # Get bump type (default to patch)
    local bump_type=${1:-patch}
    
    # Validate bump type
    if [[ ! "$bump_type" =~ ^(patch|minor|major)$ ]]; then
        print_error "Invalid bump type: $bump_type"
        echo "Usage: $0 [patch|minor|major]"
        exit 1
    fi
    
    # Check git status
    if ! check_git_status; then
        exit 1
    fi
    
    # Run tests
    if ! run_tests; then
        exit 1
    fi
    
    # Get current version
    local current_version=$(get_current_version)
    print_status "Current version: $current_version"
    
    # Calculate new version
    local new_version=$(increment_version "$current_version" "$bump_type")
    print_status "New version: $new_version (${bump_type} bump)"
    
    # Confirm with user
    echo -n "Proceed with release v$new_version? [y/N] "
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_status "Release cancelled."
        exit 0
    fi
    
    # Update version files
    print_status "Updating version files..."
    update_pyproject_version "$new_version"
    update_init_version "$new_version"
    update_changelog "$new_version"
    
    print_success "Version files updated to $new_version"
    
    # Extract changelog for this version
    local changelog_temp_file=$(extract_version_changelog "$new_version")
    
    # Commit changes
    print_status "Committing version bump..."
    git add "$PYPROJECT_FILE" "$INIT_FILE" "$CHANGELOG_FILE"
    git commit -m "chore: bump version to $new_version"
    
    # Create git tag
    print_status "Creating git tag v$new_version..."
    git tag "v$new_version"
    
    # Push to remote
    print_status "Pushing to GitHub..."
    git push origin main
    git push origin "v$new_version"
    
    print_success "Code pushed to GitHub successfully!"
    
    # Create GitHub release
    if create_github_release "$new_version" "$changelog_temp_file"; then
        print_success "Release v$new_version completed successfully!"
        print_status "View release at: https://github.com/vasparshin/calibot/releases/tag/v$new_version"
    else
        print_warning "Code was pushed but GitHub release creation failed."
        print_status "Please create the release manually if needed."
    fi
    
    # Cleanup
    rm -f "$changelog_temp_file"
    
    print_success "CaliBOT v$new_version release process complete!"
}

# Run main function with all arguments
main "$@"
