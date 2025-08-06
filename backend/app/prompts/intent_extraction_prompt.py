# Used by NLPAgent to extract event details and intent from user conversation.
INTENT_EXTRACTION_PROMPT = """You must return a valid JSON object. Copy one of these examples exactly and fill in the values:

For queries about schedule/events:
{{"intent": "query", "date": "2025-08-06", "confirmation_needed": false}}

For creating ONE event:
{{"intent": "create", "event_name": "EVENT_NAME", "date": "2025-08-06", "start_time": "HH:MM", "end_time": "HH:MM", "confirmation_needed": false}}

For creating MULTIPLE events (when user mentions multiple times like "8am, 10am, 11, 12, 13, 14"):
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "08:00", "end_time": "09:00", "confirmation_needed": false}}
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "10:00", "end_time": "11:00", "confirmation_needed": false}}
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "11:00", "end_time": "12:00", "confirmation_needed": false}}
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "12:00", "end_time": "13:00", "confirmation_needed": false}}
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "13:00", "end_time": "14:00", "confirmation_needed": false}}
{{"intent": "create", "event_name": "lesson", "date": "2025-08-06", "start_time": "14:00", "end_time": "15:00", "confirmation_needed": false}}

For confirmations/yes responses:
{{"intent": "query", "confirmation_needed": false}}

User message: {conversation_history}
Date: {current_date}

Return ONLY the JSON object(s) - one line per event for multiple events:"""
