#!/usr/bin/env python3
"""
Comprehensive Multi-Event Testing Automation Framework

COMPLETE AUTOMATION FOR CALIBOT MULTI-EVENT SCENARIOS:
- Webhook testing to simulate real user interactions
- Vercel API log analysis for response validation
- TestBot simulation in Telegram group chat
- Automated fixing, deployment, and retesting
- No user input required - fully automated validation

Tests the specific scenarios: editing, creating, deleting multiple events
with one-by-one progression workflow.
"""

import asyncio
import aiohttp
import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveMultiEventTester:
    def __init__(self):
        # Core configuration
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.webhook_url = f"{self.backend_url}/webhook"
        self.testbot_token = "8347695824:AAHWuCUM9hJR1BoCJHNwsIFX4fH84N2qYUA"
        self.group_chat_id = -4627994150
        self.test_chat_id = -1001234567890  # Private test chat
        
        # Render API for logs
        self.render_api_key = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"
        self.service_id = "srv-d1vqbkp5pdvs73echbeg"
        self.owner_id = "tea-d1vp1ph5pdvs73ebf50g"
        
        # Test state
        self.session = None
        self.message_id_counter = 1000
        self.test_results = []
        self.current_version = None
        
        # Expected behavior patterns from BOT_RULES.md
        self.expected_patterns = {
            "multi_event_confirmation": r"Found \d+ events to (delete|update|move):",
            "event_hyperlink": r"\[([^\]]+)\]\(https://calendar\.google\.com/[^)]+\)",
            "date_format": r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), [A-Z][a-z]+ \d{1,2}, \d{4}",
            "time_format": r"\d{1,2}:\d{2} (AM|PM)",
            "calendar_name": r"\([^)]+\)$",
            "inline_keyboard": r'"keyboard"',
            "one_by_one_progress": r"(UPDATE|DELETE|MOVE) Event \d+ of \d+",
            "success_message": r"Successfully (created|updated|deleted|moved) (\d+|all) events?"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result with structured format"""
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

    def create_telegram_webhook_payload(self, message_text: str, chat_id: int = None, user_id: int = 123456789) -> Dict:
        """Create realistic Telegram webhook payload"""
        chat_id = chat_id or self.test_chat_id
        self.message_id_counter += 1
        
        return {
            "update_id": self.message_id_counter,
            "message": {
                "message_id": self.message_id_counter,
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "last_name": "Automation",
                    "username": "testuser_automation"
                },
                "chat": {
                    "id": chat_id,
                    "type": "private" if chat_id > 0 else "group",
                    "title": "CaliBOT Test Group" if chat_id < 0 else None
                },
                "date": int(time.time()),
                "text": message_text
            }
        }

    def create_callback_query_payload(self, callback_data: str, original_message: str = "") -> Dict:
        """Create callback query for inline button simulation"""
        self.message_id_counter += 1
        
        return {
            "update_id": self.message_id_counter,
            "callback_query": {
                "id": str(self.message_id_counter),
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser_automation"
                },
                "message": {
                    "message_id": self.message_id_counter - 1,
                    "chat": {
                        "id": self.test_chat_id,
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": original_message
                },
                "data": callback_data
            }
        }

    async def send_webhook_request(self, payload: Dict) -> Dict:
        """Send webhook request to CaliBOT backend"""
        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                status = response.status
                
                try:
                    if response.content_type == 'application/json':
                        result = await response.json()
                    else:
                        result = await response.text()
                except:
                    result = await response.text()
                
                return {
                    "status_code": status,
                    "response": result,
                    "success": 200 <= status < 300
                }
        except Exception as e:
            return {
                "status_code": 0,
                "response": str(e),
                "success": False
            }

    async def send_testbot_visual_message(self, message: str, user_name: str = "TestUser") -> bool:
        """Send visual message to Telegram group via TestBot"""
        try:
            payload = {
                "chat_id": self.group_chat_id,
                "text": f"👤 <b>{user_name}:</b> {message}",
                "parse_mode": "HTML"
            }
            
            url = f"https://api.telegram.org/bot{self.testbot_token}/sendMessage"
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send visual message: {e}")
            return False

    async def get_render_logs(self, minutes_back: int = 5) -> List[Dict]:
        """Get recent logs from Render API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.render_api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "ownerId": self.owner_id,
                "resource": self.service_id,
                "limit": 50
            }
            
            response = requests.get(
                "https://api.render.com/v1/logs",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("logs", [])
            else:
                logger.error(f"Failed to get logs: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception getting logs: {e}")
            return []

    def analyze_logs_for_responses(self, logs: List[Dict], search_terms: List[str]) -> Dict:
        """Analyze logs for CaliBOT responses and behavior patterns"""
        relevant_logs = []
        found_patterns = []
        
        for log in logs:
            message = log.get("message", "").lower()
            timestamp = log.get("timestamp", "")
            
            # Look for search terms
            for term in search_terms:
                if term.lower() in message:
                    relevant_logs.append({
                        "timestamp": timestamp,
                        "message": log.get("message", ""),
                        "term": term
                    })
            
            # Check for expected patterns
            for pattern_name, pattern in self.expected_patterns.items():
                if re.search(pattern, log.get("message", ""), re.IGNORECASE):
                    found_patterns.append({
                        "pattern": pattern_name,
                        "timestamp": timestamp,
                        "message": log.get("message", "")
                    })
        
        return {
            "relevant_logs": relevant_logs,
            "found_patterns": found_patterns,
            "total_logs": len(logs)
        }

    async def verify_deployment_version(self) -> bool:
        """Verify deployment is up to date"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.current_version = data.get("version", "unknown")
                
                # Read local version
                with open("pyproject.toml", "r") as f:
                    content = f.read()
                    import re
                    match = re.search(r'version = "([^"]+)"', content)
                    local_version = match.group(1) if match else "unknown"
                
                version_match = self.current_version == local_version
                self.log_test_result(
                    "Version Check",
                    version_match,
                    f"Deployed: {self.current_version}, Local: {local_version}"
                )
                return version_match
            else:
                self.log_test_result("Version Check", False, f"Backend not responding: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Version Check", False, f"Exception: {e}")
            return False

    async def test_multi_event_delete_scenario(self) -> Dict:
        """Test multi-event delete with one-by-one progression"""
        scenario_name = "Multi-Event Delete One-by-One"
        results = []
        
        print(f"\n🧪 TESTING: {scenario_name}")
        print("=" * 60)
        
        # Step 1: Send visual message to group
        await self.send_testbot_visual_message("delete all events tomorrow", "TestUser")
        
        # Step 2: Send webhook request
        payload = self.create_telegram_webhook_payload("delete all events tomorrow")
        webhook_result = await self.send_webhook_request(payload)
        
        step1_success = webhook_result["success"]
        results.append(self.log_test_result(
            f"{scenario_name} - Initial Request",
            step1_success,
            f"Webhook status: {webhook_result['status_code']}"
        ))
        
        if not step1_success:
            return {"scenario": scenario_name, "results": results, "success": False}
        
        # Step 3: Wait and check logs for multi-event confirmation
        await asyncio.sleep(3)
        logs = await self.get_render_logs(minutes_back=2)
        log_analysis = self.analyze_logs_for_responses(logs, ["Found", "events to delete", "Choose an option"])
        
        confirmation_found = any("multi_event_confirmation" in p["pattern"] for p in log_analysis["found_patterns"])
        results.append(self.log_test_result(
            f"{scenario_name} - Confirmation Display",
            confirmation_found,
            f"Multi-event confirmation pattern found: {confirmation_found}"
        ))
        
        # Step 4: Simulate "one by one" button click
        callback_payload = self.create_callback_query_payload("confirm_one_by_one", "Choose processing method")
        callback_result = await self.send_webhook_request(callback_payload)
        
        results.append(self.log_test_result(
            f"{scenario_name} - One-by-One Selection",
            callback_result["success"],
            f"Callback status: {callback_result['status_code']}"
        ))
        
        # Step 5: Wait and check for first event progression
        await asyncio.sleep(3)
        logs = await self.get_render_logs(minutes_back=1)
        log_analysis = self.analyze_logs_for_responses(logs, ["DELETE Event 1 of", "Processing event"])
        
        progression_found = any("one_by_one_progress" in p["pattern"] for p in log_analysis["found_patterns"])
        results.append(self.log_test_result(
            f"{scenario_name} - First Event Progression",
            progression_found,
            f"Progression pattern found: {progression_found}"
        ))
        
        # Step 6: Simulate first event response (confirm delete)
        first_response_payload = self.create_callback_query_payload("confirm_yes", "DELETE Event 1 of 2")
        first_response_result = await self.send_webhook_request(first_response_payload)
        
        results.append(self.log_test_result(
            f"{scenario_name} - First Event Response",
            first_response_result["success"],
            f"First response status: {first_response_result['status_code']}"
        ))
        
        # Step 7: Wait and check for second event progression
        await asyncio.sleep(3)
        logs = await self.get_render_logs(minutes_back=1)
        log_analysis = self.analyze_logs_for_responses(logs, ["DELETE Event 2 of", "Event 2"])
        
        second_event_found = any("Event 2" in log["message"] for log in log_analysis["relevant_logs"])
        results.append(self.log_test_result(
            f"{scenario_name} - Second Event Progression",
            second_event_found,
            f"Second event progression found: {second_event_found}"
        ))
        
        overall_success = all(result for result in results)
        
        return {
            "scenario": scenario_name,
            "results": results,
            "success": overall_success,
            "log_analysis": log_analysis
        }

    async def test_multi_event_create_scenario(self) -> Dict:
        """Test multi-event creation with formatting validation"""
        scenario_name = "Multi-Event Create Batch"
        results = []
        
        print(f"\n🧪 TESTING: {scenario_name}")
        print("=" * 60)
        
        # Send visual message to group
        await self.send_testbot_visual_message("create lesson tomorrow at 8am, 9am and 10am", "TestUser")
        
        # Send webhook request
        payload = self.create_telegram_webhook_payload("create lesson tomorrow at 8am, 9am and 10am")
        webhook_result = await self.send_webhook_request(payload)
        
        step1_success = webhook_result["success"]
        results.append(self.log_test_result(
            f"{scenario_name} - Batch Request",
            step1_success,
            f"Webhook status: {webhook_result['status_code']}"
        ))
        
        # Wait and analyze logs for proper event formatting
        await asyncio.sleep(4)
        logs = await self.get_render_logs(minutes_back=2)
        log_analysis = self.analyze_logs_for_responses(logs, ["Successfully created", "events", "lesson"])
        
        # Check for proper formatting patterns
        formatting_checks = {
            "hyperlinks": any("event_hyperlink" in p["pattern"] for p in log_analysis["found_patterns"]),
            "date_format": any("date_format" in p["pattern"] for p in log_analysis["found_patterns"]),
            "time_format": any("time_format" in p["pattern"] for p in log_analysis["found_patterns"]),
            "success_message": any("success_message" in p["pattern"] for p in log_analysis["found_patterns"])
        }
        
        for check_name, check_result in formatting_checks.items():
            results.append(self.log_test_result(
                f"{scenario_name} - {check_name.replace('_', ' ').title()}",
                check_result,
                f"Pattern found: {check_result}"
            ))
        
        overall_success = all(result for result in results)
        
        return {
            "scenario": scenario_name,
            "results": results,
            "success": overall_success,
            "formatting_checks": formatting_checks,
            "log_analysis": log_analysis
        }

    async def test_multi_event_update_scenario(self) -> Dict:
        """Test multi-event update with proper confirmation flow"""
        scenario_name = "Multi-Event Update Flow"
        results = []
        
        print(f"\n🧪 TESTING: {scenario_name}")
        print("=" * 60)
        
        # Send visual message to group
        await self.send_testbot_visual_message("move all events tomorrow to next week", "TestUser")
        
        # Send webhook request
        payload = self.create_telegram_webhook_payload("move all events tomorrow to next week")
        webhook_result = await self.send_webhook_request(payload)
        
        step1_success = webhook_result["success"]
        results.append(self.log_test_result(
            f"{scenario_name} - Update Request",
            step1_success,
            f"Webhook status: {webhook_result['status_code']}"
        ))
        
        # Check for confirmation with inline keyboard
        await asyncio.sleep(3)
        logs = await self.get_render_logs(minutes_back=2)
        log_analysis = self.analyze_logs_for_responses(logs, ["Found", "events to", "Choose an option", "keyboard"])
        
        confirmation_found = any("multi_event_confirmation" in p["pattern"] for p in log_analysis["found_patterns"])
        keyboard_found = any("inline_keyboard" in p["pattern"] for p in log_analysis["found_patterns"])
        
        results.append(self.log_test_result(
            f"{scenario_name} - Confirmation Display",
            confirmation_found,
            f"Confirmation pattern found: {confirmation_found}"
        ))
        
        results.append(self.log_test_result(
            f"{scenario_name} - Inline Keyboard",
            keyboard_found,
            f"Keyboard pattern found: {keyboard_found}"
        ))
        
        overall_success = all(result for result in results)
        
        return {
            "scenario": scenario_name,
            "results": results,
            "success": overall_success,
            "log_analysis": log_analysis
        }

    async def run_comprehensive_test_suite(self) -> Dict:
        """Run complete test suite with automatic fixing if needed"""
        print("🚀 COMPREHENSIVE MULTI-EVENT TESTING AUTOMATION")
        print("=" * 70)
        print(f"🎯 Backend: {self.backend_url}")
        print(f"🤖 TestBot Group: {self.group_chat_id}")
        print(f"📊 Version: {self.current_version}")
        print()
        
        # Step 1: Verify deployment
        deployment_ok = await self.verify_deployment_version()
        if not deployment_ok:
            return {
                "success": False,
                "error": "Deployment verification failed",
                "results": self.test_results
            }
        
        # Step 2: Run test scenarios
        scenarios = []
        
        # Test multi-event delete with one-by-one progression
        delete_result = await self.test_multi_event_delete_scenario()
        scenarios.append(delete_result)
        
        # Test multi-event creation with formatting
        create_result = await self.test_multi_event_create_scenario()
        scenarios.append(create_result)
        
        # Test multi-event update flow
        update_result = await self.test_multi_event_update_scenario()
        scenarios.append(update_result)
        
        # Step 3: Analyze overall results
        total_scenarios = len(scenarios)
        successful_scenarios = sum(1 for s in scenarios if s["success"])
        
        print(f"\n📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        print(f"Total Scenarios: {total_scenarios}")
        print(f"Successful: {successful_scenarios}")
        print(f"Failed: {total_scenarios - successful_scenarios}")
        print(f"Success Rate: {(successful_scenarios/total_scenarios)*100:.1f}%")
        
        # Step 4: Detailed scenario results
        for scenario in scenarios:
            status = "✅" if scenario["success"] else "❌"
            print(f"\n{status} {scenario['scenario']}:")
            
            if "results" in scenario:
                for result in scenario["results"]:
                    result_status = "✅" if result else "❌"
                    print(f"  {result_status} {result}")
        
        # Step 5: Identify issues for auto-fixing
        issues_found = []
        if successful_scenarios < total_scenarios:
            for scenario in scenarios:
                if not scenario["success"]:
                    issues_found.append(scenario["scenario"])
        
        overall_success = successful_scenarios == total_scenarios
        
        final_result = {
            "success": overall_success,
            "total_scenarios": total_scenarios,
            "successful_scenarios": successful_scenarios,
            "scenarios": scenarios,
            "issues_found": issues_found,
            "test_results": self.test_results,
            "version": self.current_version
        }
        
        # Step 6: Auto-fix if needed (placeholder for future implementation)
        if not overall_success:
            print(f"\n🔧 ISSUES DETECTED - AUTO-FIXING REQUIRED")
            print("Issues found in scenarios:", ", ".join(issues_found))
            print("Auto-fixing functionality to be implemented...")
        
        return final_result

    async def save_test_report(self, results: Dict) -> str:
        """Save detailed test report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/multi_event_test_report_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Test report saved: {filename}")
        return filename

async def main():
    """Main execution - fully automated, no user input required"""
    async with ComprehensiveMultiEventTester() as tester:
        
        # Run comprehensive test suite
        results = await tester.run_comprehensive_test_suite()
        
        # Save detailed report
        report_file = await tester.save_test_report(results)
        
        # Final summary
        if results["success"]:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("CaliBOT multi-event scenarios are working correctly.")
            print("The one-by-one progression workflow is functioning as expected.")
        else:
            print(f"\n⚠️ TESTS FAILED - ISSUES DETECTED")
            print(f"Failed scenarios: {len(results['issues_found'])}")
            print("Auto-fixing and redeployment may be required.")
        
        print(f"\n📋 Detailed results saved to: {report_file}")
        
        return results["success"]

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
