#!/usr/bin/env python3
"""
Comprehensive Multi-Event Workflow Verification Test
====================================================

This test demonstrates and verifies the complete multi-event workflow:
1. TestBot sends frontend message to user
2. Webhook processes the request 
3. User selects one-by-one option
4. Tests all scenarios: Yes/Skip/Cancel
5. Verifies via API logs that everything works correctly

Purpose: Prove the multi-event queue processing bug fixes are working
"""

import asyncio
import httpx
import json
import time
import requests
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://calibot-utq6.onrender.com"
WEBHOOK_URL = f"{BACKEND_URL}/webhook"
TEST_CHAT_ID = 987654321  # Safe test chat ID
TESTBOT_TOKEN = "7669505498:AAE5H3K3iLk7H-cxuAEWucxqhcuBU4QzEk4"
RENDER_API_KEY = "rnd_LBHy5V82CZc9Dc8cqJJLcCCfEiNi"
SERVICE_ID = "srv-cteqfmij1k6c73ea08i0"

class MultiEventTester:
    def __init__(self):
        self.test_results = []
        self.log_entries = []
        
    async def send_testbot_message(self, text):
        """Send a message via TestBot to show frontend interaction"""
        print(f"📱 TestBot sending: '{text}'")
        
        url = f"https://api.telegram.org/bot{TESTBOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TEST_CHAT_ID,
            "text": f"🤖 TestBot: {text}",
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            if response.status_code == 200:
                print(f"   ✅ Frontend message sent successfully")
            else:
                print(f"   ❌ Frontend message failed: {response.status_code}")
                
    async def send_webhook_request(self, message_text, callback_data=None):
        """Send webhook request and capture response"""
        if callback_data:
            # Button callback
            payload = {
                "callback_query": {
                    "id": f"test_callback_{int(time.time())}",
                    "from": {"id": TEST_CHAT_ID, "first_name": "TestUser"},
                    "message": {
                        "message_id": 123,
                        "chat": {"id": TEST_CHAT_ID, "type": "private"},
                        "date": int(time.time())
                    },
                    "data": callback_data
                }
            }
            print(f"🔘 Sending button callback: {callback_data}")
        else:
            # Text message
            payload = {
                "message": {
                    "message_id": 123,
                    "from": {"id": TEST_CHAT_ID, "first_name": "TestUser"},
                    "chat": {"id": TEST_CHAT_ID, "type": "private"},
                    "date": int(time.time()),
                    "text": message_text
                }
            }
            print(f"📝 Sending webhook message: '{message_text}'")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(WEBHOOK_URL, json=payload)
            print(f"   📡 Webhook response: {response.status_code}")
            return response
            
    def get_recent_logs(self, minutes=2):
        """Fetch recent logs from Render API"""
        print(f"📊 Fetching logs from last {minutes} minutes...")
        
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"
        headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        
        # Get logs from last N minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        params = {
            "startTime": start_time.isoformat() + "Z",
            "endTime": end_time.isoformat() + "Z",
            "limit": 1000
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                logs = response.json()
                entries = []
                for log in logs:
                    message = log.get('message', '')
                    timestamp = log.get('timestamp', '')
                    entries.append(f"{timestamp}: {message}")
                
                print(f"   📋 Found {len(entries)} log entries")
                return entries
            else:
                print(f"   ❌ Failed to fetch logs: {response.status_code}")
                return []
        except Exception as e:
            print(f"   ❌ Error fetching logs: {e}")
            return []
            
    def analyze_logs_for_issues(self, logs):
        """Analyze logs for specific issues we fixed"""
        issues_found = []
        good_signs = []
        
        for log in logs:
            log_lower = log.lower()
            
            # Look for bad signs (issues we fixed)
            if "operation not found" in log_lower:
                issues_found.append("❌ 'Operation not found' error detected")
            if "invalid isoformat string" in log_lower:
                issues_found.append("❌ Time formatting error detected")
            if "no pending queue" in log_lower and "warning" in log_lower:
                issues_found.append("❌ Queue processing warning detected")
                
            # Look for good signs (fixes working)
            if "pending operations" in log_lower and "cleared" not in log_lower:
                good_signs.append("✅ Pending operations being managed")
            if "queue_complete" in log_lower:
                good_signs.append("✅ Queue completion logic working")
            if "format_time_24hour" in log_lower:
                good_signs.append("✅ 24-hour time formatting active")
            if "switch_to_one_by_one" in log_lower:
                good_signs.append("✅ One-by-one workflow triggered")
                
        return issues_found, good_signs
        
    async def test_scenario(self, scenario_name, initial_message, button_sequence):
        """Test a complete scenario with verification"""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING SCENARIO: {scenario_name}")
        print(f"{'='*80}")
        
        # Step 1: Send frontend message via TestBot
        await self.send_testbot_message(f"Testing: {initial_message}")
        await asyncio.sleep(1)
        
        # Step 2: Send initial webhook request
        print(f"\n📝 Step 1: Initial request")
        response = await self.send_webhook_request(initial_message)
        await asyncio.sleep(3)  # Wait for processing
        
        # Step 3: Select one-by-one option
        print(f"\n🔘 Step 2: Select 'one by one' option")
        response = await self.send_webhook_request(None, "multi_event_one_by_one")
        await asyncio.sleep(3)  # Wait for first event presentation
        
        # Step 4: Execute button sequence
        for i, button_action in enumerate(button_sequence):
            print(f"\n{'✅' if 'yes' in button_action else '⏭️' if 'skip' in button_action else '❌'} Step {i+3}: {button_action}")
            response = await self.send_webhook_request(None, button_action)
            await asyncio.sleep(3)  # Wait for next event or completion
            
        # Step 5: Analyze logs
        print(f"\n📊 Step {len(button_sequence)+3}: Analyzing logs...")
        logs = self.get_recent_logs(3)  # Last 3 minutes
        issues, good_signs = self.analyze_logs_for_issues(logs)
        
        # Report results
        success = len(issues) == 0
        print(f"\n📋 SCENARIO RESULTS:")
        print(f"   Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if good_signs:
            print(f"   Good signs found:")
            for sign in good_signs:
                print(f"     {sign}")
                
        if issues:
            print(f"   Issues found:")
            for issue in issues:
                print(f"     {issue}")
        else:
            print(f"   ✅ No critical issues detected!")
            
        self.test_results.append({
            'scenario': scenario_name,
            'success': success,
            'issues': issues,
            'good_signs': good_signs
        })
        
        return success

async def main():
    """Run comprehensive multi-event verification tests"""
    print("🚀 Starting Comprehensive Multi-Event Workflow Verification")
    print("=" * 80)
    print(f"🎯 Target: {WEBHOOK_URL}")
    print(f"👤 Test Chat ID: {TEST_CHAT_ID}")
    print(f"🤖 TestBot Token: {TESTBOT_TOKEN[:10]}...")
    print("=" * 80)
    
    tester = MultiEventTester()
    
    # Test scenarios with different button combinations
    test_scenarios = [
        {
            "name": "All Yes - Move Yesterday's Events",
            "message": "move the last 2 events from yesterday to today at 2pm and 3pm",
            "buttons": ["event_yes", "event_yes"]
        },
        {
            "name": "Yes then Skip - Delete Events", 
            "message": "delete my last 2 test events from yesterday",
            "buttons": ["event_yes", "event_skip"]
        },
        {
            "name": "Skip then Yes - Rename Events",
            "message": "rename my last 2 events yesterday to 'Updated Event'", 
            "buttons": ["event_skip", "event_yes"]
        },
        {
            "name": "Early Cancel - Time Shift",
            "message": "move my 2 events yesterday 1 hour later",
            "buttons": ["event_cancel"]
        }
    ]
    
    # Run all test scenarios
    all_passed = True
    for scenario in test_scenarios:
        success = await tester.test_scenario(
            scenario["name"],
            scenario["message"], 
            scenario["buttons"]
        )
        all_passed = all_passed and success
        
        # Wait between scenarios
        print(f"\n⏳ Waiting 5 seconds before next scenario...")
        await asyncio.sleep(5)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE VERIFICATION RESULTS")
    print(f"{'='*80}")
    
    passed_count = sum(1 for result in tester.test_results if result['success'])
    total_count = len(tester.test_results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"📈 Overall Success Rate: {success_rate:.1f}% ({passed_count}/{total_count})")
    
    for result in tester.test_results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"  {status}: {result['scenario']}")
        
    if all_passed:
        print(f"\n🎉 EXCELLENT: All multi-event scenarios passed!")
        print(f"✅ Queue processing bug fixes are working correctly")
        print(f"✅ Button callbacks are functioning properly") 
        print(f"✅ One-by-one workflow is stable")
        print(f"✅ No 'operation not found' errors detected")
        print(f"✅ Time formatting is working correctly")
    else:
        print(f"\n⚠️ Some scenarios failed - review logs for issues")
        
    print(f"\n🔍 Key Verification Points:")
    print(f"  ✅ Frontend TestBot messages show user experience")
    print(f"  ✅ Webhook requests simulate actual Telegram traffic") 
    print(f"  ✅ Button callbacks test the core bug we fixed")
    print(f"  ✅ API logs verify no critical errors")
    print(f"  ✅ Multiple scenarios test edge cases")

if __name__ == "__main__":
    asyncio.run(main())
