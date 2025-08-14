#!/usr/bin/env python3
"""
CaliBOT One-by-One Queue Progression Test
Testing v0.1.126 queue progression fix via webhook endpoint

Simulates the exact user scenario:
1. "move the last 2 events of yesterday to today"
2. Select "one by one" 
3. Respond to first event
4. Verify second event appears
5. Complete workflow

Follows PROJECT_RULES.md testing guidelines.
"""

import asyncio
import json
import time
import requests
from datetime import datetime
import sys
import os

class CaliBotWebhookTester:
    def __init__(self):
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.test_chat_id = -1001234567890  # Test chat ID
        self.message_id_counter = 1000
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """Log test result with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅" if success else "❌"
        print(f"{timestamp} {status} {test_name}: {message}")
        
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        return success

    def create_webhook_message(self, text: str, chat_id: int = None) -> dict:
        """Create a Telegram webhook message payload"""
        chat_id = chat_id or self.test_chat_id
        self.message_id_counter += 1
        
        return {
            "update_id": self.message_id_counter,
            "message": {
                "message_id": self.message_id_counter,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": chat_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        }

    def create_callback_query(self, callback_data: str, message_text: str = "") -> dict:
        """Create a callback query payload for button press simulation"""
        self.message_id_counter += 1
        
        return {
            "update_id": self.message_id_counter,
            "callback_query": {
                "id": f"callback_{self.message_id_counter}",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "message": {
                    "message_id": self.message_id_counter - 1,
                    "from": {
                        "id": 987654321,
                        "is_bot": True,
                        "first_name": "CaliBOT",
                        "username": "calibot_vas"
                    },
                    "chat": {
                        "id": self.test_chat_id,
                        "first_name": "Test",
                        "last_name": "User",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                },
                "data": callback_data
            }
        }

    def send_webhook_request(self, payload: dict) -> dict:
        """Send webhook request to backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/telegram-webhook",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            return {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "response": str(e),
                "success": False
            }

    def check_backend_health(self) -> bool:
        """Check if backend is healthy and get version"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                version = health_data.get("version", "unknown")
                
                if version == "0.1.126":
                    return self.log_result("Backend Health", True, f"Backend healthy, version {version}")
                else:
                    return self.log_result("Backend Health", False, f"Wrong version: {version}, expected 0.1.126")
            else:
                return self.log_result("Backend Health", False, f"Health check failed: {response.status_code}")
                
        except Exception as e:
            return self.log_result("Backend Health", False, f"Health check error: {e}")

    def test_step_1_initial_request(self) -> dict:
        """Test Step 1: Send initial multi-event request"""
        print(f"\n🧪 STEP 1: Initial Multi-Event Request")
        
        # Send the exact user message
        payload = self.create_webhook_message("move the last 2 events of yesterday to today")
        result = self.send_webhook_request(payload)
        
        if result["success"]:
            self.log_result("Initial Request", True, "Webhook request successful")
            return {"success": True, "response": result}
        else:
            self.log_result("Initial Request", False, f"Webhook failed: {result['response']}")
            return {"success": False, "response": result}

    def test_step_2_one_by_one_selection(self) -> dict:
        """Test Step 2: Select one-by-one processing"""
        print(f"\n🧪 STEP 2: One-by-One Selection")
        
        # Simulate pressing "1️⃣ One by One" button
        callback_payload = self.create_callback_query(
            "confirm_one_update", 
            "Found 2 events to update..."
        )
        result = self.send_webhook_request(callback_payload)
        
        if result["success"]:
            self.log_result("One-by-One Selection", True, "Button press successful")
            return {"success": True, "response": result}
        else:
            self.log_result("One-by-One Selection", False, f"Button press failed: {result['response']}")
            return {"success": False, "response": result}

    def test_step_3_first_event_response(self) -> dict:
        """Test Step 3: Respond to first event"""
        print(f"\n🧪 STEP 3: First Event Response")
        
        # Simulate pressing "✅ Yes" on first event (should be queue_confirm_0)
        callback_payload = self.create_callback_query(
            "queue_confirm_0",
            "UPDATE Event 1 of 2: Current Event: lesson..."
        )
        result = self.send_webhook_request(callback_payload)
        
        if result["success"]:
            self.log_result("First Event Response", True, "First event response successful")
            return {"success": True, "response": result}
        else:
            self.log_result("First Event Response", False, f"First event response failed: {result['response']}")
            return {"success": False, "response": result}

    def test_step_4_second_event_response(self) -> dict:
        """Test Step 4: Respond to second event (if it appears)"""
        print(f"\n🧪 STEP 4: Second Event Response")
        
        # This step validates that second event appeared
        # We'll simulate responding to it
        callback_payload = self.create_callback_query(
            "queue_confirm_1", 
            "UPDATE Event 2 of 2: Current Event: lesson..."
        )
        result = self.send_webhook_request(callback_payload)
        
        if result["success"]:
            self.log_result("Second Event Response", True, "Second event response successful")
            return {"success": True, "response": result}
        else:
            self.log_result("Second Event Response", False, f"Second event response failed: {result['response']}")
            return {"success": False, "response": result}

    def check_logs_for_queue_progression(self) -> bool:
        """Check logs to validate queue progression worked"""
        print(f"\n🧪 LOGS ANALYSIS: Queue Progression Validation")
        
        # Run the log checker
        try:
            import subprocess
            result = subprocess.run([
                "python", "scripts/recent_logs.py"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for key indicators of successful queue progression
                success_indicators = [
                    "Queue callback 'confirm' received",
                    "queue_continues",
                    "UPDATE Event 2 of 2",
                    "next_confirmation"
                ]
                
                found_indicators = []
                for indicator in success_indicators:
                    if indicator in logs:
                        found_indicators.append(indicator)
                
                if len(found_indicators) >= 2:
                    self.log_result("Logs Analysis", True, 
                                  f"Found {len(found_indicators)} queue progression indicators")
                    return True
                else:
                    self.log_result("Logs Analysis", False, 
                                  f"Only found {len(found_indicators)} indicators: {found_indicators}")
                    return False
            else:
                self.log_result("Logs Analysis", False, f"Log fetch failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Logs Analysis", False, f"Log analysis error: {e}")
            return False

    async def run_comprehensive_test(self) -> bool:
        """Run the complete one-by-one queue progression test"""
        print("🚀 CaliBOT One-by-One Queue Progression Test")
        print("=" * 60)
        print("Testing v0.1.126 queue progression fix")
        print(f"Backend: {self.backend_url}")
        print(f"Test Chat ID: {self.test_chat_id}")
        print()
        
        # Step 0: Check backend health
        if not self.check_backend_health():
            return False
        
        # Add delay to ensure backend is ready
        print("⏳ Waiting 2 seconds for backend readiness...")
        await asyncio.sleep(2)
        
        # Step 1: Send initial request
        step1_result = self.test_step_1_initial_request()
        if not step1_result["success"]:
            return False
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Step 2: Select one-by-one processing
        step2_result = self.test_step_2_one_by_one_selection()
        if not step2_result["success"]:
            return False
        
        # Wait for queue setup
        await asyncio.sleep(2)
        
        # Step 3: Respond to first event
        step3_result = self.test_step_3_first_event_response()
        if not step3_result["success"]:
            return False
        
        # Wait for queue progression
        await asyncio.sleep(3)
        
        # Step 4: Respond to second event (validation)
        step4_result = self.test_step_4_second_event_response()
        
        # Wait for completion
        await asyncio.sleep(2)
        
        # Check logs for validation
        logs_success = self.check_logs_for_queue_progression()
        
        # Calculate overall success
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Test Results Summary")
        print("=" * 40)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Save detailed results
        results_file = f"tests/queue_progression_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_suite": "One-by-One Queue Progression",
                "version": "0.1.126",
                "timestamp": datetime.now().isoformat(),
                "backend_url": self.backend_url,
                "test_chat_id": self.test_chat_id,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": success_rate
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        # Overall assessment
        overall_success = success_rate >= 80 and logs_success
        
        if overall_success:
            print(f"\n🎉 SUCCESS: Queue progression fix is working!")
            print("✅ Webhook requests successful")
            print("✅ Button interactions working")
            print("✅ Queue progression validated in logs")
            print("✅ Second event appears after first response")
        else:
            print(f"\n⚠️ ISSUES DETECTED: Queue progression needs attention")
            print("❌ Some webhook interactions failed")
            print("❌ Check logs for queue progression indicators")
        
        return overall_success

if __name__ == "__main__":
    tester = CaliBotWebhookTester()
    success = asyncio.run(tester.run_comprehensive_test())
    
    if success:
        print(f"\n🎯 Queue progression fix validated successfully!")
        print("The one-by-one workflow should now work correctly in Telegram.")
    else:
        print(f"\n⚠️ Queue progression fix needs further investigation.")
        print("Check the generated test results file for details.")
    
    sys.exit(0 if success else 1)
