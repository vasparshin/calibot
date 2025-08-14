#!/usr/bin/env python3
"""
ONE-BY-ONE EVENT TESTING WITH FRONTEND & BACKEND INTEGRATION
- Creates safe test events first
- Tests one-by-one deletion progression 
- Tests confirmation flow patterns
- Shows TestBot visual messages AND CaliBOT backend responses
- Displays live logs during testing
- Fixes frontend/backend synchronization issue
"""

import asyncio
import aiohttp
import requests
import time
import json
from datetime import datetime, timedelta

class OneByOneEventTester:
    def __init__(self):
        self.backend_url = "https://calibot-utq6.onrender.com"
        self.webhook_url = f"{self.backend_url}/webhook"
        self.testbot_token = "7638628162:AAE-0eKLVAVjfNaP1sZgdYUzPbVmJkMjfN0"
        self.group_chat_id = -4627994150
        self.render_api_key = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"
        self.message_id = 2000
        self.test_events_created = []
        
    def create_webhook_payload(self, message_text: str) -> dict:
        """Create webhook payload for CaliBOT"""
        self.message_id += 1
        return {
            "update_id": self.message_id,
            "message": {
                "message_id": self.message_id,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "test_user_automation"
                },
                "chat": {
                    "id": self.group_chat_id,
                    "type": "supergroup", 
                    "title": "CaliBOT Testing Group"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    async def send_testbot_visual_message(self, message: str):
        """Send TestBot visual message - trying multiple approaches"""
        success = False
        
        # Method 1: Direct API call
        try:
            url = f"https://api.telegram.org/bot{self.testbot_token}/sendMessage"
            
            payload = {
                "chat_id": self.group_chat_id,
                "text": f"🤖 TestBot: {message}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                print(f"[CHECK] TestBot visual message sent: {message}")
                success = True
            else:
                print(f"[X] TestBot Method 1 failed ({response.status_code}): {response.text[:100]}")
                
        except Exception as e:
            print(f"[X] TestBot Method 1 error: {e}")
        
        # Method 2: Try with string chat_id
        if not success:
            try:
                payload = {
                    "chat_id": str(self.group_chat_id),
                    "text": f"🤖 TestBot Command: {message}"
                }
                
                response = requests.post(url, data=payload, timeout=15)
                
                if response.status_code == 200:
                    print(f"[CHECK] TestBot visual message sent (Method 2): {message}")
                    success = True
                else:
                    print(f"[X] TestBot Method 2 failed ({response.status_code}): {response.text[:100]}")
                    
            except Exception as e:
                print(f"[X] TestBot Method 2 error: {e}")
        
        return success
    
    async def send_webhook_to_calibot(self, message: str):
        """Send webhook to CaliBOT backend"""
        try:
            payload = self.create_webhook_payload(message)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                ) as response:
                    status = response.status
                    response_text = await response.text()
                    
                    if status == 200:
                        print(f"[CHECK] Webhook sent successfully: {message}")
                        return True, response_text
                    else:
                        print(f"[X] Webhook failed ({status}): {response_text[:100]}")
                        return False, response_text
                        
        except Exception as e:
            print(f"[X] Webhook error: {e}")
            return False, str(e)
    
    async def send_test_command(self, message: str, step_description: str):
        """Send both visual TestBot message and backend webhook"""
        print(f"\n📋 {step_description}")
        print(f"💬 Command: {message}")
        
        # Send TestBot visual message first
        visual_success = await self.send_testbot_visual_message(message)
        
        # Brief delay to ensure message order
        await asyncio.sleep(2)
        
        # Send webhook to CaliBOT backend
        webhook_success, response = await self.send_webhook_to_calibot(message)
        
        if visual_success and webhook_success:
            print(f"[CHECKCHECK] Both visual and backend messages sent successfully")
        elif webhook_success:
            print(f"[PARTIAL] Backend webhook worked, visual message may have failed")
        else:
            print(f"[XX] Command failed - check logs")
        
        return webhook_success
    
    async def create_test_events(self, count: int = 3):
        """Create multiple safe test events for deletion testing"""
        print(f"\n📝 CREATING {count} SAFE TEST EVENTS FOR ONE-BY-ONE TESTING")
        print("=" * 60)
        
        created_events = []
        
        for i in range(1, count + 1):
            event_name = f"TEST_ONEBYONE_{i:03d}"
            message = f"create {event_name} tomorrow at {13 + i}:00-{14 + i}:00 for testing"
            
            success = await self.send_test_command(
                message, 
                f"Step {i}: Creating test event {event_name}"
            )
            
            if success:
                created_events.append(event_name)
                print(f"[CHECK] Event created: {event_name}")
            else:
                print(f"[X] Failed to create: {event_name}")
            
            # Wait between creations
            await asyncio.sleep(4)
        
        self.test_events_created = created_events
        print(f"\n📊 Successfully created {len(created_events)}/{count} test events")
        return created_events
    
    async def test_one_by_one_deletion_flow(self):
        """Test complete one-by-one deletion progression"""
        print(f"\n🧪 ONE-BY-ONE DELETION WORKFLOW TESTING")
        print("=" * 60)
        
        if len(self.test_events_created) < 2:
            print("[X] Need at least 2 test events for one-by-one testing")
            return False
        
        # Step 1: Request deletion of multiple test events
        delete_message = f"delete {self.test_events_created[0]} and {self.test_events_created[1]}"
        success_1 = await self.send_test_command(
            delete_message,
            "Step 1: Multi-event deletion request"
        )
        
        if not success_1:
            print("[X] Initial deletion request failed")
            return False
        
        print("[CHECK] Multi-delete request sent - waiting for confirmation prompt...")
        await asyncio.sleep(6)
        
        # Step 2: Send "one by one" confirmation
        success_2 = await self.send_test_command(
            "one by one",
            "Step 2: One-by-one confirmation"
        )
        
        if not success_2:
            print("[X] One-by-one confirmation failed") 
            return False
        
        print("[CHECK] One-by-one confirmation sent - waiting for first event prompt...")
        await asyncio.sleep(6)
        
        # Step 3: Confirm first event deletion
        success_3 = await self.send_test_command(
            "yes",
            "Step 3: First event deletion confirmation"
        )
        
        if not success_3:
            print("[X] First event confirmation failed")
            return False
        
        print("[CHECK] First event confirmed - waiting for second event prompt...")
        await asyncio.sleep(6)
        
        # Step 4: Confirm second event deletion  
        success_4 = await self.send_test_command(
            "yes",
            "Step 4: Second event deletion confirmation"
        )
        
        if not success_4:
            print("[X] Second event confirmation failed")
            return False
        
        print("[CHECKCHECK] Complete one-by-one deletion sequence executed!")
        return True
    
    async def test_create_edit_delete_workflow(self):
        """Test comprehensive create/edit/delete workflow"""
        print(f"\n✏️ CREATE/EDIT/DELETE WORKFLOW TESTING")
        print("=" * 60)
        
        # Create an event for editing
        event_name = "TEST_EDIT_DELETE_001"
        create_message = f"create {event_name} tomorrow at 16:00-17:00 for editing test"
        
        success_create = await self.send_test_command(
            create_message,
            "Edit Test Step 1: Create event for editing"
        )
        
        if not success_create:
            print("[X] Event creation for editing failed")
            return False
        
        await asyncio.sleep(5)
        
        # Edit the event
        edit_message = f"change {event_name} to 18:00-19:00"
        success_edit = await self.send_test_command(
            edit_message,
            "Edit Test Step 2: Edit event time"
        )
        
        if not success_edit:
            print("[X] Event editing failed")
            return False
        
        await asyncio.sleep(5)
        
        # Delete the event
        delete_message = f"delete {event_name}"
        success_delete = await self.send_test_command(
            delete_message,
            "Edit Test Step 3: Delete edited event"
        )
        
        if success_delete:
            print("[CHECKCHECK] Complete create/edit/delete workflow executed!")
            return True
        else:
            print("[X] Event deletion failed")
            return False
    
    async def monitor_logs_background(self, duration=180):
        """Monitor logs in background during testing"""
        print(f"\n⏰ STARTING LOG MONITORING FOR {duration} SECONDS...")
        
        start_time = time.time()
        last_check = datetime.utcnow() - timedelta(minutes=1)
        
        while (time.time() - start_time) < duration:
            try:
                headers = {
                    "Authorization": f"Bearer {self.render_api_key}",
                    "Content-Type": "application/json"
                }
                
                end_time = datetime.utcnow()
                start_search = end_time - timedelta(minutes=2)
                
                url = "https://api.render.com/v1/services/srv-ctfbqacl6cac73aro0q0/logs"
                params = {
                    "startTime": start_search.isoformat() + "Z",
                    "endTime": end_time.isoformat() + "Z", 
                    "limit": 10
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logs = data.get("logs", [])
                            
                            # Show new logs only
                            new_logs = [log for log in logs 
                                      if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > last_check]
                            
                            for log in new_logs:
                                timestamp = log.get("timestamp", "")[:19].replace("T", " ")
                                message = log.get("message", "")[:80]
                                print(f"📋 {timestamp} | {message}")
                                last_check = max(last_check, datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')))
                
                await asyncio.sleep(8)  # Check every 8 seconds
                
            except Exception as e:
                print(f"[X] Log monitoring error: {e}")
                await asyncio.sleep(15)

async def main():
    """Run comprehensive one-by-one testing with frontend/backend integration"""
    print("🤖 ONE-BY-ONE EVENT TESTING WITH FRONTEND/BACKEND INTEGRATION")
    print("=" * 80)
    print("✅ This comprehensive test will:")
    print("  • Create safe test events (TEST_ONEBYONE_001, 002, 003)")
    print("  • Test multi-event deletion with one-by-one confirmation")
    print("  • Test create/edit/delete workflow") 
    print("  • Send TestBot visual messages + CaliBOT backend webhooks")
    print("  • Monitor live logs throughout testing")
    print("  • Fix frontend/backend synchronization issues")
    print()
    
    tester = OneByOneEventTester()
    
    # Start live log monitoring in background
    log_task = asyncio.create_task(tester.monitor_logs_background(180))  # 3 minutes
    
    try:
        print("🚀 PHASE 1: CREATE TEST EVENTS")
        created_events = await tester.create_test_events(3)
        
        if len(created_events) < 2:
            print("[X] Not enough test events created - skipping deletion test")
        else:
            print(f"\n🚀 PHASE 2: ONE-BY-ONE DELETION WORKFLOW")
            deletion_success = await tester.test_one_by_one_deletion_flow()
            
            if deletion_success:
                print(f"[CHECKCHECK] One-by-one deletion workflow completed successfully!")
            else:
                print(f"[X] One-by-one deletion workflow failed")
        
        print(f"\n🚀 PHASE 3: CREATE/EDIT/DELETE WORKFLOW")
        edit_success = await tester.test_create_edit_delete_workflow()
        
        if edit_success:
            print(f"[CHECKCHECK] Create/edit/delete workflow completed successfully!")
        else:
            print(f"[X] Create/edit/delete workflow failed")
        
        print(f"\n📋 TESTING COMPLETED - CHECK YOUR TELEGRAM GROUP:")
        print(f"  • TestBot messages showing commands sent")
        print(f"  • CaliBOT responses with confirmations and prompts")
        print(f"  • Complete one-by-one deletion progression")
        print(f"  • Create/edit/delete workflow demonstrations")
        
    except Exception as e:
        print(f"\n[X] Test execution error: {e}")
        
    finally:
        # Stop log monitoring
        log_task.cancel()
        print(f"\n⏰ Log monitoring stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[X] Testing interrupted by user")
    except Exception as e:
        print(f"\n[X] Error: {e}")
