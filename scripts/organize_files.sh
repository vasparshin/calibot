#!/bin/bash

# Script to organize test files and demo files to the tests folder
# This helps maintain a clean project structure

PROJECT_ROOT="/workspaces/calibot"
TESTS_DIR="$PROJECT_ROOT/tests"

echo "🔍 Checking for misplaced test and demo files..."

# Find test files in the root directory
ROOT_TEST_FILES=$(find "$PROJECT_ROOT" -maxdepth 1 -name "test_*.py" -o -name "*_test.py" -o -name "*demo*.py")

if [ -n "$ROOT_TEST_FILES" ]; then
    echo "📁 Found test/demo files in project root:"
    echo "$ROOT_TEST_FILES"
    echo ""
    echo "INFO: Moving files to tests/ folder..."
    mv $ROOT_TEST_FILES "$TESTS_DIR/"
    echo "SUCCESS: Files moved successfully!"
else
    echo "SUCCESS: No misplaced test/demo files found in project root."
fi

# Find test files in backend directory
BACKEND_TEST_FILES=$(find "$PROJECT_ROOT/backend" -name "test_*.py" -o -name "*_test.py")

if [ -n "$BACKEND_TEST_FILES" ]; then
    echo "📁 Found test files in backend directory:"
    echo "$BACKEND_TEST_FILES"
    echo ""
    echo "INFO: Moving files to tests/ folder..."
    mv $BACKEND_TEST_FILES "$TESTS_DIR/"
    echo "SUCCESS: Files moved successfully!"
else
    echo "SUCCESS: No misplaced test files found in backend directory."
fi

echo ""
echo "INFO: Final structure in tests/ folder:"
ls -la "$TESTS_DIR/" | grep -E "(test_|demo)" | head -10

echo ""
echo "🎯 File organization complete!"
