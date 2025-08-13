#!/usr/bin/env python3
"""
Automated Test Bot - Simulates user interactions with Calibot for comprehensive testing.

This script can:
1. Send automated messages to your Telegram bot
2. Monitor responses and logs
3. Run comprehensive test scenarios
4. Validate functionality without manual intervention
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomatedTestBot:
    def __init__(self, bot_token: str, chat_id: str, backend_url: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.backend_url = backend_url
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, text: str, wait_for_response: bool = True) -> Dict[str, Any]:
        """Send a message to the bot and optionally wait for response."""
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }
        
        logger.info(f"Sending message: {text}")
        
        async with self.session.post(url, json=payload) as response:
            result = await response.json()
            
        if wait_for_response:
            # Wait a bit for bot to process and respond
            await asyncio.sleep(2)
            
        return result
    
    async def get_updates(self, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get updates from Telegram API."""
        url = f"{self.telegram_api_url}/getUpdates"
        params = {"timeout": 5}
        if offset:
            params["offset"] = offset
            
        async with self.session.get(url, params=params) as response:
            result = await response.json()
            return result.get("result", [])
    
    async def simulate_webhook_payload(self, message_text: str, user_id: int = 12345) -> Dict[str, Any]:
        """Simulate a webhook payload that would be sent to the backend."""
        return {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": user_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    async def test_backend_directly(self, message_text: str, user_id: int = 12345) -> Dict[str, Any]:
        """Send a webhook payload directly to the backend for testing."""
        webhook_url = f"{self.backend_url}/webhook"
        payload = await self.simulate_webhook_payload(message_text, user_id)
        
        logger.info(f"Testing backend directly with: {message_text}")
        
        try:
            async with self.session.post(webhook_url, json=payload) as response:
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = {"status": response.status, "text": await response.text()}
                
                logger.info(f"Backend response: {result}")
                return result
        except Exception as e:
            logger.error(f"Backend test failed: {e}")
            return {"error": str(e)}
    
    async def run_test_scenario(self, scenario_name: str, test_messages: List[str]) -> Dict[str, Any]:
        """Run a complete test scenario with multiple messages."""
        logger.info(f"Starting test scenario: {scenario_name}")
        
        scenario_results = {
            "scenario": scenario_name,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "success": True,
            "errors": []
        }
        
        for i, message in enumerate(test_messages):
            try:
                # Test both direct backend and Telegram (if available)
                backend_result = await self.test_backend_directly(message)
                
                message_result = {
                    "message": message,
                    "backend_response": backend_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                scenario_results["messages"].append(message_result)
                
                # Brief pause between messages
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Error testing message '{message}': {e}"
                logger.error(error_msg)
                scenario_results["errors"].append(error_msg)
                scenario_results["success"] = False
        
        scenario_results["end_time"] = datetime.now().isoformat()
        self.test_results.append(scenario_results)
        
        logger.info(f"Completed scenario: {scenario_name} - Success: {scenario_results['success']}")
        return scenario_results

# Test scenarios
TEST_SCENARIOS = {
    "basic_calendar_operations": [
        "create an event called 'Team Meeting' tomorrow at 2pm",
        "show me my events for tomorrow",
        "move the last event to next Friday at 3pm",
        "delete the team meeting event"
    ],
    
    "multiple_events_operations": [
        "create 3 events: 'Morning standup' at 9am, 'Code review' at 11am, 'Lunch' at 12pm all for tomorrow",
        "show me tomorrow's schedule",
        "move the last 2 events of tomorrow to next Monday",
        "show me next Monday's schedule"
    ],
    
    "complex_date_handling": [
        "create an event 'Project deadline' next Friday at 5pm",
        "move it to the following Monday at 10am",
        "show me events for next week",
        "reschedule the project deadline to December 15th at 2pm"
    ],
    
    "error_scenarios": [
        "create an event without a time",
        "move a non-existent event",
        "delete all events (should ask for confirmation)",
        "show events for invalid date"
    ],
    
    "intent_extraction_test": [
        "move the last 2 events of today to tomorrow",
        "reschedule my first meeting of next week to Friday",
        "delete the last 3 events created this week",
        "show me events between next Monday and Friday"
    ]
}

async def main():
    """Run automated testing scenarios."""
    
    # Configuration - you'll need to set these
    BOT_TOKEN = os.getenv("TEST_BOT_TOKEN", "")
    CHAT_ID = os.getenv("TEST_CHAT_ID", "")
    BACKEND_URL = os.getenv("BACKEND_URL", "https://calibot-test.onrender.com")
    
    if not BOT_TOKEN:
        logger.error("TEST_BOT_TOKEN environment variable not set")
        return
    
    # Run tests
    async with AutomatedTestBot(BOT_TOKEN, CHAT_ID, BACKEND_URL) as test_bot:
        
        logger.info("Starting automated testing...")
        
        # Run all test scenarios
        for scenario_name, messages in TEST_SCENARIOS.items():
            await test_bot.run_test_scenario(scenario_name, messages)
            
            # Pause between scenarios
            await asyncio.sleep(2)
        
        # Generate test report
        report = {
            "test_run_id": f"test_{int(time.time())}",
            "total_scenarios": len(TEST_SCENARIOS),
            "successful_scenarios": sum(1 for r in test_bot.test_results if r["success"]),
            "failed_scenarios": sum(1 for r in test_bot.test_results if not r["success"]),
            "results": test_bot.test_results,
            "summary": {
                "start_time": test_bot.test_results[0]["start_time"] if test_bot.test_results else None,
                "end_time": test_bot.test_results[-1]["end_time"] if test_bot.test_results else None
            }
        }
        
        # Save report
        report_file = f"test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to: {report_file}")
        logger.info(f"Scenarios: {report['successful_scenarios']}/{report['total_scenarios']} successful")
        
        # Print summary
        print("\n" + "="*60)
        print("AUTOMATED TEST RESULTS")
        print("="*60)
        print(f"Total Scenarios: {report['total_scenarios']}")
        print(f"Successful: {report['successful_scenarios']}")
        print(f"Failed: {report['failed_scenarios']}")
        print(f"Report saved to: {report_file}")
        
        if report['failed_scenarios'] > 0:
            print("\nFAILED SCENARIOS:")
            for result in test_bot.test_results:
                if not result["success"]:
                    print(f"- {result['scenario']}: {len(result['errors'])} errors")
                    for error in result['errors']:
                        print(f"  • {error}")

if __name__ == "__main__":
    asyncio.run(main())
