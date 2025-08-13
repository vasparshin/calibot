#!/usr/bin/env python3
"""
Simple Test Guide - Step by step testing without complex chat IDs.

This provides a simple manual testing approach that's much easier.
"""

import os

def main():
    print("🚀 SIMPLE BOT TESTING GUIDE")
    print("=" * 50)
    
    print("\n1️⃣ FIX GROUP CHAT ISSUE")
    print("📱 Go to @BotFather on Telegram")
    print("💬 Send: /setprivacy")
    print("🤖 Select: @vas_calibot")
    print("🔓 Choose: Disable")
    print("✅ Now your bot can read all group messages!")
    
    print("\n2️⃣ TEST IN PRIVATE CHAT")
    print("💬 Send to @vas_calibot directly:")
    print("   'show me my events for today'")
    print("   (This should work if your backend is running)")
    
    print("\n3️⃣ TEST THE CRITICAL ISSUE")
    print("💬 Send to @vas_calibot:")
    print("   'move the last 2 events of today to tomorrow'")
    print("   (This is the intent extraction issue we fixed)")
    
    print("\n4️⃣ TEST IN GROUP CHAT (after fixing privacy)")
    print("👥 Create a group chat")
    print("➕ Add @vas_calibot to the group")
    print("💬 Send: 'create an event called Test tomorrow at 3pm'")
    print("   (Bot should respond)")
    
    print("\n5️⃣ MONITOR BACKEND LOGS")
    print("🖥️ Check your Render deployment logs:")
    print("   https://dashboard.render.com/")
    print("   Look for webhook requests and responses")
    
    print("\n6️⃣ COMMON ISSUES & SOLUTIONS")
    print("❌ Bot not responding in private:")
    print("   → Check webhook URL in backend")
    print("   → Verify backend is deployed and running")
    print("   → Check environment variables")
    
    print("\n❌ Bot not responding in group:")
    print("   → Disable privacy mode (step 1)")
    print("   → Add bot as admin in group")
    print("   → Make sure bot has message permissions")
    
    print("\n❌ Bot responds but gives errors:")
    print("   → Check authentication (OAuth with Google)")
    print("   → Verify Google Calendar API credentials")
    print("   → Check OpenAI API key")
    
    print("\n🎯 BACKEND TESTING (alternative)")
    print("If you want to test the backend directly:")
    print("1. cd backend")
    print("2. uvicorn app.main:app --reload")
    print("3. cd ../tests")
    print("4. python direct_api_tester.py")
    print("5. Enter: http://localhost:8000")
    
    print("\n✅ EXPECTED BEHAVIOR")
    print("After fixing privacy mode, your bot should:")
    print("✅ Respond to messages in private chat")
    print("✅ Respond to messages in group chat")
    print("✅ Process 'move events' correctly as UPDATE intent")
    print("✅ Show consistent formatting for event messages")
    
    print("\n🔗 USEFUL COMMANDS")
    print("Test authentication: 'authenticate' or 'login'")
    print("Test simple query: 'show me today's events'")
    print("Test creation: 'create meeting tomorrow 2pm'")
    print("Test the fix: 'move last 2 events to tomorrow'")
    
    print(f"\n🤖 Your bot: @vas_calibot")
    print(f"🌐 Backend: https://calibot-utq6.onrender.com/webhook")
    print(f"📊 Monitor: https://dashboard.render.com/")

if __name__ == "__main__":
    main()
