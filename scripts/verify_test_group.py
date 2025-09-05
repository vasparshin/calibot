#!/usr/bin/env python3
"""
Group Chat Verification Script
Helps ensure you're testing on the correct CaliBOT group chat before running tests.
"""

import sys
from datetime import datetime

def main():
    """Interactive group verification checklist"""
    print("🔍 CaliBOT Test Group Verification")
    print("=" * 40)
    
    print("\n1. Check Last Message Time:")
    last_msg_time = input("   Enter time of last message in group (HH:MM): ")
    current_time = datetime.now().strftime("%H:%M")
    
    print(f"   Current time: {current_time}")
    print(f"   Last message: {last_msg_time}")
    
    # Simple time comparison (not perfect but helps catch obvious issues)
    try:
        current_hour = int(current_time.split(':')[0])
        last_hour = int(last_msg_time.split(':')[0])
        time_diff = abs(current_hour - last_hour)
        
        if time_diff > 2:
            print("   ⚠️  WARNING: Large time gap detected - verify correct group!")
        else:
            print("   ✅ Time gap looks reasonable")
    except:
        print("   ⚠️  Could not parse time - manual verification needed")
    
    print("\n2. Group Identity Check:")
    group_name = input("   Enter group name/title: ")
    if "calibot" in group_name.lower() or "test" in group_name.lower():
        print("   ✅ Group name suggests correct test group")
    else:
        print("   ⚠️  Group name doesn't suggest CaliBOT test group")
    
    print("\n3. Bot Responsiveness:")
    print("   Send '/status' command to bot and check response")
    bot_response = input("   Did bot respond to /status? (y/n): ")
    
    if bot_response.lower() in ['y', 'yes']:
        print("   ✅ Bot is responsive")
    else:
        print("   ❌ Bot not responsive - check group/bot status")
    
    print("\n4. Recent Activity Check:")
    recent_activity = input("   Do you see recent test messages/interactions? (y/n): ")
    
    if recent_activity.lower() in ['y', 'yes']:
        print("   ✅ Recent activity confirmed")
    else:
        print("   ⚠️  No recent activity - verify correct group")
    
    print("\n" + "=" * 40)
    print("VERIFICATION SUMMARY:")
    
    # Count warnings
    checks_passed = 0
    total_checks = 4
    
    if time_diff <= 2:
        checks_passed += 1
    
    if "calibot" in group_name.lower() or "test" in group_name.lower():
        checks_passed += 1
        
    if bot_response.lower() in ['y', 'yes']:
        checks_passed += 1
        
    if recent_activity.lower() in ['y', 'yes']:
        checks_passed += 1
    
    print(f"Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed >= 3:
        print("✅ LIKELY CORRECT GROUP - Safe to proceed with testing")
        print("\nNext steps:")
        print("1. Run: python scripts/quick_version_check.py")
        print("2. Start multi-event testing workflow")
        return True
    else:
        print("⚠️  VERIFICATION CONCERNS - Review group selection")
        print("\nRecommended actions:")
        print("1. Double-check you're in the CaliBOT test group")
        print("2. Look for recent message timestamps")
        print("3. Send /status to verify bot connectivity")
        print("4. Re-run this verification script")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
