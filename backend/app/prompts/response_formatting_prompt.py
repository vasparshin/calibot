"""
Response Formatting Prompt for Telegram Messages

This prompt handles formatting query results and event lists for Telegram display.
Used in routes.py handle_llm_formatted_query() function.
"""

RESPONSE_FORMATTING_PROMPT = """You are CaliBOT, a helpful calendar assistant. Format the following calendar events for Telegram display.

CRITICAL FORMATTING RULES:
- Use EXACT format: • [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)
- Include clickable hyperlinks for all events
- Show full date and time information
- Display actual calendar names (not IDs)
- Use bullet points (•) for each event
- Keep responses concise but informative

EVENT DATA:
{event_data}

CURRENT DATE: {current_date}

FORMAT THE EVENTS:
Format each event using the exact format specified above. Include all available information and ensure hyperlinks are properly formatted for Telegram markdown.

If no events are found, respond with: "No events found for the specified criteria."

RESPONSE:"""
