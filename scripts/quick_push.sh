#!/bin/bash

# Quick Push Script - Simple wrapper for the full push script
# Usage: ./quick_push.sh [optional commit message]

PROJECT_ROOT="/workspaces/calibot"
PUSH_SCRIPT="$PROJECT_ROOT/scripts/push_to_github.sh"

echo "🚀 CaliBOT Quick Push"
echo "===================="

# Check if custom commit message is provided
if [ ! -z "$1" ]; then
    echo "📝 Using custom commit message: $1"
    cd "$PROJECT_ROOT"
    git add .
    git commit -m "$1"
    git push origin main
    echo "✅ Quick push completed!"
else
    echo "📋 Using automated changelog extraction..."
    exec "$PUSH_SCRIPT"
fi
