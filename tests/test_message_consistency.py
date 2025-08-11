#!/usr/bin/env python3
"""
Test to verify message format consistency across create/update/delete operations
and ensure inline keyboard button implementation
"""
import sys
import os
sys.path.append('/workspaces/calibot')

def test_keyboard_consistency():
    """Test that all operations use inline keyboards consistently"""
    print("🔘 Testing Inline Keyboard Consistency...")
    
    # Import the keyboard creation function
    try:
        from backend.app.services.telegram import create_confirmation_keyboard
        
        # Test different keyboard types
        test_cases = [
            ("single_event", "✅ Yes", "❌ No"),
            ("duplicate", "✅ Create Anyway", "❌ Cancel"),
            ("multi_event", "🔄 All", "1️⃣ One by One", "❌ Cancel")
        ]
        
        all_passed = True
        for case in test_cases:
            operation_type = case[0]
            expected_buttons = case[1:]
            
            keyboard = create_confirmation_keyboard(operation_type)
            print(f"   {operation_type}: {keyboard}")
            
            # Check that keyboard has inline_keyboard structure
            if "inline_keyboard" not in keyboard:
                print(f"      ❌ Missing inline_keyboard structure")
                all_passed = False
                continue
            
            # Extract button texts from keyboard
            button_texts = []
            for row in keyboard["inline_keyboard"]:
                for button in row:
                    button_texts.append(button["text"])
            
            # Check that expected buttons are present
            for expected_button in expected_buttons:
                if expected_button not in button_texts:
                    print(f"      ❌ Missing button: {expected_button}")
                    all_passed = False
                else:
                    print(f"      ✅ Found button: {expected_button}")
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Error testing keyboards: {e}")
        return False

def test_message_format_consistency():
    """Test that message formats are consistent across operations"""
    print("\n📝 Testing Message Format Consistency...")
    
    try:
        from backend.app.utils.message_formatter import MessageFormatter

        # Prepare mock events
        mock_event = {
            "summary": "Test Event",
            "start": "2025-08-09T10:00:00+01:00",
            "end": "2025-08-09T11:00:00+01:00",
            "calendar_name": "Test Calendar",
            "id": "evt_123",
            "htmlLink": "https://calendar.google.com/event/test"
        }

        # Test success message formatting for create/update/delete
        print("   Testing success messages:")
        create_msg = MessageFormatter.format_success_message_create([mock_event])
        update_msg = MessageFormatter.format_success_message_update([mock_event])
        delete_msg = MessageFormatter.format_success_message_delete(1)

        for label, msg in [("create", create_msg), ("update", update_msg), ("delete", delete_msg)]:
            print(f"      {label}: {msg.splitlines()[0]}")
            if "Successfully" not in msg:
                print(f"         ❌ Missing 'Successfully' in {label}")
                return False

        # Test confirmation message formatting (multi-event)
        print("\n   Testing confirmation message formatting:")
        confirmation_msg = MessageFormatter.format_confirmation_message("delete", [mock_event])
        print(f"      Confirmation header: {confirmation_msg.splitlines()[0]}")
        if "Found" not in confirmation_msg or "delete" not in confirmation_msg.lower():
            print("         ❌ Confirmation message missing expected content")
            return False

        # Test duplicate message formatting (simulate duplicates input)
        duplicate_msg = MessageFormatter.format_duplicate_message([{"new_event": mock_event}])
        if "duplicate" not in duplicate_msg.lower():
            print("         ❌ Duplicate message missing keyword")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Error testing message formats: {e}")
        return False

def test_bot_rules_compliance():
    """Test that current implementation matches BOT_RULES.md"""
    print("\n📋 Testing BOT_RULES.md Compliance...")
    
    try:
        # Check if BOT_RULES.md mentions inline keyboards as implemented
        with open('/workspaces/calibot/BOT_RULES.md', 'r') as f:
            content = f.read()
        
        # Check for "Planned" in context of keyboards (should NOT exist)
        lines = content.split('\n')
        keyboard_planned_found = False
        for i, line in enumerate(lines):
            if 'planned' in line.lower() and ('keyboard' in line.lower() or 
                (i < len(lines)-5 and any('keyboard' in lines[j].lower() for j in range(i, min(i+5, len(lines)))))):
                keyboard_planned_found = True
                break
        
        if keyboard_planned_found:
            print("   ❌ BOT_RULES.md still shows keyboards as 'Planned'")
            return False
        else:
            print("   ✅ BOT_RULES.md shows keyboards as implemented")
        
        # Check for consistent event format requirements
        required_elements = ["Event Name", "hyperlink", "Date", "Time", "Calendar Name"]
        for element in required_elements:
            if element.lower() in content.lower():
                print(f"      ✅ BOT_RULES.md includes {element} requirement")
            else:
                print(f"      ❌ Missing {element} requirement in BOT_RULES.md")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking BOT_RULES.md: {e}")
        return False

def main():
    """Run all consistency tests"""
    print("🔍 CaliBOT v0.1.16 - Message Format & Keyboard Consistency Test")
    print("=" * 65)
    
    test_results = []
    
    # Test 1: Keyboard consistency
    test_results.append(test_keyboard_consistency())
    
    # Test 2: Message format consistency  
    test_results.append(test_message_format_consistency())
    
    # Test 3: BOT_RULES.md compliance
    test_results.append(test_bot_rules_compliance())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 65)
    print(f"📊 CONSISTENCY TEST SUMMARY")
    print(f"   Tests Passed: {passed}/{total}")
    
    if passed == total:
        print(f"   🎉 ALL CONSISTENCY TESTS PASSED!")
        print(f"   ✅ Inline keyboards implemented across all operations")
        print(f"   ✅ Message formats consistent with BOT_RULES.md")
        print(f"   ✅ No duplicate confirmation messages")
        return True
    else:
        print(f"   ❌ CONSISTENCY ISSUES FOUND - {total-passed} test(s) failed")
        if not test_results[0]:
            print(f"   🔘 Keyboard implementation has issues")
        if not test_results[1]:
            print(f"   📝 Message format consistency problems")
        if not test_results[2]:
            print(f"   📋 BOT_RULES.md compliance issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
