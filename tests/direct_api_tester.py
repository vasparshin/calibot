#!/usr/bin/env python3
"""
Direct API Tester - Tests Calibot backend directly without Telegram.

This bypasses Telegram entirely and sends webhook payloads directly to your backend,
allowing for rapid testing and debugging without manual message sending.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

class DirectAPITester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_webhook_payload(self, message_text: str, user_id: int = 12345) -> Dict[str, Any]:
        """Create a Telegram webhook payload."""
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
    
    async def test_message(self, message: str, user_id: int = 12345) -> Dict[str, Any]:
        """Test a single message against the backend."""
        webhook_url = f"{self.backend_url}/webhook"
        payload = self.create_webhook_payload(message, user_id)
        
        print(f"\n🧪 Testing: '{message}'")
        print(f"📡 Sending to: {webhook_url}")
        
        try:
            async with self.session.post(webhook_url, json=payload, timeout=30) as response:
                status = response.status
                
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = await response.text()
                
                print(f"✅ Status: {status}")
                print(f"📥 Response: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
                
                return {
                    "message": message,
                    "status": status,
                    "response": result,
                    "success": 200 <= status < 300,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "message": message,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_critical_scenarios(self) -> List[Dict[str, Any]]:
        """Test the critical scenarios that were previously failing."""
        
        critical_tests = [
            # Intent extraction issue - this was the main problem
            "move the last 2 events of today to tomorrow",
            
            # Multiple events processing
            "create 3 events: 'Meeting 1' at 9am, 'Meeting 2' at 11am, 'Meeting 3' at 2pm all for tomorrow",
            
            # Single event creation (formatting consistency issue)
            "create an event called 'Test Event' tomorrow at 3pm",
            
            # Update operations
            "move my first event of tomorrow to Friday at 4pm",
            
            # Delete operations
            "delete the last event of tomorrow",
            
            # Query operations (should work)
            "show me my events for tomorrow",
            
            # Complex date handling
            "reschedule my meeting tomorrow to next Monday at 10am",
        ]
        
        results = []
        for message in critical_tests:
            result = await self.test_message(message)
            results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        return results
    
    async def test_intent_extraction_specifically(self) -> None:
        """Focus specifically on intent extraction issues."""
        
        print("\n🎯 INTENT EXTRACTION FOCUS TEST")
        print("="*50)
        
        # Test cases that should be classified as 'update' not 'query'
        update_tests = [
            "move the last 2 events of today to tomorrow",
            "move my first meeting to Friday",
            "reschedule the team meeting to next week",
            "shift all today's events to Monday",
        ]
        
        # Test cases that should be classified as 'query'
        query_tests = [
            "show me tomorrow's schedule",
            "what events do I have next week",
            "list my meetings for Friday",
            "what's on my calendar tomorrow",
        ]
        
        print("\n📝 Update Intent Tests (should trigger event modifications):")
        for message in update_tests:
            await self.test_message(message)
        
        print("\n📋 Query Intent Tests (should show information):")
        for message in query_tests:
            await self.test_message(message)

async def main():
    """Run direct API tests."""
    
    # Check if we should test local or deployed
    backend_url = input("Enter backend URL (press Enter for localhost:8000): ").strip()
    if not backend_url:
        backend_url = "http://localhost:8000"
    
    print(f"\n🚀 Starting Direct API Testing")
    print(f"🎯 Target: {backend_url}")
    print("="*60)
    
    async with DirectAPITester(backend_url) as tester:
        
        # Test critical scenarios
        print("\n🔍 CRITICAL SCENARIOS TEST")
        results = await tester.test_critical_scenarios()
        
        # Run intent extraction focus test
        await tester.test_intent_extraction_specifically()
        
        # Summary
        successful = sum(1 for r in results if r.get("success", False))
        total = len(results)
        
        print(f"\n📊 SUMMARY")
        print("="*30)
        print(f"Total Tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        
        if successful < total:
            print(f"\n❌ FAILED TESTS:")
            for result in results:
                if not result.get("success", False):
                    print(f"  • {result['message']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
        
        # Save detailed results
        timestamp = int(time.time())
        report_file = f"api_test_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_run": timestamp,
                "backend_url": backend_url,
                "results": results,
                "summary": {
                    "total": total,
                    "successful": successful,
                    "failed": total - successful
                }
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {report_file}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
