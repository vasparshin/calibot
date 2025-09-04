"""
Backend Query Response Formatter

This script analyzes the feasibility of moving query response formatting from LLM to backend.
Currently, the system uses LLM for final response formatting, but this could be replaced with
backend logic to reduce LLM calls and improve consistency.

ARCHITECTURE ANALYSIS:
1. Current Flow: User → LLM Intent → Query Operation → LLM Formatting → Response
2. Proposed Flow: User → LLM Intent → Query Operation → Backend Formatting → Response

ADVANTAGES:
- Reduces LLM calls by 1 per query (from 2 to 1)
- Improves response consistency
- Faster response times
- Lower costs
- More predictable formatting

DISADVANTAGES:
- Less natural language variation
- Harder to handle edge cases
- Requires maintaining formatting logic
- Less flexible for complex queries

IMPLEMENTATION COMPLEXITY: MEDIUM
- Need to replicate LLM formatting logic
- Handle various query types (schedule, specific events, date ranges)
- Maintain natural language responses
- Handle edge cases (no events, errors, etc.)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BackendQueryFormatter:
    """
    Backend-based query response formatter to replace LLM formatting.
    
    This class replicates the LLM formatting logic for query responses,
    providing consistent, fast formatting without additional LLM calls.
    """
    
    def __init__(self):
        """Initialize the backend formatter."""
        pass
    
    def format_query_response(self, query_data: Dict[str, Any], original_request: Dict[str, Any]) -> str:
        """
        Format query response using backend logic instead of LLM.
        
        Args:
            query_data: Result from query operation containing events and metadata
            original_request: Original user request for context
            
        Returns:
            Formatted response string ready to send to user
        """
        try:
            # Extract data
            events = query_data.get("events", [])
            event_count = query_data.get("event_count", 0)
            query_params = query_data.get("query_params", {})
            original_message = original_request.get("original_message", "")
            
            # Handle authentication requirement
            if query_data.get("auth_required"):
                return "Please authenticate with Google Calendar first: /start"
            
            # Handle query failures
            if not query_data.get("success", True):
                return f"I couldn't retrieve your calendar information: {query_data.get('message', 'Unknown error')}"
            
            # Handle no events found
            if not events:
                return self._format_no_events_response(original_message, query_params)
            
            # Format events found
            return self._format_events_response(events, original_message, query_params)
            
        except Exception as e:
            logger.error(f"BackendQueryFormatter: Error formatting query response: {e}")
            return "I encountered an error while formatting your query results. Please try again."
    
    def _format_no_events_response(self, original_message: str, query_params: Dict[str, Any]) -> str:
        """Format response when no events are found."""
        # Extract query context
        date = query_params.get("raw_date", "")
        event_name = query_params.get("event_name", "")
        
        # Build natural language response
        if date and event_name:
            return f"I couldn't find any events named '{event_name}' on {date}. Try checking a different date or event name."
        elif date:
            return f"I couldn't find any events on {date}. Your calendar appears to be free on that day."
        elif event_name:
            return f"I couldn't find any events named '{event_name}'. Try checking a different event name or date range."
        else:
            return "I couldn't find any events matching your request. Try being more specific about the date or event name."
    
    def _format_events_response(self, events: List[Dict], original_message: str, query_params: Dict[str, Any]) -> str:
        """Format response when events are found."""
        # Import here to avoid circular imports
        from app.utils.message_formatter import MessageFormatter
        
        # Build response header
        event_count = len(events)
        date = query_params.get("raw_date", "")
        event_name = query_params.get("event_name", "")
        
        # Create natural language header
        header = self._create_response_header(event_count, date, event_name, original_message)
        
        # Format each event using existing MessageFormatter
        formatted_events = []
        for event in events:
            try:
                # Use existing master formatter for consistency
                formatted_event = MessageFormatter.format_event_with_hyperlink(event, include_hyperlink=True)
                formatted_events.append(f"• {formatted_event}")
            except Exception as e:
                logger.warning(f"BackendQueryFormatter: Error formatting event {event.get('summary', 'Unknown')}: {e}")
                # Fallback formatting
                fallback = self._format_event_fallback(event)
                formatted_events.append(f"• {fallback}")
        
        # Combine header and events
        if formatted_events:
            return f"{header}\n\n" + "\n".join(formatted_events)
        else:
            return header
    
    def _create_response_header(self, event_count: int, date: str, event_name: str, original_message: str) -> str:
        """Create natural language header for query response."""
        # Analyze original message for context
        message_lower = original_message.lower()
        
        if "schedule" in message_lower or "what" in message_lower and "today" in message_lower:
            if date:
                return f"Here's your schedule for {date}:"
            else:
                return f"Here's your schedule:"
        
        elif "when" in message_lower:
            if event_name:
                return f"Here's when '{event_name}' is scheduled:"
            else:
                return f"Here are the events I found:"
        
        elif "find" in message_lower or "show" in message_lower:
            if event_name:
                return f"I found {event_count} event(s) named '{event_name}':"
            else:
                return f"I found {event_count} event(s):"
        
        else:
            # Generic response
            if event_count == 1:
                return "Here's the event I found:"
            else:
                return f"Here are the {event_count} events I found:"
    
    def _format_event_fallback(self, event: Dict[str, Any]) -> str:
        """Fallback event formatting when MessageFormatter fails."""
        try:
            # Extract basic event information
            title = event.get('summary', 'Untitled Event')
            start = event.get('start', {})
            end = event.get('end', {})
            calendar_name = event.get('calendar_name', 'Unknown Calendar')
            link = event.get('htmlLink', event.get('link', ''))
            
            # Parse datetime
            if isinstance(start, dict):
                start_time = start.get('dateTime', start.get('date', ''))
            else:
                start_time = str(start)
            
            if isinstance(end, dict):
                end_time = end.get('dateTime', end.get('date', ''))
            else:
                end_time = str(end)
            
            # Format date and time
            try:
                if 'T' in start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%A, %B %d, %Y')
                    formatted_start = dt.strftime('%H:%M')
                    
                    if 'T' in end_time:
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        formatted_end = end_dt.strftime('%H:%M')
                        time_display = f"at {formatted_start} - {formatted_end}"
                    else:
                        time_display = f"at {formatted_start}"
                else:
                    formatted_date = "Unknown date"
                    time_display = "at Unknown time"
            except:
                formatted_date = "Unknown date"
                time_display = "at Unknown time"
            
            # Create hyperlink if available
            if link:
                return f"[{title}]({link}) on {formatted_date} {time_display} ({calendar_name})"
            else:
                return f"{title} on {formatted_date} {time_display} ({calendar_name})"
                
        except Exception as e:
            logger.error(f"BackendQueryFormatter: Fallback formatting failed: {e}")
            return f"Event: {event.get('summary', 'Unknown')} (formatting error)"
    
    def format_schedule_response(self, events: List[Dict], date: str) -> str:
        """Specialized formatter for schedule queries."""
        if not events:
            return f"Your schedule for {date} is clear - no events found."
        
        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x.get('start', ''))
        
        # Create schedule-specific header
        if date.lower() == "today":
            header = "Here's your schedule for today:"
        elif date.lower() == "tomorrow":
            header = "Here's your schedule for tomorrow:"
        else:
            header = f"Here's your schedule for {date}:"
        
        # Format events
        formatted_events = []
        for event in sorted_events:
            try:
                from app.utils.message_formatter import MessageFormatter
                formatted_event = MessageFormatter.format_event_with_hyperlink(event, include_hyperlink=True)
                formatted_events.append(f"• {formatted_event}")
            except Exception as e:
                logger.warning(f"BackendQueryFormatter: Error formatting schedule event: {e}")
                fallback = self._format_event_fallback(event)
                formatted_events.append(f"• {fallback}")
        
        return f"{header}\n\n" + "\n".join(formatted_events)


# Analysis of what needs to be changed to implement this:

"""
IMPLEMENTATION REQUIREMENTS:

1. MODIFY query_operation.py:
   - Change return value from requires_llm_formatting=True to requires_backend_formatting=True
   - Add query_type field to help backend formatter choose appropriate response style

2. MODIFY routes.py:
   - Replace handle_llm_formatted_query() with handle_backend_formatted_query()
   - Remove LLM formatting prompt and response generation
   - Use BackendQueryFormatter.format_query_response() instead

3. ADD response templates:
   - Create templates for different query types (schedule, find, when, etc.)
   - Handle edge cases (no events, errors, authentication)

4. UPDATE message_formatter.py:
   - Ensure format_event_with_hyperlink() handles all event data structures
   - Add validation for missing fields

5. TESTING:
   - Test all query types with backend formatting
   - Compare responses with current LLM formatting
   - Ensure consistency across different event types

COMPLEXITY ASSESSMENT:
- LOW: Basic event formatting (already exists in MessageFormatter)
- MEDIUM: Natural language response generation
- MEDIUM: Query type detection and appropriate response selection
- HIGH: Edge case handling and error recovery
- MEDIUM: Integration with existing query operation flow

ESTIMATED DEVELOPMENT TIME:
- Backend formatter implementation: 2-3 hours
- Integration with query operation: 1 hour
- Testing and validation: 2-3 hours
- Total: 6-7 hours

RISKS:
- May lose some natural language variation
- Harder to handle complex query contexts
- Requires maintaining formatting logic
- Potential for inconsistent responses

BENEFITS:
- Reduces LLM calls by 50% for queries
- Faster response times
- More predictable formatting
- Lower operational costs
- Better error handling control
"""
