"""
LLM-Driven Query Operation for handling event queries and schedule requests.

ARCHITECTURE:
1. User message → LLM extracts intent + generic parameters (event_name, date, etc.)
2. Query operation resolves dates and executes query
3. Query operation returns data with requires_llm_formatting=true
4. Routes passes data back to LLM for final response formatting
5. LLM formats user-friendly response and sends to user

This eliminates ALL hardcoded logic and makes the system truly flexible.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)

class QueryOperation(BaseOperation):
    """Handles event query operations including schedule requests."""

    async def execute(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query operation - LLM-driven approach."""
        try:
            # Extract query parameters from LLM response
            query_params = self.extract_query_parameters(event_data)

            # Execute the query to get data
            query_result = await self.execute_query(chat_id, query_params)

            # Return data for LLM to process and format final response
            return {
                "success": True,
                "query_result": query_result,
                "requires_llm_formatting": True,  # Signal that LLM should format the final response
                "original_request": event_data
            }

        except Exception as e:
            logger.error(f"Error in query operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process query."
            }

    def extract_query_parameters(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract query parameters from LLM response and resolve dates."""
        from datetime import datetime, timedelta

        # Get raw parameters from LLM
        raw_date = event_data.get("date", "")
        event_name = event_data.get("event_name", "")

        # Resolve relative dates to ISO format
        resolved_date = self.resolve_date_parameter(raw_date)

        return {
            "event_name": event_name,
            "date": resolved_date,  # Now in ISO format or empty for general queries
            "start_time": event_data.get("start_time", ""),
            "end_time": event_data.get("end_time", ""),
            "calendar_name": event_data.get("calendar_name", ""),
            "query_type": event_data.get("query_type", "general"),  # For context
            "target": event_data.get("target", ""),  # e.g., "last 3", "first 2", "all"
            "raw_date": raw_date  # Keep original for LLM context
        }

    def resolve_date_parameter(self, date_param: str) -> str:
        """Resolve relative date parameters to ISO format."""
        if not date_param:
            return ""

        date_param_lower = date_param.lower().strip()
        today = datetime.now()

        # Handle relative dates
        if date_param_lower == "today":
            return today.strftime("%Y-%m-%d")
        elif date_param_lower == "tomorrow":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_param_lower == "day after tomorrow":
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        elif date_param_lower == "yesterday":
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_param_lower == "this week":
            # Return start of current week (Monday)
            monday = today - timedelta(days=today.weekday())
            return monday.strftime("%Y-%m-%d")
        elif date_param_lower == "next week":
            # Return start of next week (Monday)
            monday = today - timedelta(days=today.weekday())
            next_monday = monday + timedelta(days=7)
            return next_monday.strftime("%Y-%m-%d")
        elif date_param_lower == "this month":
            # Return first day of current month
            first_day = today.replace(day=1)
            return first_day.strftime("%Y-%m-%d")
        elif date_param_lower == "next month":
            # Return first day of next month
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            return next_month.strftime("%Y-%m-%d")
        else:
            # Try to parse as ISO date or return as-is
            try:
                # Check if it's already an ISO date
                datetime.fromisoformat(date_param)
                return date_param
            except ValueError:
                # Return as-is for the calendar service to handle
                return date_param

    async def execute_query(self, chat_id: int, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual query based on LLM-provided parameters."""
        try:
            # Use calendar service to query events
            matched_events = await self.calendar_service.query_events(query_params)

            if not matched_events.get("success"):
                if matched_events.get("auth_required"):
                    return {
                        "auth_required": True,
                        "message": "Please authenticate with Google Calendar first",
                        "events": []
                    }
                return {
                    "success": False,
                    "message": matched_events.get("message", "Query failed"),
                    "events": []
                }

            events = matched_events.get("events", [])

            # Apply target filtering if specified (last N, first N, etc.)
            if query_params.get("target"):
                events = self.apply_target_filter(events, query_params["target"])

            return {
                "success": True,
                "events": events,
                "event_count": len(events),
                "query_params": query_params,
                "auth_required": False
            }

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "success": False,
                "message": f"Error retrieving events: {str(e)}",
                "events": []
            }

    def apply_target_filter(self, events: List[Dict], target: str) -> List[Dict]:
        """Apply target filtering like 'last 3', 'first 2', 'all'."""
        if not events:
            return events

        target_lower = target.lower().strip()

        if target_lower == "all":
            return events

        # Sort events chronologically for consistent ordering
        events_sorted = sorted(events, key=lambda x: x.get('start', ''))

        if target_lower.startswith("last"):
            try:
                count = int(target_lower.split()[-1]) if len(target_lower.split()) > 1 else 1
                return events_sorted[-count:]
            except (ValueError, IndexError):
                return events_sorted[-1:]  # Default to last 1

        elif target_lower.startswith("first"):
            try:
                count = int(target_lower.split()[-1]) if len(target_lower.split()) > 1 else 1
                return events_sorted[:count]
            except (ValueError, IndexError):
                return events_sorted[:1]  # Default to first 1

        # If target doesn't match patterns, return all events
        return events

    # Test method to demonstrate the new architecture
    def test_llm_driven_query(self):
        """Test the new LLM-driven query architecture"""
        print("🧪 Testing LLM-Driven Query Architecture")
        print("=" * 50)

        # Simulate LLM responses
        test_cases = [
            {
                "name": "Simple today query",
                "llm_response": {"intent": "query", "event_name": "", "date": "today"},
                "expected": "Should resolve 'today' to current date"
            },
            {
                "name": "Meeting query with date",
                "llm_response": {"intent": "query", "event_name": "meeting", "date": "tomorrow"},
                "expected": "Should find meetings for tomorrow"
            },
            {
                "name": "Week query",
                "llm_response": {"intent": "query", "event_name": "", "date": "this week"},
                "expected": "Should resolve 'this week' to Monday of current week"
            },
            {
                "name": "Target filtering",
                "llm_response": {"intent": "query", "event_name": "", "date": "today", "target": "last 3"},
                "expected": "Should return last 3 events chronologically"
            }
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. {test['name']}")
            print(f"   LLM Response: {test['llm_response']}")

            # Test parameter extraction
            params = self.extract_query_parameters(test['llm_response'])
            print(f"   Resolved Params: {params}")
            print(f"   Expected: {test['expected']}")

        print("\n✅ Architecture Test Complete")
        print("🎯 Key Benefits:")
        print("   - No hardcoded schedule types")
        print("   - Generic parameter handling")
        print("   - LLM formats final responses")
        print("   - Flexible and extensible")




