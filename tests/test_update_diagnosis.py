#!/usr/bin/env python3
"""
Simple test to identify the specific event editing issue.
Tests the route logic and multi-event operations.
"""

import sys
import os
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set required environment variables
os.environ['LITELLM_MODEL'] = 'gpt-4.1-mini'
os.environ['GOOGLE_CLIENT_ID'] = 'test'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test'

def test_intent_prompt_update_examples():
    """Test if the intent extraction prompt has proper update examples"""
    print("=== Testing Intent Extraction Prompt for Update Examples ===")
    
    try:
        from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
        
        print("Checking prompt for update examples...")
        
        # Check if prompt contains update examples
        if 'update' in INTENT_EXTRACTION_PROMPT.lower():
            print("✅ Prompt contains 'update' references")
        else:
            print("❌ Prompt missing 'update' references")
            
        # Check for specific update patterns
        update_patterns = [
            'new_start_time',
            'time_shift',
            'move',
            'change'
        ]
        
        for pattern in update_patterns:
            if pattern in INTENT_EXTRACTION_PROMPT:
                print(f"✅ Prompt contains '{pattern}' pattern")
            else:
                print(f"❌ Prompt missing '{pattern}' pattern")
                
        # Show relevant parts of the prompt
        lines = INTENT_EXTRACTION_PROMPT.split('\n')
        update_lines = [line for line in lines if 'update' in line.lower()]
        
        print("\nUpdate-related lines in prompt:")
        for line in update_lines[:5]:  # Show first 5
            print(f"  {line.strip()}")
            
    except ImportError as e:
        print(f"❌ Could not import prompt: {e}")

def test_multi_event_handler_import():
    """Test if multi-event handler can be imported and has update methods"""
    print("\n=== Testing Multi-Event Handler ===")
    
    try:
        from app.services.multi_event_operations import MultiEventOperationHandler
        
        # Check if class has required methods
        required_methods = [
            'handle_update_operation',
            'confirm_operation',
            '_execute_operation'
        ]
        
        for method in required_methods:
            if hasattr(MultiEventOperationHandler, method):
                print(f"✅ Handler has method: {method}")
            else:
                print(f"❌ Handler missing method: {method}")
                
        print("✅ MultiEventOperationHandler imported successfully")
        
    except ImportError as e:
        print(f"❌ Could not import MultiEventOperationHandler: {e}")

def test_google_calendar_service_update():
    """Test if Google Calendar service has update_event method"""
    print("\n=== Testing Google Calendar Service ===")
    
    try:
        from app.services.google_calendar import GoogleCalendarService
        
        # Check if service has update_event method
        if hasattr(GoogleCalendarService, 'update_event'):
            print("✅ GoogleCalendarService has update_event method")
            
            # Get method signature
            import inspect
            signature = inspect.signature(GoogleCalendarService.update_event)
            print(f"   Method signature: {signature}")
        else:
            print("❌ GoogleCalendarService missing update_event method")
            
    except ImportError as e:
        print(f"❌ Could not import GoogleCalendarService: {e}")

def test_routes_update_handling():
    """Test if routes.py properly handles update intents"""
    print("\n=== Testing Routes Update Handling ===")
    
    try:
        # Read routes.py to check for update handling
        routes_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'api', 'routes.py')
        
        with open(routes_path, 'r') as f:
            routes_content = f.read()
            
        # Check for update-related code
        update_checks = [
            ('intent == "update"', 'Direct update intent check'),
            ('elif intent in ["delete", "update"]', 'Multi-intent check'),
            ('handle_update_operation', 'Update operation handler call'),
            ('process_update_delete_with_confirmation', 'Confirmation handler')
        ]
        
        for pattern, description in update_checks:
            if pattern in routes_content:
                print(f"✅ Found: {description}")
            else:
                print(f"❌ Missing: {description}")
                
    except Exception as e:
        print(f"❌ Error reading routes.py: {e}")

def identify_likely_issues():
    """Identify the most likely issues based on common patterns"""
    print("\n=== Likely Issues Analysis ===")
    
    common_issues = [
        {
            "issue": "Intent not extracted as 'update'",
            "cause": "NLP agent parsing issue or prompt problem",
            "symptoms": "Update requests treated as create/delete/query"
        },
        {
            "issue": "Update operation not triggering confirmation",
            "cause": "Missing confirmation_needed flag or route logic issue",
            "symptoms": "No confirmation keyboard shown to user"
        },
        {
            "issue": "Confirmation callback not processed",
            "cause": "Missing callback handler or incorrect callback data parsing",
            "symptoms": "User clicks confirm but nothing happens"
        },
        {
            "issue": "Calendar API update call fails",
            "cause": "Incorrect datetime format or missing parameters",
            "symptoms": "API errors in logs"
        },
        {
            "issue": "Event not found for update",
            "cause": "Event search logic not finding target events",
            "symptoms": "No events found matching criteria"
        }
    ]
    
    print("Most common event editing issues:")
    for i, issue in enumerate(common_issues, 1):
        print(f"\n{i}. {issue['issue']}")
        print(f"   Cause: {issue['cause']}")
        print(f"   Symptoms: {issue['symptoms']}")

def main():
    """Run all diagnostic tests"""
    print("🔍 Event Editing Issue Diagnostic")
    print("=" * 50)
    
    test_intent_prompt_update_examples()
    test_multi_event_handler_import()
    test_google_calendar_service_update()
    test_routes_update_handling()
    identify_likely_issues()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic completed")
    print("\nNext steps:")
    print("1. Check production logs for specific error messages")
    print("2. Test with a simple update request: 'change my lesson to 3pm'")
    print("3. Verify intent extraction is working correctly")
    print("4. Check if confirmation keyboards are appearing")

if __name__ == "__main__":
    main()
