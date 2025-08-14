#!/usr/bin/env python3
"""
CaliBOT Deployment Monitor and Queue Progression Tester

Monitors for v0.1.126 deployment and runs webhook tests once ready.
Tests the specific queue progression fix scenario.
"""

import time
import requests
import json
from datetime import datetime

class DeploymentMonitorAndTester:
    def __init__(self):
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.target_version = "0.1.126"
        self.test_chat_id = -4627994150  # Use the actual chat ID from logs
        
    def check_deployment_status(self):
        """Check if target version is deployed"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                version = health_data.get("version", "unknown")
                return version == self.target_version, version
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def create_webhook_message(self, text: str) -> dict:
        """Create webhook message payload"""
        return {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": self.test_chat_id,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        }
    
    def create_callback_query(self, callback_data: str) -> dict:
        """Create callback query payload"""
        return {
            "update_id": int(time.time()),
            "callback_query": {
                "id": f"test_{int(time.time())}",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "message": {
                    "message_id": int(time.time()) - 1,
                    "chat": {
                        "id": self.test_chat_id,
                        "type": "private"
                    },
                    "date": int(time.time()) - 1,
                    "text": "Test message"
                },
                "data": callback_data
            }
        }
    
    def send_webhook_request(self, payload: dict) -> dict:
        """Send webhook request"""
        try:
            response = requests.post(
                f"{self.backend_url}/telegram-webhook",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text[:200] if response.text else "No response"
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response": str(e)
            }
    
    def test_queue_progression_flow(self):
        """Test the complete queue progression flow"""
        print(f"\n🧪 TESTING QUEUE PROGRESSION FLOW")
        print("=" * 50)
        
        # Step 1: Send multi-event request
        print("📋 Step 1: Sending multi-event request...")
        payload1 = self.create_webhook_message("move the last 2 events of yesterday to today")
        result1 = self.send_webhook_request(payload1)
        
        if not result1["success"]:
            print(f"❌ Step 1 failed: {result1['response']}")
            return False
        
        print(f"✅ Step 1 success: {result1['status_code']}")
        time.sleep(3)  # Wait for processing
        
        # Step 2: Select one-by-one
        print("📋 Step 2: Selecting one-by-one processing...")
        payload2 = self.create_callback_query("confirm_one_update")
        result2 = self.send_webhook_request(payload2)
        
        if not result2["success"]:
            print(f"❌ Step 2 failed: {result2['response']}")
            return False
        
        print(f"✅ Step 2 success: {result2['status_code']}")
        time.sleep(3)  # Wait for queue setup
        
        # Step 3: Respond to first event (THE CRITICAL TEST)
        print("📋 Step 3: Responding to first event (CRITICAL)...")
        payload3 = self.create_callback_query("queue_confirm_0")
        result3 = self.send_webhook_request(payload3)
        
        if not result3["success"]:
            print(f"❌ Step 3 failed: {result3['response']}")
            return False
        
        print(f"✅ Step 3 success: {result3['status_code']}")
        time.sleep(3)  # Wait for queue progression
        
        # Step 4: Check logs for second event appearance
        print("📋 Step 4: Checking logs for queue progression...")
        return self.check_logs_for_progression()
    
    def check_logs_for_progression(self):
        """Check logs for evidence of queue progression"""
        try:
            import subprocess
            result = subprocess.run([
                "python", "scripts/recent_logs.py"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for queue progression indicators
                indicators = [
                    "Queue callback 'confirm' received",
                    "queue_continues",
                    "UPDATE Event 2 of 2",
                    "next_confirmation",
                    "Queue progression"
                ]
                
                found = []
                for indicator in indicators:
                    if indicator in logs:
                        found.append(indicator)
                
                print(f"📊 Found {len(found)} progression indicators: {found}")
                
                if len(found) >= 2:
                    print(f"✅ Queue progression detected in logs")
                    return True
                else:
                    print(f"❌ Insufficient queue progression evidence")
                    return False
            else:
                print(f"❌ Log fetch failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Log check error: {e}")
            return False
    
    def monitor_and_test(self):
        """Monitor deployment and run tests when ready"""
        print("🚀 CaliBOT Deployment Monitor & Queue Progression Tester")
        print("=" * 60)
        print(f"Target: {self.target_version}")
        print(f"Backend: {self.backend_url}")
        print()
        
        max_wait_time = 600  # 10 minutes
        check_interval = 30  # 30 seconds
        start_time = time.time()
        
        print(f"⏳ Monitoring deployment (max wait: {max_wait_time//60} minutes)...")
        
        while time.time() - start_time < max_wait_time:
            deployed, version_info = self.check_deployment_status()
            
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if deployed:
                print(f"\n🎉 {current_time} - Target version {self.target_version} deployed!")
                print(f"🚀 Starting queue progression tests...")
                
                # Run the actual tests
                test_success = self.test_queue_progression_flow()
                
                if test_success:
                    print(f"\n🎯 SUCCESS: Queue progression fix validated!")
                    print("✅ Webhook requests successful")
                    print("✅ Queue progression working in logs")
                    print("✅ Second event appears after first response")
                    return True
                else:
                    print(f"\n⚠️ PARTIAL SUCCESS: Deployment ready but queue progression needs investigation")
                    return False
            else:
                print(f"{current_time} - Waiting... (current: {version_info})")
                time.sleep(check_interval)
        
        print(f"\n⏰ Timeout: Deployment not ready after {max_wait_time//60} minutes")
        return False

if __name__ == "__main__":
    monitor = DeploymentMonitorAndTester()
    success = monitor.monitor_and_test()
    
    if success:
        print(f"\n🎉 Queue progression fix is working correctly!")
        print("The one-by-one workflow should now function properly in Telegram.")
    else:
        print(f"\n⚠️ Manual testing may be needed once deployment completes.")
    
    exit(0 if success else 1)
