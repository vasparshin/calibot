#!/usr/bin/env python3
"""
Debug script for calendar move issues in v0.1.78

Issues to investigate:
1. Calendar lookup for "Tonya" 
2. Why events aren't moving between calendars
3. Success message URL formatting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.agent.calendar_agent import CalendarAgent
from backend.app.services.google_calendar import GoogleCalendarService

def test_calendar_lookup():
    """Test calendar lookup functionality"""
    print("=== TESTING CALENDAR LOOKUP ===")
    
    try:
        # Test calendar lookup
        calendar_service = GoogleCalendarService()
        calendar_agent = CalendarAgent(calendar_service)
        
        # Check if calendar agent is properly initialized
        print(f"Calendar agent initialized: {calendar_agent is not None}")
        print(f"Calendar cache exists: {hasattr(calendar_agent, 'calendar_cache')}")
        
        if hasattr(calendar_agent, 'calendar_cache') and calendar_agent.calendar_cache:
            print(f"Calendar cache size: {len(calendar_agent.calendar_cache)}")
            print("\nAll calendars:")
            for cal_id, info in calendar_agent.calendar_cache.items():
                name = info.get('name', 'No Name')
                print(f"  {cal_id}: {name}")
        else:
            print("Calendar cache is empty or not loaded")
            print("Attempting to update calendar cache...")
            
            # Try to load calendars
            try:
                calendars = calendar_service.get_calendars()
                if calendars:
                    print(f"Found {len(calendars)} calendars from API")
                    for cal in calendars:
                        print(f"  {cal.get('id', 'no_id')}: {cal.get('summary', 'No Name')}")
                else:
                    print("No calendars returned from API")
            except Exception as e:
                print(f"Error getting calendars: {e}")
        
        # Test Tonya lookup specifically
        print(f"\nTesting 'Tonya' lookup...")
        result = calendar_agent._find_calendar_by_name('Tonya')
        print(f"Calendar ID for 'Tonya': {result}")
        
        # Test other common names
        for name in ['Tonya', 'tonya', 'TONYA', 'zoutna', 'Personal']:
            result = calendar_agent._find_calendar_by_name(name)
            print(f"  '{name}' -> {result}")
            
    except Exception as e:
        print(f"Error in calendar lookup test: {e}")
        import traceback
        traceback.print_exc()

def test_intent_extraction():
    """Test the specific intent that's failing"""
    print("\n=== TESTING INTENT EXTRACTION ===")
    
    try:
        from backend.app.agent.nlp_agent import NLPAgent
        
        nlp_agent = NLPAgent()
        
        # Test the exact message that's failing
        test_message = 'move the lessons today to calendar "Tonya"'
        print(f"Testing message: {test_message}")
        
        # Test fallback logic
        print("Testing fallback regex for calendar extraction...")
        import re
        user_lower = test_message.lower()
        calendar_match = re.search(r'to calendar ["\']([^"\']+)["\']', user_lower)
        if calendar_match:
            target_calendar = calendar_match.group(1).strip()
            print(f"Extracted calendar name: '{target_calendar}'")
        else:
            print("No calendar match found")
            
        # Test other patterns
        patterns = [
            r'to calendar ["\']([^"\']+)["\']',
            r'to calendar ([^\s]+)',
            r'calendar ["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_lower)
            if match:
                print(f"Pattern '{pattern}' matched: '{match.group(1)}'")
            else:
                print(f"Pattern '{pattern}' did not match")
                
    except Exception as e:
        print(f"Error in intent extraction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar_lookup()
    test_intent_extraction()
