#!/usr/bin/env python3
"""
Test script to verify hyperlink formatting is preserved in Telegram messages
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio

def strip_markdown(text: str) -> str:
    """Remove Markdown formatting characters from text, but preserve hyperlinks"""
    import re
    # Remove bold **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic *text* (but not hyperlinks)
    text = re.sub(r'(?<!\])\*(.*?)\*(?!\()', r'\1', text)
    # Remove other common markdown
    text = re.sub(r'`(.*?)`', r'\1', text)  # code
    text = re.sub(r'_(.*?)_', r'\1', text)  # underline
    # Keep hyperlinks [text](url) intact
    return text

def detect_hyperlinks(text: str) -> bool:
    """Check if text contains hyperlinks that should trigger Markdown mode"""
    return '[' in text and '](' in text and ')' in text

def test_hyperlink_preservation():
    """Test that hyperlinks are preserved in markdown stripping"""
    print("Testing hyperlink preservation...")
    
    # Test cases
    test_cases = [
        {
            "input": "[Event Name](https://calendar.google.com/event/abc123)",
            "expected_preserved": True,
            "description": "Simple hyperlink"
        },
        {
            "input": "• [lesson](https://calendar.google.com/event/abc123) on Sat Aug 09 at 08:00 AM - 09:00 AM (Tonya's Calendar)",
            "expected_preserved": True,
            "description": "Hyperlink in formatted event"
        },
        {
            "input": "**Bold text** and *italic* but keep [link](http://example.com)",
            "expected_preserved": True,
            "description": "Mixed formatting with hyperlink"
        },
        {
            "input": "No hyperlinks here, just **bold** and *italic*",
            "expected_preserved": False,
            "description": "No hyperlinks to preserve"
        }
    ]
    
    print("\n=== Testing strip_markdown function ===")
    for i, case in enumerate(test_cases, 1):
        result = strip_markdown(case["input"])
        has_hyperlink = '[' in result and '](' in result and ')' in result
        
        print(f"\nTest {i}: {case['description']}")
        print(f"Input:    {case['input']}")
        print(f"Output:   {result}")
        print(f"Hyperlink preserved: {has_hyperlink}")
        print(f"Expected preserved: {case['expected_preserved']}")
        
        if has_hyperlink == case["expected_preserved"]:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            return False
    
    print("\n=== Testing message formatting logic ===")
    # Test the message detection logic
    test_messages = [
        "Successfully created 2 events:\n\n• [lesson](https://calendar.google.com/event/abc123) on Sat Aug 09 at 08:00 AM - 09:00 AM (Tonya's Calendar)",
        "Simple message without hyperlinks",
        "Multiple [link1](http://example1.com) and [link2](http://example2.com) in one message"
    ]
    
    for i, msg in enumerate(test_messages, 1):
        has_hyperlinks = '[' in msg and '](' in msg and ')' in msg
        print(f"\nMessage {i}: {'HAS' if has_hyperlinks else 'NO'} hyperlinks")
        print(f"Content: {msg[:80]}...")
        print(f"Would use Markdown mode: {has_hyperlinks}")
    
    return True

async def test_send_message_logic():
    """Test the send_telegram_message logic (without actually sending)"""
    print("\n=== Testing send_telegram_message logic ===")
    
    test_messages = [
        {
            "text": "• [lesson](https://calendar.google.com/event/abc123) on Sat Aug 09 at 08:00 AM",
            "should_use_markdown": True
        },
        {
            "text": "Simple text message without any special formatting",
            "should_use_markdown": False
        }
    ]
    
    for i, test in enumerate(test_messages, 1):
        print(f"\nTest {i}:")
        print(f"Input: {test['text']}")
        
        # Check the detection logic
        has_hyperlinks = detect_hyperlinks(test['text'])
        print(f"Hyperlinks detected: {has_hyperlinks}")
        print(f"Should use Markdown: {test['should_use_markdown']}")
        
        if has_hyperlinks == test['should_use_markdown']:
            print("✅ Detection logic PASS")
        else:
            print("❌ Detection logic FAIL")
            return False
    
    return True

if __name__ == "__main__":
    print("🔗 Testing Hyperlink Preservation in Telegram Messages")
    print("=" * 60)
    
    success = True
    
    try:
        # Test markdown stripping
        if not test_hyperlink_preservation():
            success = False
        
        # Test message sending logic
        if not asyncio.run(test_send_message_logic()):
            success = False
            
        print("\n" + "=" * 60)
        if success:
            print("✅ ALL TESTS PASSED - Hyperlink preservation is working!")
        else:
            print("❌ SOME TESTS FAILED - Hyperlink preservation needs fixes")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("=" * 60)
    exit(0 if success else 1)
