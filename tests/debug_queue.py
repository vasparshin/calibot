#!/usr/bin/env python3
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.services.event_queue_handler import EventQueueHandler
from unittest.mock import MagicMock
from datetime import datetime

async def debug_queue_progression():
    print("🔍 Debugging one-by-one queue progression...")
    
    # Mock services
    calendar_service = MagicMock()
    calendar_agent = MagicMock()
    conversation_state = MagicMock()
    telegram_service = MagicMock()
    
    handler = EventQueueHandler(telegram_service, conversation_state, calendar_service, calendar_agent)
    
    # Create test events
    events = [
        {
            'intent': 'update',
            'event_id': 'event1', 
            'event_name': 'Lesson 1',
            'start_time': '2025-08-10T17:00:00Z',
            'end_time': '2025-08-10T18:00:00Z',
            'time_shift': '-3 hours'
        },
        {
            'intent': 'update',
            'event_id': 'event2',
            'event_name': 'Lesson 2',
            'start_time': '2025-08-10T19:00:00Z',
            'end_time': '2025-08-10T20:00:00Z',
            'time_shift': '-3 hours'
        }
    ]
    
    # Create queue
    chat_id = "test_user"
    handler.pending_queues[chat_id] = {
        'events': events,
        'current_index': 0,
        'created_at': datetime.now()
    }
    
    # Mock successful updates
    calendar_service.update_event.return_value = {
        'success': True,
        'updated_event': {'htmlLink': 'https://calendar.google.com/test'},
        'event_link': 'https://calendar.google.com/test'
    }
    
    print(f"Initial queue state: index={handler.pending_queues[chat_id]['current_index']}, total={len(events)}")
    
    # Step 1: User selects "one"
    print("\n=== STEP 1: User selects 'one' ===")
    step1_result = await handler.process_queue_response(chat_id, "one")
    print(f"Step1 result keys: {list(step1_result.keys())}")
    print(f"Step1 message preview: {step1_result.get('message', '')[:100]}...")
    print(f"Step1 has keyboard: {step1_result.get('keyboard') is not None}")
    print(f"Queue index after step1: {handler.pending_queues[chat_id]['current_index']}")
    
    # Step 2: User confirms first event
    print("\n=== STEP 2: User confirms first event with 'yes' ===")
    step2_result = await handler.process_queue_response(chat_id, "yes")
    print(f"Step2 result keys: {list(step2_result.keys())}")
    print(f"Step2 queue_continues: {step2_result.get('queue_continues')}")
    print(f"Step2 has next_confirmation: {step2_result.get('next_confirmation') is not None}")
    print(f"Step2 message: {step2_result.get('message', '')[:100]}...")
    
    if chat_id in handler.pending_queues:
        print(f"Queue index after step2: {handler.pending_queues[chat_id]['current_index']}")
    else:
        print("Queue was deleted after step2!")
    
    if step2_result.get('next_confirmation'):
        next_conf = step2_result['next_confirmation']
        print(f"Next confirmation message: {next_conf.get('message', '')[:100]}...")
        print(f"Next confirmation has keyboard: {next_conf.get('keyboard') is not None}")
    
    # Check what happens if queue still exists
    if chat_id in handler.pending_queues:
        print("\n=== STEP 3: User confirms second event ===")
        step3_result = await handler.process_queue_response(chat_id, "yes")
        print(f"Step3 result keys: {list(step3_result.keys())}")
        print(f"Step3 queue_complete: {step3_result.get('queue_complete')}")
        print(f"Step3 message: {step3_result.get('message', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_queue_progression())
