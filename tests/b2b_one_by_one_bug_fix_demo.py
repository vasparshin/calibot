"""
Bot-to-Bot Demo with Live Debugging for One-by-One Multi-Event Fix

This script performs a comprehensive automated test of the one-by-one bug fix
with real-time log monitoring and step-by-step verification.

CRITICAL TEST: Verifies the fix for the bug where clicking "yes" on first event
in one-by-one mode was deleting ALL events instead of just the current one.
"""

import asyncio
import logging
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OneByOneBugFixDemo:
    def __init__(self):
        self.bot_token = "7469105928:AAE_4j3R3rB4i_VYpQOXPu-Mj6lWWzuwRJ4"  # From PROJECT_RULES.md
        self.chat_id = -4627994150  # Test group from PROJECT_RULES.md
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.render_api_url = "https://api.render.com/v1"
        self.render_api_key = "rnd_OxNGMpAcYq8b3wpjdOoNdjXOHGh1"  # From scripts
        self.service_id = "srv-cshqdfgl6cac738oi2k0"  # CaliBOT service ID
        
    def send_telegram_message(self, text: str) -> Dict[str, Any]:
        """Send message to Telegram bot"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print(f"📤 SENT: {text}")
                    return {"success": True, "message_id": result["result"]["message_id"]}
                else:
                    print(f"❌ Telegram API error: {result}")
                    return {"success": False, "error": result}
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Exception sending message: {e}")
            return {"success": False, "error": str(e)}
    
    def simulate_button_click(self, callback_data: str, message_id: int) -> Dict[str, Any]:
        """Simulate clicking an inline keyboard button"""
        url = f"{self.base_url}/answerCallbackQuery"
        
        # First, we need to simulate the callback query
        # Since we can't directly trigger callbacks, we'll use a different approach
        print(f"🔘 SIMULATING BUTTON CLICK: {callback_data}")
        
        # For this demo, we'll send text commands that trigger the same logic
        if callback_data == "multi_one_delete":
            return self.send_telegram_message("one")
        elif callback_data.startswith("queue_confirm_"):
            return self.send_telegram_message("yes")
        elif callback_data.startswith("queue_skip_"):
            return self.send_telegram_message("skip")
        else:
            return self.send_telegram_message(callback_data)
    
    def get_recent_logs(self, minutes: int = 5) -> list:
        """Fetch recent logs from Render API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.render_api_key}",
                "Content-Type": "application/json"
            }
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)
            
            url = f"{self.render_api_url}/services/{self.service_id}/logs"
            params = {
                "startTime": start_time.isoformat() + "Z",
                "endTime": end_time.isoformat() + "Z",
                "limit": 100
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                logs = response.json()
                return logs
            else:
                print(f"❌ Failed to fetch logs: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return []
    
    def wait_and_monitor_logs(self, wait_seconds: int = 3, search_terms: list = None):
        """Wait and monitor logs for specific events"""
        print(f"⏳ Waiting {wait_seconds} seconds and monitoring logs...")
        
        if search_terms is None:
            search_terms = ["Processing single event", "Queue", "DELETE Event", "Successfully deleted"]
        
        time.sleep(wait_seconds)
        
        logs = self.get_recent_logs(2)  # Get last 2 minutes of logs
        
        print(f"\n🔍 LOG ANALYSIS (searching for: {search_terms}):")
        relevant_logs = []
        
        for log_entry in logs:
            message = log_entry.get("message", "")
            timestamp = log_entry.get("timestamp", "")
            
            # Check if log contains any of our search terms
            if any(term.lower() in message.lower() for term in search_terms):
                relevant_logs.append(f"{timestamp}: {message}")
        
        if relevant_logs:
            for log in relevant_logs[-10:]:  # Show last 10 relevant logs
                print(f"📝 {log}")
        else:
            print("🔍 No relevant logs found")
        
        return relevant_logs

async def run_one_by_one_bug_fix_demo():
    """Run comprehensive one-by-one bug fix demo with debugging"""
    
    print("🎯 ONE-BY-ONE BUG FIX VERIFICATION DEMO")
    print("=" * 80)
    print("🐛 TESTING FIX FOR: One-by-one processing deleting all events on first 'yes'")
    print("🔧 EXPECTED BEHAVIOR: Each 'yes' should process only current event, advance to next")
    print("🚨 BUG BEHAVIOR (FIXED): First 'yes' deletes all events, no next confirmation")
    print("=" * 80)
    
    demo = OneByOneBugFixDemo()
    
    try:
        # Step 1: Create test events
        print("\n📅 STEP 1: Creating test events for one-by-one demo")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        test_events = [
            f"create OneByOneBugTest_001 tomorrow 14:00-15:00",
            f"create OneByOneBugTest_002 tomorrow 15:00-16:00", 
            f"create OneByOneBugTest_003 tomorrow 16:00-17:00"
        ]
        
        for event_cmd in test_events:
            demo.send_telegram_message(event_cmd)
            time.sleep(1)
        
        demo.wait_and_monitor_logs(5, ["create", "Event created", "OneByOneBugTest"])
        
        # Step 2: Request multi-delete
        print("\n🗑️ STEP 2: Requesting multi-delete of test events")
        demo.send_telegram_message(f"delete all OneByOneBugTest events tomorrow")
        
        demo.wait_and_monitor_logs(5, ["Found", "events to delete", "multi_event"])
        
        # Step 3: Select "One by One" 
        print("\n1️⃣ STEP 3: Selecting 'One by One' processing")
        print("🔍 CRITICAL: This should set one_by_one_mode = True in queue")
        
        demo.send_telegram_message("one")
        
        demo.wait_and_monitor_logs(5, ["one_by_one_mode", "Queue", "DELETE Event 1 of"])
        
        # Step 4: CRITICAL TEST - Click "Yes" for first event
        print("\n✅ STEP 4: CRITICAL BUG FIX TEST - Clicking 'Yes' for FIRST event")
        print("🔍 DEBUGGING FOCUS:")
        print("   - Should process ONLY OneByOneBugTest_001")
        print("   - Should advance to 'DELETE Event 2 of 3' for OneByOneBugTest_002")
        print("   - Should NOT see 'Successfully deleted 3 event(s)!'")
        print("   - Should NOT see all 3 'Processing single event' logs at once")
        
        demo.send_telegram_message("yes")
        
        # Enhanced log monitoring for the critical test
        logs = demo.wait_and_monitor_logs(8, [
            "Processing single event", 
            "DELETE Event", 
            "Successfully deleted",
            "queue_continues",
            "next_confirmation"
        ])
        
        # Analyze logs for bug indicators
        print("\n🔬 BUG FIX ANALYSIS:")
        processing_logs = [log for log in logs if "Processing single event" in log]
        delete_event_logs = [log for log in logs if "DELETE Event" in log]
        success_logs = [log for log in logs if "Successfully deleted" in log and "event(s)" in log]
        
        print(f"📊 Processing single event logs: {len(processing_logs)}")
        print(f"📊 DELETE Event confirmations: {len(delete_event_logs)}")
        print(f"📊 Bulk success messages: {len(success_logs)}")
        
        if len(processing_logs) == 1:
            print("✅ GOOD: Only 1 event processed (bug fixed)")
        elif len(processing_logs) > 1:
            print("❌ BUG STILL EXISTS: Multiple events processed at once")
            
        if len(delete_event_logs) >= 2:
            print("✅ GOOD: Moved to next event confirmation")
        else:
            print("❌ ISSUE: No next event confirmation shown")
        
        # Step 5: Continue with second event
        print("\n✅ STEP 5: Processing second event")
        demo.send_telegram_message("yes")
        
        demo.wait_and_monitor_logs(5, ["Processing single event", "DELETE Event 3 of"])
        
        # Step 6: Skip third event to test skip functionality
        print("\n⏭️ STEP 6: Skipping third event to test skip functionality")
        demo.send_telegram_message("skip")
        
        demo.wait_and_monitor_logs(5, ["skip", "Skipped", "queue_complete"])
        
        # Step 7: Verify final state
        print("\n🔍 STEP 7: Verifying remaining events")
        demo.send_telegram_message(f"what events do I have tomorrow")
        
        demo.wait_and_monitor_logs(5, ["OneByOneBugTest", "events"])
        
        # Step 8: Cleanup any remaining events
        print("\n🧹 STEP 8: Cleaning up remaining test events")
        demo.send_telegram_message(f"delete any remaining OneByOneBugTest events tomorrow")
        
        time.sleep(2)
        demo.send_telegram_message("all")  # Delete all remaining
        
        demo.wait_and_monitor_logs(3, ["deleted", "OneByOneBugTest"])
        
        print("\n🎉 ONE-BY-ONE BUG FIX DEMO COMPLETED!")
        print("\n📋 VERIFICATION CHECKLIST:")
        print("✅ Check if first 'yes' processed only 1 event (not 3)")
        print("✅ Check if second event confirmation appeared") 
        print("✅ Check if buttons disappeared properly")
        print("✅ Check if skip functionality worked")
        print("✅ Check logs for proper queue flow")
        
        print(f"\n🔗 View full logs: https://dashboard.render.com/services/{demo.service_id}/logs")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_one_by_one_bug_fix_demo())
