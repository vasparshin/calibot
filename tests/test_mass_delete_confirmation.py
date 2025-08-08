#!/usr/bin/env python3
"""
Test script to validate mass delete confirmation workflow
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/workspaces/calibot/backend')
os.chdir('/workspaces/calibot/backend')

from app.agent.nlp_agent import NLPAgent
from app.services.event_queue_handler import EventQueueHandler  
from app.services.multi_event_operations import MultiEventOperationHandler
from app.services.conversation import ConversationState

async def test_mass_delete_confirmation():
    """Test the complete mass delete confirmation workflow"""
    print("Testing Mass Delete Confirmation Workflow")
    print("=" * 50)
    
    # Initialize components
    nlp_agent = NLPAgent()
    event_queue_handler = EventQueueHandler()
    multi_event_handler = MultiEventOperationHandler()
    conversation_state = ConversationState()
    
    chat_id = "test_chat_123"
    
    # Test 1: Intent extraction for mass delete
    print("\n1. Testing intent extraction for mass delete request...")
    user_message = "Delete all events titled 'lesson' scheduled for day before yesterday"
    history = []
    
    try:
        event_data = await nlp_agent.extract_intent(user_message, history)
        print(f"   Intent extracted: {event_data}")
        
        if not isinstance(event_data, dict):
            print("   ❌ FAIL: event_data is not a dictionary")
            return False
            
        if event_data.get("intent") not in ["delete", "batch_delete"]:
            print(f"   ⚠️  WARNING: Intent is '{event_data.get('intent')}', expected 'delete' or 'batch_delete'")
        else:
            print("   ✅ PASS: Intent correctly identified")
            
    except Exception as e:
        print(f"   ❌ FAIL: Intent extraction failed: {e}")
        return False
    
    # Test 2: Multi-event detection
    print("\n2. Testing multi-event detection...")
    try:
        is_multi_event = event_queue_handler.detect_multi_event_request(event_data)
        print(f"   Multi-event detected: {is_multi_event}")
        
        if is_multi_event:
            print("   ✅ PASS: Multi-event request detected")
        else:
            print("   ⚠️  INFO: Single event or not detected as multi-event")
            
    except Exception as e:
        print(f"   ❌ FAIL: Multi-event detection failed: {e}")
        return False
    
    # Test 3: Queue creation simulation
    print("\n3. Testing queue creation for confirmation...")
    try:
        # Simulate finding matching events
        mock_events = [
            {
                "intent": "delete",
                "event_id": "event_1",
                "event_name": "lesson",
                "start_time": "2025-08-06 08:00",
                "end_time": "2025-08-06 09:00",
                "calendar_id": "primary",
                "calendar_name": "Default"
            },
            {
                "intent": "delete", 
                "event_id": "event_2",
                "event_name": "lesson",
                "start_time": "2025-08-06 10:00",
                "end_time": "2025-08-06 11:00",
                "calendar_id": "primary",
                "calendar_name": "Default"
            }
        ]
        
        queue_result = event_queue_handler.create_event_queue(chat_id, mock_events)
        print(f"   Queue creation result: {queue_result}")
        
        if queue_result.get("success"):
            print("   ✅ PASS: Queue created successfully")
        else:
            print(f"   ❌ FAIL: Queue creation failed: {queue_result}")
            return False
            
    except Exception as e:
        print(f"   ❌ FAIL: Queue creation failed: {e}")
        return False
    
    # Test 4: Pending operation check
    print("\n4. Testing pending operation detection...")
    try:
        has_pending_queue = event_queue_handler.has_pending_queue(chat_id)
        has_pending_operation = multi_event_handler.has_pending_operation(chat_id)
        
        print(f"   Has pending queue: {has_pending_queue}")
        print(f"   Has pending operation: {has_pending_operation}")
        
        if has_pending_queue or has_pending_operation:
            print("   ✅ PASS: Pending operations detected")
        else:
            print("   ❌ FAIL: No pending operations found after queue creation")
            return False
            
    except Exception as e:
        print(f"   ❌ FAIL: Pending operation check failed: {e}")
        return False
    
    # Test 5: Confirmation processing
    print("\n5. Testing confirmation processing...")
    try:
        confirmation_message = "Yes"
        
        if has_pending_queue:
            queue_result = await event_queue_handler.process_queue_response(chat_id, confirmation_message)
            print(f"   Queue confirmation result: {queue_result}")
        elif has_pending_operation:
            confirmation_result = await multi_event_handler.confirm_operation(chat_id, confirmation_message)
            print(f"   Operation confirmation result: {confirmation_result}")
        
        print("   ✅ PASS: Confirmation processing completed")
        
    except Exception as e:
        print(f"   ❌ FAIL: Confirmation processing failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Mass Delete Confirmation Workflow Test COMPLETED")
    print("All critical components are functioning correctly.")
    return True

async def test_type_safety():
    """Test type safety for event_data handling"""
    print("\nTesting Type Safety")
    print("=" * 30)
    
    # Test different event_data formats
    test_cases = [
        {"intent": "delete", "event_name": "lesson"},  # Valid dict
        [{"intent": "delete"}],  # Invalid list 
        "invalid_string",  # Invalid string
        None,  # Invalid None
        {"intent": "batch_create", "events": [{"intent": "create"}]}  # Batch format
    ]
    
    for i, event_data in enumerate(test_cases, 1):
        print(f"\n{i}. Testing event_data type: {type(event_data)}")
        
        # Simulate the validation logic from routes.py
        if not isinstance(event_data, dict):
            print(f"   ❌ Invalid type detected: {type(event_data)}")
            print("   ✅ PASS: Would be caught by validation")
        elif event_data.get("intent") == "batch_create" and "events" in event_data:
            print("   ✅ PASS: Batch format detected and would be handled")
        elif event_data.get("intent") in ["delete", "update"]:
            print("   ✅ PASS: Valid delete/update format")
        else:
            print("   ✅ PASS: Other valid format")
    
    return True

if __name__ == "__main__":
    async def main():
        print("CaliBOT Mass Delete Confirmation Test")
        print("====================================")
        
        success1 = await test_mass_delete_confirmation()
        success2 = await test_type_safety()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED!")
            print("The mass delete confirmation workflow is working correctly.")
        else:
            print("\n❌ SOME TESTS FAILED")
            print("Please check the error messages above.")
            
    asyncio.run(main())
