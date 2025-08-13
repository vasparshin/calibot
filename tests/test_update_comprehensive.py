#!/usr/bin/env python3
"""
Test specifically the event editing workflow to identify the exact issue.
"""

import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set required environment variables
os.environ['LITELLM_MODEL'] = 'gpt-4.1-mini'
os.environ['GOOGLE_CLIENT_ID'] = 'test'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test'

async def test_simple_update_scenario():
    """Test a simple update scenario to identify where it breaks"""
    print("=== Testing Simple Update Scenario ===")
    
    try:
        # Import required modules
        from app.agent.nlp_agent import NLPAgent
        from app.services.multi_event_operations import MultiEventOperationHandler
        from app.services.google_calendar import GoogleCalendarService
        from app.services.telegram import TelegramBotService
        from app.services.conversation import ConversationState
        
        # Test 1: Intent extraction
        print("1. Testing intent extraction...")
        nlp_agent = NLPAgent()
        
        # Mock the LLM call to return a proper update intent
        with patch('app.agent.nlp_agent.acompletion') as mock_llm:
            mock_llm.return_value = MagicMock()
            mock_llm.return_value.choices = [MagicMock()]
            mock_llm.return_value.choices[0].message = MagicMock()
            mock_llm.return_value.choices[0].message.content = '{"intent": "update", "event_name": "lesson", "new_start_time": "15:00", "confirmation_needed": true}'
            
            result = await nlp_agent.extract_intent_from_message("change my lesson to 3pm", [])
            print(f"   Intent extraction result: {json.dumps(result, indent=2)}")
            
            if result.get("intent") == "update":
                print("   ✅ Intent correctly extracted as 'update'")
            else:
                print(f"   ❌ Intent extraction failed. Got: {result.get('intent')}")
                return False
        
        # Test 2: Multi-event handler
        print("\n2. Testing multi-event update handler...")
        
        # Mock services
        calendar_service = MagicMock()
        calendar_service.get_events = AsyncMock(return_value=[
            {
                "id": "test_123",
                "summary": "lesson",
                "start": "2025-08-13T10:00:00",
                "end": "2025-08-13T11:00:00",
                "calendar_id": "primary",
                "calendar_name": "Main",
                "date": "2025-08-13",
                "start_time": "10:00",
                "end_time": "11:00"
            }
        ])
        
        telegram_service = MagicMock()
        conversation_state = MagicMock()
        
        handler = MultiEventOperationHandler(
            calendar_service=calendar_service,
            telegram_service=telegram_service,
            conversation_state=conversation_state
        )
        
        chat_id = 12345
        event_data = {
            "intent": "update",
            "event_name": "lesson",
            "new_start_time": "15:00",
            "confirmation_needed": True
        }
        
        handler_result = await handler.handle_update_operation(chat_id, event_data)
        print(f"   Handler result: {json.dumps(handler_result, indent=2)}")
        
        if handler_result.get("success") and handler_result.get("requires_user_action"):
            print("   ✅ Handler correctly requests user confirmation")
        else:
            print(f"   ❌ Handler failed: {handler_result}")
            return False
        
        # Test 3: Confirmation and execution
        print("\n3. Testing confirmation and execution...")
        
        # Mock the calendar service update call
        calendar_service.update_event = MagicMock(return_value={
            "success": True,
            "event_id": "test_123",
            "updated_event": {
                "summary": "lesson",
                "start": "2025-08-13T15:00:00",
                "end": "2025-08-13T16:00:00",
                "calendar_name": "Main",
                "id": "test_123",
                "htmlLink": "https://calendar.google.com/calendar/event?eid=test123"
            }
        })
        
        # Test confirmation
        confirm_result = await handler.confirm_operation(chat_id, "yes")
        print(f"   Confirmation result: {json.dumps(confirm_result, indent=2)}")
        
        if confirm_result.get("success"):
            print("   ✅ Confirmation and execution successful")
            
            # Check if calendar service was called
            if calendar_service.update_event.called:
                print("   ✅ Calendar service update_event was called")
                call_args = calendar_service.update_event.call_args
                print(f"      Called with: {call_args}")
            else:
                print("   ❌ Calendar service update_event was NOT called")
                return False
        else:
            print(f"   ❌ Confirmation failed: {confirm_result}")
            return False
        
        print("\n✅ All tests passed - update workflow appears to be working")
        return True
        
    except Exception as e:
        print(f"❌ ERROR in test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_datetime_formatting_issue():
    """Test if there's a datetime formatting issue causing calendar API failures"""
    print("\n=== Testing DateTime Formatting ===")
    
    try:
        from app.services.google_calendar import GoogleCalendarService
        
        # Test different datetime formats that might be causing issues
        test_formats = [
            "15:00",  # Simple time
            "2025-08-13T15:00:00",  # ISO format
            "2025-08-13T15:00:00+00:00",  # ISO with timezone
            "2025-08-13 15:00:00"  # Space-separated
        ]
        
        print("Testing datetime formats that might cause issues:")
        for fmt in test_formats:
            print(f"  {fmt}: ", end="")
            try:
                from datetime import datetime
                if "T" in fmt:
                    dt = datetime.fromisoformat(fmt.replace('Z', '+00:00'))
                    print(f"✅ Valid ISO format -> {dt}")
                elif ":" in fmt and len(fmt) <= 6:
                    print(f"⚠️  Time only, needs date")
                else:
                    print(f"❓ Unknown format")
            except Exception as e:
                print(f"❌ Invalid: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR testing datetime formats: {e}")
        return False

def check_common_deployment_issues():
    """Check for common issues that occur in production but not in testing"""
    print("\n=== Checking Common Deployment Issues ===")
    
    issues_checklist = [
        ("Environment variables", "Are all required env vars set in production?"),
        ("Google API credentials", "Are the Google Calendar API credentials valid and not expired?"),
        ("Token storage", "Are user authentication tokens being stored and retrieved correctly?"),
        ("Calendar permissions", "Does the bot have permission to read/write calendars?"),
        ("Event ID format", "Are event IDs being passed correctly between operations?"),
        ("Timezone handling", "Are timezones being handled correctly?"),
        ("User authentication", "Is the user properly authenticated with Google?"),
        ("Calendar selection", "Is the correct calendar being selected for updates?")
    ]
    
    print("Common issues to check in production logs:")
    for issue, description in issues_checklist:
        print(f"  • {issue}: {description}")
    
    print("\nDebugging commands to run on production:")
    print("  1. Check for authentication errors: Look for '401', 'unauthorized', 'token'")
    print("  2. Check for calendar API errors: Look for 'calendar', 'event not found', 'invalid'")  
    print("  3. Check intent processing: Look for 'intent', 'update', 'confirmation'")
    print("  4. Check callback handling: Look for 'callback', 'keyboard', 'confirm'")

async def main():
    """Run comprehensive event editing diagnostics"""
    print("🔍 Event Editing Issue Comprehensive Diagnosis")
    print("=" * 60)
    
    success = True
    
    try:
        # Run workflow test
        if not await test_simple_update_scenario():
            success = False
            
        # Run datetime formatting test  
        if not await test_datetime_formatting_issue():
            success = False
            
        # Check deployment issues
        check_common_deployment_issues()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 All local tests passed! Issue likely in production environment.")
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("1. Check production logs for specific error messages")
            print("2. Verify Google Calendar API credentials are valid")
            print("3. Test user authentication flow")
            print("4. Check if events are being found correctly")
            print("5. Verify callback handling is working")
        else:
            print("❌ Found issues in local testing - see above for details")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in diagnostics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
