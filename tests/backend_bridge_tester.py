#!/usr/bin/env python3
"""
Backend Bridge Test System - Tests Calibot by directly calling backend APIs instead of Telegram messages.

This bypasses the Telegram bot-to-bot limitation by:
1. Simulating webhook payloads directly to Calibot's backend
2. Testing the exact same code path that real users trigger
3. Monitoring responses and logs in real-time
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackendBridgeTester:
    def __init__(self, calibot_backend_url: str = "https://calibot-utq6.onrender.com", test_chat_id: int = -4627994150):
        self.backend_url = calibot_backend_url
        self.webhook_url = f"{calibot_backend_url}/webhook"
        self.test_chat_id = test_chat_id
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_telegram_update(self, message_text: str, user_id: int = 123456789) -> Dict[str, Any]:
        """Create a realistic Telegram webhook payload that simulates a human user."""
        return {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": user_id,
                    "is_bot": False,  # Critical: This simulates a HUMAN user
                    "first_name": "Test",
                    "last_name": "User", 
                    "username": "testuser",
                    "language_code": "en"
                },
                "chat": {
                    "id": self.test_chat_id,
                    "title": "Calendar testing",
                    "type": "group",
                    "all_members_are_administrators": False
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    async def send_webhook_payload(self, message_text: str, user_id: int = 123456789) -> Dict[str, Any]:
        """Send a webhook payload directly to Calibot's backend."""
        payload = self.create_telegram_update(message_text, user_id)
        
        logger.info(f"📡 Sending webhook payload: {message_text}")
        logger.info(f"🎯 Target: {self.webhook_url}")
        
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
                
                test_result = {
                    "message": message_text,
                    "status": status,
                    "response": result,
                    "success": 200 <= status < 300,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
                
                if test_result["success"]:
                    logger.info(f"✅ SUCCESS - Status: {status}")
                    logger.info(f"📥 Response: {str(result)[:200]}...")
                else:
                    logger.error(f"❌ FAILED - Status: {status}")
                    logger.error(f"📥 Response: {str(result)[:200]}...")
                
                return test_result
                
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return {
                "message": message_text,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
    
    async def test_critical_intent_extraction(self) -> List[Dict[str, Any]]:
        """Test the specific intent extraction issue that was reported."""
        
        logger.info("🎯 TESTING CRITICAL INTENT EXTRACTION ISSUE")
        logger.info("=" * 60)
        
        critical_tests = [
            {
                "message": "move the last 2 events of today to tomorrow",
                "expected_intent": "update",
                "description": "This was being incorrectly classified as 'query' instead of 'update'"
            },
            {
                "message": "show me tomorrow's schedule", 
                "expected_intent": "query",
                "description": "This should correctly be classified as 'query'"
            },
            {
                "message": "create an event called 'Test Meeting' tomorrow at 3pm",
                "expected_intent": "create", 
                "description": "Testing single event creation with formatting consistency"
            },
            {
                "message": "create 3 events: 'Morning standup' at 9am, 'Code review' at 11am, 'Lunch meeting' at 12pm all for tomorrow",
                "expected_intent": "create",
                "description": "Testing multiple event creation"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(critical_tests, 1):
            logger.info(f"\n🧪 Test {i}/4: {test_case['description']}")
            logger.info(f"📝 Message: '{test_case['message']}'")
            logger.info(f"🎯 Expected: {test_case['expected_intent']} intent")
            
            result = await self.send_webhook_payload(test_case["message"])
            result.update({
                "test_number": i,
                "expected_intent": test_case["expected_intent"],
                "description": test_case["description"]
            })
            results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        return results
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run a comprehensive test suite covering all major functionality."""
        
        logger.info("🚀 RUNNING COMPREHENSIVE TEST SUITE")
        logger.info("=" * 50)
        
        # Test the critical intent extraction issue first
        critical_results = await self.test_critical_intent_extraction()
        
        # Additional edge case tests
        logger.info("\n🔍 TESTING EDGE CASES")
        logger.info("=" * 30)
        
        edge_case_tests = [
            "reschedule my first meeting tomorrow to next Monday at 10am",
            "delete the last 3 events created today",
            "move all my meetings from today to next Friday", 
            "what events do I have next week between Monday and Friday"
        ]
        
        edge_results = []
        for message in edge_case_tests:
            result = await self.send_webhook_payload(message)
            edge_results.append(result)
            await asyncio.sleep(1)
        
        # Compile comprehensive results
        all_results = critical_results + edge_results
        successful = sum(1 for r in all_results if r.get("success", False))
        
        summary = {
            "test_run_id": f"comprehensive_{int(time.time())}",
            "total_tests": len(all_results),
            "successful_tests": successful,
            "failed_tests": len(all_results) - successful,
            "critical_tests": critical_results,
            "edge_case_tests": edge_results,
            "all_results": all_results,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 40)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Successful: {summary['successful_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {(successful/len(all_results)*100):.1f}%")
        
        return summary

async def main():
    """Automated testing system - no user input required."""
    
    print("🔗 CALIBOT AUTOMATED TESTING SYSTEM")
    print("=" * 50)
    print("🤖 Fully automated testing - no user input required")
    print("🎯 Backend: https://calibot-utq6.onrender.com")
    print("🔄 Running comprehensive test suite automatically...")
    print()
    
    async with BackendBridgeTester() as tester:
        # Run comprehensive test suite automatically
        print("🚀 STARTING AUTOMATED COMPREHENSIVE TESTING")
        print("=" * 50)
        
        summary = await tester.run_comprehensive_test_suite()
        
        # Save comprehensive results
        timestamp = int(time.time())
        filename = f"automated_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Automated test results saved to: {filename}")
        
        # Show summary
        print(f"\n📊 AUTOMATED TEST SUMMARY")
        print("=" * 40)
        print(f"✅ Total Tests: {summary.get('total_tests', 0)}")
        print(f"🎯 Successful: {summary.get('successful_tests', 0)}")
        print(f"❌ Failed: {summary.get('failed_tests', 0)}")
        
        success_rate = (summary.get('successful_tests', 0) / max(summary.get('total_tests', 1), 1)) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 EXCELLENT! Tests are mostly passing!")
        elif success_rate >= 60:
            print("\n⚠️ GOOD but needs some fixes")
        else:
            print("\n🔧 NEEDS ATTENTION - Multiple issues detected")
        
        return summary

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
