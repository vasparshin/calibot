#!/usr/bin/env python3
"""
Debug script to test regex patterns for calendar extraction
"""

import re

def test_calendar_patterns():
    """Test calendar extraction patterns against actual user message"""
    
    # The exact message from the logs
    user_message = 'move the lessons today to calendar "Tonya"'
    user_lower = user_message.lower()
    
    print(f"Original message: '{user_message}'")
    print(f"Lowercase message: '{user_lower}'")
    print()
    
    # Test patterns from the code
    calendar_patterns = [
        r'to calendar ["\']([^"\']+)["\']',  # 'to calendar "Name"'
        r'to calendar ([^\s]+)',             # 'to calendar Name'
        r'calendar ["\']([^"\']+)["\']',     # 'calendar "Name"'
        r'move.*to ([A-Z][a-zA-Z]+)',        # 'move to Name'
    ]
    
    print("Testing patterns:")
    for i, pattern in enumerate(calendar_patterns, 1):
        print(f"{i}. Pattern: {pattern}")
        match = re.search(pattern, user_lower)
        if match:
            target_calendar = match.group(1).strip()
            print(f"   ✅ MATCHED: '{target_calendar}'")
        else:
            print(f"   ❌ No match")
        print()
    
    # Test additional patterns
    print("Testing additional patterns:")
    additional_patterns = [
        r'to calendar\s*["\']([^"\']+)["\']',     # with optional space
        r'calendar\s*["\']([^"\']+)["\']',        # with optional space
        r'to\s+calendar\s+["\']([^"\']+)["\']',   # multiple spaces
        r'"([^"]+)"',                             # any quoted text
    ]
    
    for i, pattern in enumerate(additional_patterns, 1):
        print(f"{i}. Additional pattern: {pattern}")
        match = re.search(pattern, user_lower)
        if match:
            target_calendar = match.group(1).strip()
            print(f"   ✅ MATCHED: '{target_calendar}'")
        else:
            print(f"   ❌ No match")
        print()

if __name__ == "__main__":
    test_calendar_patterns()
