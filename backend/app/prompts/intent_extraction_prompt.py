# Used by NLPAgent to extract event details and intent from user conversation.
INTENT_EXTRACTION_PROMPT = """You must return a valid JSON object. Copy one of these examples exactly and fill in the values:

For queries about schedule/events:
{{"intent": "query", "date": "2025-08-06", "confirmation_needed": false}}

For creating events:
{{"intent": "create", "event_name": "EVENT_NAME", "date": "2025-08-06", "start_time": "HH:MM", "end_time": "HH:MM", "confirmation_needed": false}}

For confirmations/yes responses:
{{"intent": "query", "confirmation_needed": false}}

User message: {conversation_history}
Date: {current_date}

Return ONLY the JSON object (copy exactly from examples above):"""
