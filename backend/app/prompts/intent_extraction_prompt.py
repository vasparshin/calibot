# Used by NLPAgent to extract event details and intent from user conversation.
INTENT_EXTRACTION_PROMPT = """
You are an intelligent assistant helping users manage their calendar.
Extract event details from the conversation. 

Return a JSON object with the following fields:
- intent: The user's intent (create, update, delete, query)
- event_name: The name/title of the event (can be inferred from the conversation)
- date: The date of the event in YYYY-MM-DD format. If the user refers to a time period such as "next week", "next Monday", or any relative date, infer the specific date(s). For example, if the user says "next Monday", the date should be the next Monday after the current date. If no date is provided, use the current date or the best possible inferred date.
- start_time: The start time in HH:MM format (if provided or inferred from the context)
- end_time: The end time in HH:MM format (if provided or inferred from the context)
- description: Any additional details about the event (inferred from conversation)
- participants: List of people involved (if mentioned or inferred)
- confirmation_needed: Whether user confirmation is needed (true/false)

In the case of vague or ambiguous date references like "next week" or "next Monday":
- For "next week", the date should be set to the beginning of the next week (the first day of the week, e.g., next Monday).
- For "next Monday", infer the actual date of the upcoming Monday, and ensure it's formatted as YYYY-MM-DD.
- If the user asks for an event within a specific range (e.g., "next week" or "this month"), set the date range as needed.

Make sure to carefully extract the date when ambiguous phrases are used, like "next week", "today", "tomorrow", "next month", etc.

Here is the conversation history:
{conversation_history}

Now, extract the event details based on the most recent message.

current date is: {current_date}

JSON:
"""