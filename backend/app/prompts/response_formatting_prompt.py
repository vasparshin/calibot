# Used for formatting Telegram responses to users
RESPONSE_FORMATTING_PROMPT = """You received this query from the user: "{original_message}"

I retrieved the following calendar data:
{events_data}

Query parameters used: {query_params}

Based on the user's request and the retrieved data, provide a natural, helpful response.
If no events were found, explain this clearly and suggest alternatives if appropriate.

CRITICAL: Format ALL events using this EXACT format (MANDATORY):
• [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)

Examples:
• [Math Lesson](https://calendar.google.com/calendar/event?eid=abc123) on Monday, September 02, 2025 at 09:00 AM - 10:00 AM (Personal)
• [Team Meeting](https://calendar.google.com/calendar/event?eid=def456) on Tuesday, September 03, 2025 at 02:00 PM - 03:00 PM (Work)

RULES:
- ALWAYS use bullet points (•)
- ALWAYS create hyperlinks with [Event Name](link)
- ALWAYS use full date format: Day, Month DD, YYYY
- ALWAYS use 12-hour time format with AM/PM
- ALWAYS include calendar name in parentheses
- Use the Link field from the event data for hyperlinks

Return only the response message that should be sent to the user."""
