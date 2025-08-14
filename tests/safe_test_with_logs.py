#!/usr/bin/env python3
"""
SAFE CaliBOT Multi-Event Testing
- Only creates and deletes CLEARLY MARKED test events  
- Shows live Render API logs during testing
- Sends both visual TestBot messages AND webhooks to CaliBOT
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timedelta

sys.path.append('.')
from tests.comprehensive_multi_event_automation import ComprehensiveMultiEventTester

class SafeTestRunner:
    def __init__(self):
        self.tester = ComprehensiveMultiEventTester()
    
    async def show_live_logs(self, duration_seconds=30):
        """Show live logs from Render API during testing"""
        print(f"\n[CLOCK] SHOWING LIVE LOGS FOR {duration_seconds} SECONDS")
        print("=" * 60)
        
        start_time = time.time()
        last_log_time = datetime.utcnow() - timedelta(minutes=1)
        
        while (time.time() - start_time) < duration_seconds:
            try:
                logs = await self.tester.get_render_logs(minutes_back=2)
                new_logs = [log for log in logs if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > last_log_time]
                
                for log in new_logs:
                    timestamp = log['timestamp'][:19].replace('T', ' ')
                    message = log['message'][:100]
                    print(f"[LOG] {timestamp} | {message}")
                    last_log_time = max(last_log_time, datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')))
                
                await asyncio.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                print(f"[X] Log fetch error: {e}")
                await asyncio.sleep(5)
    
    async def run_safe_test_with_logs(self):
        """Run safe testing with live log monitoring"""
        print("[ROBOT] SAFE CALIBOT TESTING WITH LIVE LOGS")
        print("=" * 60)
        print("[CHECK] SAFETY FEATURES:")
        print("  • Only creates TEST_AUTOMATION_EVENT_* events")
        print("  • Only deletes events it created")
        print("  • Shows live Render API logs")
        print("  • Sends webhooks to CaliBOT for real responses")
        print()
        
        # Start log monitoring in background
        log_task = asyncio.create_task(self.show_live_logs(120))  # 2 minutes of logs
        
        try:
            # Initialize tester
            await self.tester.initialize()
            
            # Step 1: Create safe test events
            print("\n[FIX] STEP 1: Creating safe test events...")
            safe_events_created = await self.tester.create_safe_test_events()
            
            if not safe_events_created:
                print("[X] Could not create safe test events - aborting")
                return False
            
            print("[CHECK] Safe test events created successfully")
            await asyncio.sleep(5)  # Let logs populate
            
            # Step 2: Test deletion of ONLY our test events
            print("\n[FIX] STEP 2: Testing safe deletion...")
            delete_message = "delete TEST_AUTOMATION_EVENT_001 and TEST_AUTOMATION_EVENT_002"
            
            # Send both visual message AND webhook
            print(f"[MSG] Sending message: {delete_message}")
            await self.tester.send_testbot_visual_message(delete_message, "SafeTestUser")
            
            await asyncio.sleep(5)  # Let logs populate
            
            # Step 3: Test creation
            print("\n[FIX] STEP 3: Testing safe creation...")
            create_message = "create TEST_AUTO_LESSON tomorrow at 2pm-3pm"
            
            print(f"[MSG] Sending message: {create_message}")
            await self.tester.send_testbot_visual_message(create_message, "SafeTestUser")
            
            await asyncio.sleep(5)  # Let logs populate
            
            print("\n[CHECK] Safe testing completed!")
            print("[REPORT] Check Telegram group for TestBot messages and CaliBOT responses")
            
        except Exception as e:
            print(f"\n[X] Test error: {e}")
            
        finally:
            # Stop log monitoring
            log_task.cancel()
            await self.tester.cleanup()

async def main():
    """Run safe testing with live logs"""
    runner = SafeTestRunner()
    await runner.run_safe_test_with_logs()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[X] Testing interrupted by user")
    except Exception as e:
        print(f"\n[X] Error: {e}")
