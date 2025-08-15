"""
Test script to reproduce the one-by-one delete bug reported by user.

Issue: When user selects "one by one" and then clicks "yes" for first event,
the system deletes all events instead of just the first one and moving to the second.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_one_by_one_delete_bug():
    """Test the specific bug: one-by-one delete confirmation not working properly"""
    
    print("🔧 One-by-One Delete Bug Reproduction Test")
    print("=" * 60)
    
    # Test chat ID (-4627994150 is the documented test group)
    test_chat_id = -4627994150
    
    # Step 1: Create multiple test events to delete
    print("\n1. Creating test events for deletion...")
    
    # First, create some test events
    create_events = [
        {
            "event_name": "OneByOneBug_Test1",
            "start_time": "14:00",
            "end_time": "15:00", 
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        },
        {
            "event_name": "OneByOneBug_Test2", 
            "start_time": "15:00",
            "end_time": "16:00",
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        },
        {
            "event_name": "OneByOneBug_Test3",
            "start_time": "16:00", 
            "end_time": "17:00",
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        }
    ]
    
    try:
        # Import services
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        
        from app.services.google_calendar_service import GoogleCalendarService
        from app.services.telegram_bot_service import TelegramBotService
        from app.services.conversation import ConversationState
        from app.services.multi_event_operations import MultiEventOperationHandler
        from app.services.event_queue_handler import EventQueueHandler
        from app.config import get_config
        
        # Initialize services
        config = get_config()
        calendar_service = GoogleCalendarService()
        telegram_service = TelegramBotService(config.TELEGRAM_BOT_TOKEN)
        conversation_state = ConversationState()
        event_queue_handler = EventQueueHandler(
            telegram_service, 
            conversation_state, 
            calendar_service
        )
        multi_event_handler = MultiEventOperationHandler(
            calendar_service, 
            telegram_service, 
            conversation_state,
            event_queue_handler
        )
        
        # Create test events first
        print("Creating test events...")
        created_events = []
        for event_data in create_events:
            try:
                result = await calendar_service.create_event(event_data)
                if result.get('success'):
                    created_events.append({
                        'id': result.get('event_id'),
                        'name': event_data['event_name'],
                        'date': event_data['date'],
                        'start_time': event_data['start_time']
                    })
                    print(f"✅ Created: {event_data['event_name']}")
                else:
                    print(f"❌ Failed to create: {event_data['event_name']} - {result.get('message')}")
            except Exception as e:
                print(f"❌ Error creating {event_data['event_name']}: {e}")
        
        if len(created_events) < 3:
            print("❌ Could not create enough test events. Skipping test.")
            return
        
        print(f"✅ Created {len(created_events)} test events")
        
        # Step 2: Test the delete operation with one-by-one selection
        print("\n2. Testing delete operation with one-by-one selection...")
        
        # Simulate delete request for all test events
        delete_criteria = {
            'intent': 'delete',
            'event_name': 'OneByOneBug_Test',  # This should match all 3 events
            'date': created_events[0]['date']
        }
        
        # Call handle_delete_operation
        delete_result = await multi_event_handler.handle_delete_operation(test_chat_id, delete_criteria)
        
        print(f"Delete operation result: {delete_result}")
        
        if delete_result.get('success') and delete_result.get('requires_user_action'):
            print("✅ Multi-event delete confirmation received")
            
            # Step 3: Simulate selecting "one by one"
            print("\n3. Simulating 'one by one' selection...")
            
            confirmation_result = await multi_event_handler.confirm_operation(test_chat_id, "one")
            print(f"One-by-one confirmation result: {confirmation_result}")
            
            if confirmation_result.get('success'):
                print("✅ One-by-one mode activated")
                
                # Step 4: Check the queue state
                print("\n4. Checking queue state...")
                has_queue = event_queue_handler.has_pending_queue(test_chat_id)
                print(f"Has pending queue: {has_queue}")
                
                if has_queue:
                    # Step 5: Simulate clicking "yes" for the first event
                    print("\n5. Simulating 'yes' click for first event...")
                    
                    # Check queue before processing
                    queue = event_queue_handler.pending_queues.get(test_chat_id)
                    if queue:
                        print(f"Queue before processing: {len(queue['events'])} events")
                        print(f"Current index: {queue['current_index']}")
                        print(f"One-by-one mode: {queue.get('one_by_one_mode', False)}")
                    
                    # Process the "yes" response
                    queue_response = await event_queue_handler.process_queue_response(test_chat_id, "yes")
                    print(f"Queue response to 'yes': {queue_response}")
                    
                    # Check queue after processing
                    has_queue_after = event_queue_handler.has_pending_queue(test_chat_id)
                    print(f"Has pending queue after 'yes': {has_queue_after}")
                    
                    if has_queue_after:
                        queue_after = event_queue_handler.pending_queues.get(test_chat_id)
                        if queue_after:
                            print(f"Queue after processing: {len(queue_after['events'])} events")
                            print(f"Current index after: {queue_after['current_index']}")
                            
                            # This should show that we moved to the next event, not deleted all
                            if queue_after['current_index'] == 1:
                                print("✅ SUCCESS: Moved to next event as expected")
                            else:
                                print(f"❌ BUG: Current index is {queue_after['current_index']}, expected 1")
                    else:
                        # Check if this is because all events were processed/deleted at once (the bug)
                        print("❌ BUG: Queue disappeared - likely all events were deleted at once")
                        
                        # Check if events actually exist
                        remaining_events = await calendar_service.query_events({
                            'date': created_events[0]['date']
                        })
                        
                        test_events_remaining = [e for e in remaining_events.get('events', []) 
                                               if 'OneByOneBug_Test' in e.get('summary', '')]
                        
                        print(f"Remaining test events: {len(test_events_remaining)}")
                        for event in test_events_remaining:
                            print(f"  - {event.get('summary')} at {event.get('start', {}).get('dateTime', 'unknown time')}")
                        
                        if len(test_events_remaining) == 0:
                            print("❌ CONFIRMED BUG: All events deleted instead of just the first one")
                        elif len(test_events_remaining) == 2:
                            print("✅ Expected behavior: Only first event deleted")
                        else:
                            print(f"❓ Unexpected: {len(test_events_remaining)} events remaining")
                else:
                    print("❌ No pending queue found after one-by-one confirmation")
            else:
                print(f"❌ One-by-one confirmation failed: {confirmation_result}")
        else:
            print(f"❌ Delete operation failed or no confirmation needed: {delete_result}")
        
        # Cleanup: Delete any remaining test events
        print("\n6. Cleaning up remaining test events...")
        cleanup_events = await calendar_service.query_events({
            'date': created_events[0]['date']
        })
        
        test_events_to_cleanup = [e for e in cleanup_events.get('events', []) 
                                 if 'OneByOneBug_Test' in e.get('summary', '')]
        
        for event in test_events_to_cleanup:
            try:
                delete_result = await calendar_service.delete_event({
                    'event_id': event.get('id'),
                    'calendar_id': event.get('calendar_id', 'primary')
                })
                print(f"🧹 Cleaned up: {event.get('summary')}")
            except Exception as e:
                print(f"❌ Cleanup failed for {event.get('summary')}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_one_by_one_delete_bug())
