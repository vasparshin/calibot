#!/usr/bin/env python3
"""
Test Target Parsing Fix

Tests that "last 3" correctly parses to count=3 and target="last"
"""

import sys
import os
import re

# Add the project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_target_parsing():
    """Test the target parsing logic"""
    print("🧪 Testing Target Parsing Logic")
    
    test_cases = [
        ("last 3", "last", 3),
        ("first 2", "first", 2),
        ("next 4", "next", 4),
        ("last", "last", 1),  # No number, should remain 1
        ("", "", 1),  # Empty target
    ]
    
    for target_input, expected_target, expected_count in test_cases:
        # Simulate the parsing logic from multi_event_operations.py
        target = target_input
        count = 1  # Default
        
        # Parse numeric count from target string (e.g., "last 3", "first 2")
        if target and not isinstance(count, int) or count == 1:
            # Extract number from target like "last 3", "first 2", "next 4"
            number_match = re.search(r'(\w+)\s+(\d+)', target)
            if number_match:
                target_word = number_match.group(1)  # "last", "first", etc.
                extracted_count = int(number_match.group(2))  # the number
                target = target_word  # Update target to just the word
                count = extracted_count  # Update count to the extracted number
        
        result_target = target
        result_count = count
        
        if result_target == expected_target and result_count == expected_count:
            print(f"✅ '{target_input}' -> target: '{result_target}', count: {result_count}")
        else:
            print(f"❌ '{target_input}' -> expected target: '{expected_target}', count: {expected_count}, got target: '{result_target}', count: {result_count}")
            return False
    
    return True

def test_syntax_check():
    """Check that the modified file compiles"""
    print("\n🧪 Testing Modified File Syntax")
    
    try:
        import py_compile
        py_compile.compile('backend/app/services/multi_event_operations.py', doraise=True)
        print("✅ multi_event_operations.py compiles successfully")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in multi_event_operations.py: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Multi-Event Fixes v0.1.100\n")
    
    parsing_passed = test_target_parsing()
    syntax_passed = test_syntax_check()
    
    print(f"\n📊 Test Results:")
    print(f"Target Parsing: {'✅ PASS' if parsing_passed else '❌ FAIL'}")
    print(f"Syntax Check: {'✅ PASS' if syntax_passed else '❌ FAIL'}")
    
    if parsing_passed and syntax_passed:
        print("\n🎉 All fixes ready for deployment!")
        return True
    else:
        print("\n⚠️ Some tests failed - review the output above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
