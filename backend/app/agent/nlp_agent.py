from datetime import datetime
from litellm import acompletion
from app.utils.helpers import format_conversation_history
from app.config import LITELLM_MODEL
from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
from app.prompts.relevancy_classifier_prompt import RELEVANCY_CLASSIFIER_PROMPT
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPAgent:
    def __init__(self):
        self.system_prompt = INTENT_EXTRACTION_PROMPT
        self.model = LITELLM_MODEL

    # --------- Internal lightweight fallback parsers ---------
    def _parse_simple_batch_create(self, user_message: str) -> dict | None:
        """Parse simple multi-time creation requests when LLM output is malformed.
        Examples handled:
          "add two lessons today at 5 and 7 pm"
          "create 3 meetings for tomorrow at 9, 10 and 11"
          "schedule two calls in tonya's calendar at 14:00 and 16:00"
          "create two events today one at 5 and one at 7pm"
        Assumptions:
          - Default duration 1 hour per event
          - If meridiem (am/pm) supplied on last time, apply to earlier times lacking one
          - If no meridiem provided and hour < 8 -> assume AM else PM
        Returns batch_create intent dict or None.
        """
        import re
        text = user_message.lower()
        # Quick gate: must mention create/add/schedule (including 'lessons' verbs) and at least two time tokens
        if not any(k in text for k in ["add", "create", "schedule", "lesson", "meet", "call"]):
            return None
        if len(re.findall(r"\b(\d{1,2})(?::\d{2})?\s*(?:am|pm)?\b", text)) < 2:
            return None
        # (Optional) Count detection retained for potential future validation but not strictly required now
        # We intentionally avoid using count directly to stay permissive even if user says "a couple" etc.
        num_map = {"two":2, "three":3, "four":4, "five":5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10}
        for word, val in num_map.items():
            if re.search(rf"\b{word}\b", text):
                break  # Not used presently
        # Event name: word after number or explicit quoted name
        event_name = None
        m_quote = re.search(r'"([a-zA-Z ]{2,40})"', user_message)
        if m_quote:
            event_name = m_quote.group(1).strip().lower()
        if not event_name:
            m_en = re.search(r"(?:add|create|schedule)\s+(?:two|three|four|five|six|seven|eight|nine|ten|\d+)\s+([a-zA-Z]+)", text)
            if m_en:
                event_name = m_en.group(1).lower()
        if event_name and event_name.endswith('s'):
            # naive singularization
            event_name = event_name[:-1]
        if not event_name:
            event_name = "event"
        # Date detection
        from datetime import datetime, timedelta
        if "tomorrow" in text:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date = datetime.now().strftime("%Y-%m-%d")
        # Calendar detection (tonya's calendar etc.)
        calendar_name = None
        cal_match = re.search(r"(tonya'?s calendar)", text)
        if cal_match:
            calendar_name = cal_match.group(1)
        # Times extraction
        time_tokens = re.findall(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
        if not time_tokens:
            return None
        # Determine global meridiem if only last has it
        last_meridiem = None
        for h, m, ap in time_tokens:
            if ap:
                last_meridiem = ap
        events = []
        for h, m, ap in time_tokens:
            hour = int(h)
            minute = int(m) if m else 0
            meridiem = ap or last_meridiem
            if not meridiem:
                # Improved assumption: times 1-11 default to AM (common user expectation for bare morning hours)
                # Only treat 12 or values >= 13 as PM when unspecified.
                if 1 <= hour <= 11:
                    meridiem = 'am'
                else:
                    meridiem = 'pm'
            # Convert to 24h
            hour24 = hour % 12
            if meridiem == 'pm':
                hour24 += 12
            start_hour = f"{hour24:02d}:{minute:02d}"
            # Default 1 hour duration
            from datetime import datetime as _dt, timedelta as _td
            try:
                st = _dt.strptime(start_hour, "%H:%M")
                et = st + _td(hours=1)
                end_hour = et.strftime("%H:%M")
            except Exception:
                end_hour = start_hour
            events.append({"start_time": start_hour, "end_time": end_hour})
        # Deduplicate times
        seen = set(); dedup=[]
        for ev in events:
            if ev['start_time'] in seen: continue
            seen.add(ev['start_time']); dedup.append(ev)
        if len(dedup) < 2:
            return None
        return {
            "intent": "batch_create",
            "event_name": event_name,
            "date": date,
            "events": dedup,
            "calendar_name": calendar_name,
            "confirmation_needed": False
        }

        
    async def check_relevancy(self, user_message: str, history: list) -> dict:
        """Check if the user message is relevant to calendar tasks."""
        
        system_prompt = RELEVANCY_CLASSIFIER_PROMPT

        formatted_history = format_conversation_history(history)
        
        response = await acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt.format(conversation_history=formatted_history)},
                {"role": "user", "content": f"User message: {user_message}"}
            ],
        )

        try:
            relevancy_result = response["choices"][0]["message"]["content"]
            return json.loads(relevancy_result)
        except Exception as e:
            return {"relevant": False, "reason": "Failed to process response"}


    async def extract_intent(self, user_message, conversation_history):
        """Process user message and extract calendar intent and details"""
        try:
            formatted_history = format_conversation_history(conversation_history)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")

            system_message = self.system_prompt.format(conversation_history=formatted_history, current_date=current_datetime)

            # 🔍 COMPREHENSIVE LLM DEBUGGING - Log everything being sent to the model
            logger.info(f"🔍 LLM INPUT DEBUG - User message: '{user_message}'")
            logger.info(f"🔍 LLM INPUT DEBUG - Conversation history length: {len(conversation_history)} messages")
            logger.info(f"🔍 LLM INPUT DEBUG - Formatted history preview: {formatted_history[:300]}{'...' if len(formatted_history) > 300 else ''}")
            logger.info(f"🔍 LLM INPUT DEBUG - Current datetime: {current_datetime}")
            logger.info(f"🔍 LLM INPUT DEBUG - System message length: {len(system_message)} chars")
            logger.info(f"🔍 LLM INPUT DEBUG - System message preview: {system_message[:500]}{'...' if len(system_message) > 500 else ''}")

            async def _call_llm():
                # Use clean LLM call for better compatibility
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                # Log the exact messages being sent
                logger.info(f"🔍 LLM CALL DEBUG - Messages being sent to {self.model}:")
                for i, msg in enumerate(messages):
                    logger.info(f"🔍 Message {i+1} ({msg['role']}): {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
                
                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    max_tokens=200,  # Reduced for focused JSON responses
                    temperature=0.1,  # Tiny bit of randomness to avoid getting stuck
                )
                
                # Log the raw response structure
                logger.info(f"🔍 LLM RESPONSE DEBUG - Raw response type: {type(response)}")
                logger.info(f"🔍 LLM RESPONSE DEBUG - Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                if isinstance(response, dict) and 'choices' in response:
                    logger.info(f"🔍 LLM RESPONSE DEBUG - Choices length: {len(response['choices'])}")
                    if response['choices']:
                        choice = response['choices'][0]
                        logger.info(f"🔍 LLM RESPONSE DEBUG - Choice keys: {list(choice.keys())}")
                        if 'message' in choice:
                            message = choice['message']
                            logger.info(f"🔍 LLM RESPONSE DEBUG - Message keys: {list(message.keys())}")
                            content = message.get('content', '')
                            logger.info(f"🔍 LLM RESPONSE DEBUG - Raw content: '{content}'")
                
                return response

            response = await _call_llm()

            result = response['choices'][0]['message']['content']
            logger.info(f"Raw LLM response: '{result}'")
            logger.info(f"Response length: {len(result)}")
            logger.info(f"Response type: {type(result)}")
            
            # Clean the response more aggressively
            cleaned_result = result.strip()
            
            # Remove any markdown formatting
            if cleaned_result.startswith('```') and cleaned_result.endswith('```'):
                lines = cleaned_result.split('\n')
                if len(lines) > 2:
                    cleaned_result = '\n'.join(lines[1:-1])
            
            # Remove json tags if present
            if cleaned_result.startswith('```json') and cleaned_result.endswith('```'):
                cleaned_result = cleaned_result[7:-3].strip()
            
            # Remove extra quotes if the entire response is quoted
            if cleaned_result.startswith('"') and cleaned_result.endswith('"') and cleaned_result.count('"') == 2:
                cleaned_result = cleaned_result[1:-1]
            
            logger.info(f"Cleaned response: '{cleaned_result}'")
            
            # Handle malformed partial responses immediately
            if cleaned_result.strip(' "') in ['intent', 'query', 'create', 'delete', 'update']:
                logger.error(f"🚨 LLM returned malformed partial response: '{cleaned_result}' - using fallback")
                # Determine intent based on user message
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['today', 'what', 'plan', 'schedule', 'agenda', 'list', 'show']):
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                elif any(word in user_lower for word in ['add', 'create', 'make']):
                    return {"intent": "create", "event_name": "event", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                elif any(word in user_lower for word in ['delete', 'remove']):
                    return {"intent": "delete", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                elif any(word in user_lower for word in ['move', 'update', 'change']):
                    return {"intent": "update", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                else:
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            # Primary JSON parsing - expect the LLM to return proper JSON
            try:
                parsed_result = json.loads(cleaned_result)
                logger.info(f"✅ Successfully parsed LLM JSON response: {parsed_result}")
                
                # Debug logging for multi-event target extraction
                if parsed_result.get('intent') in ['update', 'delete'] and 'target' in parsed_result:
                    logger.info(f"🎯 Target field extracted: '{parsed_result['target']}'")
                    
                    # CRITICAL DEBUG for "last 3" issues
                    if "last" in str(parsed_result['target']).lower():
                        logger.info(f"🚨 LAST TARGET DEBUG - Full JSON: {parsed_result}")
                        logger.info(f"🚨 LAST TARGET DEBUG - Target value: '{parsed_result['target']}'")
                        logger.info(f"🚨 LAST TARGET DEBUG - Contains number? {'3' in str(parsed_result['target'])}")
                    
                    if 'event_name' in parsed_result:
                        logger.info(f"📅 Event name: '{parsed_result['event_name']}'")
                    if 'date' in parsed_result:
                        logger.info(f"📆 Date: '{parsed_result['date']}'")
                    if 'new_date' in parsed_result:
                        logger.info(f"📆 New date: '{parsed_result['new_date']}'")
                    if 'time_shift' in parsed_result:
                        logger.info(f"⏰ Time shift: '{parsed_result['time_shift']}'")
                
                # Validate basic structure
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-dict JSON: {type(parsed_result)} - {parsed_result}")
                    raise ValueError("Non-dict response")
                
                if 'intent' not in parsed_result:
                    logger.error(f"LLM JSON missing 'intent' field: {parsed_result}")
                    raise ValueError("Missing intent field")
                
                # Success - return the properly parsed result
                return parsed_result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"LLM JSON parsing failed: {e}")
                logger.error(f"Raw response that failed: '{result}'")
                logger.error(f"Cleaned response that failed: '{cleaned_result}'")
                
                # Secondary attempt: try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
                if json_match:
                    try:
                        secondary_result = json.loads(json_match.group())
                        logger.info(f"✅ Secondary JSON extraction successful: {secondary_result}")
                        return secondary_result
                    except json.JSONDecodeError:
                        logger.error("Secondary JSON extraction also failed")
                
                # If all JSON parsing fails, use intelligent fallback
                # Enhanced fallback based on user message keywords
                user_lower = user_message.lower()
                # Attempt structured batch create parse first
                batch_parsed = self._parse_simple_batch_create(user_message)
                if batch_parsed:
                    logger.info(f"Rule-based batch_create fallback parsed: {batch_parsed}")
                    return batch_parsed
                
                if any(word in user_lower for word in ['delete', 'remove']):
                    logger.info("Exception fallback: detected delete intent")
                    fallback = {"intent": "delete", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                    if "lesson" in user_lower:
                        fallback["event_name"] = "lesson"
                    elif "event" in user_lower:
                        fallback["event_name"] = "event"
                    # Extract target
                    if "last" in user_lower:
                        fallback["target"] = "last"
                    elif "first" in user_lower:
                        fallback["target"] = "first"
                    elif "2nd" in user_lower or "second" in user_lower:
                        fallback["target"] = "2nd"
                    elif "3rd" in user_lower or "third" in user_lower:
                        fallback["target"] = "3rd"
                    return fallback
                    
                elif any(word in user_lower for word in ['move', 'update', 'change']):
                    logger.info("Exception fallback: detected update intent")
                    fallback = {"intent": "update", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                    if "lesson" in user_lower:
                        fallback["event_name"] = "lesson"
                    elif "event" in user_lower:
                        fallback["event_name"] = "event"
                    
                    # Extract target
                    if "last" in user_lower:
                        fallback["target"] = "last"
                    elif "first" in user_lower:
                        fallback["target"] = "first"
                    elif "2nd" in user_lower or "second" in user_lower:
                        fallback["target"] = "2nd"
                    elif "3rd" in user_lower or "third" in user_lower:
                        fallback["target"] = "3rd"
                    
                    # CRITICAL FIX: Extract time information for direct time updates
                    import re
                    
                    # Extract new time if specified (e.g., "change to 7pm", "move to 3:30")
                    time_patterns = [
                        r'to (\d{1,2}):(\d{2})\s*(am|pm)?',       # "to 7:30pm"
                        r'to (\d{1,2})\s*(am|pm)',                # "to 7pm"
                        r'at (\d{1,2}):(\d{2})\s*(am|pm)?',       # "at 7:30pm"
                        r'at (\d{1,2})\s*(am|pm)',                # "at 7pm"
                        r'(\d{1,2}):(\d{2})\s*(am|pm)',           # "7:30pm"
                        r'(\d{1,2})\s*(am|pm)',                   # "7pm"
                    ]
                    
                    new_start_time = None
                    for pattern in time_patterns:
                        match = re.search(pattern, user_lower)
                        if match:
                            if len(match.groups()) == 3:  # Hour, minute, am/pm
                                hour, minute, meridiem = match.groups()
                                minute = minute or "00"
                            elif len(match.groups()) == 2:  # Hour, am/pm
                                hour, meridiem = match.groups()
                                minute = "00"
                            else:
                                continue
                            
                            # Convert to 24-hour format
                            hour = int(hour)
                            if meridiem and meridiem.lower() == 'pm' and hour != 12:
                                hour += 12
                            elif meridiem and meridiem.lower() == 'am' and hour == 12:
                                hour = 0
                            elif not meridiem:
                                # No meridiem specified - use context
                                if hour < 8:  # Assume PM for hours 1-7
                                    hour += 12
                            
                            new_start_time = f"{hour:02d}:{minute}"
                            logger.error(f"🔥 ✅ EXTRACTED TIME: '{new_start_time}' from '{user_message}'")
                            break
                    
                    if new_start_time:
                        fallback["new_start_time"] = new_start_time
                        # Calculate end time (assume 1 hour duration)
                        start_hour, start_minute = map(int, new_start_time.split(':'))
                        end_hour = start_hour + 1
                        if end_hour >= 24:
                            end_hour = 23
                            start_minute = 59
                        fallback["new_end_time"] = f"{end_hour:02d}:{start_minute:02d}"
                        logger.error(f"🔥 ✅ CALCULATED END TIME: '{fallback['new_end_time']}' (1 hour duration)")
                    
                    # Extract calendar move information
                    # Extract calendar move information with improved logging
                    logger.error(f"🔥 CRITICAL DEBUG: Starting calendar extraction for message: '{user_message}'")
                    logger.error(f"🔥 CRITICAL DEBUG: Lowercase message: '{user_lower}'")
                    
                    # Try multiple patterns for calendar extraction
                    calendar_patterns = [
                        r'to calendar ["\']([^"\']+)["\']',  # 'to calendar "Name"'
                        r'to calendar ([^\s]+)',             # 'to calendar Name'  
                        r'calendar ["\']([^"\']+)["\']',     # 'calendar "Name"'
                        r'move.*to ([A-Z][a-zA-Z]+)',        # 'move to Name'
                        r'to\s+["\']([^"\']+)["\']',         # 'to "Name"' (simplified)
                        r'move.*["\']([^"\']+)["\']',        # any quoted name after move
                    ]
                    
                    target_calendar = None
                    for i, pattern in enumerate(calendar_patterns):
                        logger.error(f"🔥 CRITICAL DEBUG: Testing pattern {i+1}: '{pattern}'")
                        calendar_match = re.search(pattern, user_lower)
                        if calendar_match:
                            target_calendar = calendar_match.group(1).strip()
                            logger.error(f"🔥 ✅ CRITICAL DEBUG: Calendar pattern '{pattern}' matched: '{target_calendar}'")
                            break
                        else:
                            logger.error(f"🔥 ❌ CRITICAL DEBUG: Pattern '{pattern}' did not match")
                    
                    if target_calendar:
                        fallback["calendar_name"] = target_calendar.title()  # Capitalize properly
                        logger.error(f"🔥 ✅ CRITICAL DEBUG: EXTRACTED target calendar for move: '{target_calendar.title()}' from message: '{user_message}'")
                    else:
                        logger.error(f"🔥 ❌ CRITICAL DEBUG: No calendar extraction from primary patterns for message: '{user_message}' (lowercase: '{user_lower}')")
                        # Try case-insensitive search for known calendar names
                        known_calendars = ['tonya', 'personal', 'work', 'family']
                        for cal_name in known_calendars:
                            if cal_name in user_lower:
                                fallback["calendar_name"] = cal_name.title()
                                logger.error(f"🔥 ✅ CRITICAL DEBUG: Found known calendar name '{cal_name}' -> '{cal_name.title()}' in message")
                                target_calendar = cal_name.title()
                                break
                        
                        if not target_calendar:
                            logger.error(f"🔥 ❌ CRITICAL DEBUG: FAILED to extract calendar name from: '{user_message}'")
                    
                    logger.error(f"🔥 📋 CRITICAL DEBUG: Fallback result for update BEFORE return: {fallback}")
                    return fallback
                    
                elif any(word in user_lower for word in ['today', 'what', 'plan', 'schedule', 'agenda', 'list', 'show']):
                    logger.info("Exception fallback: detected query intent")
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                else:
                    logger.info("Exception fallback: detected create intent")
                    return {"intent": "create", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False, "event_name": "event"}
            
            # SUCCESS: LLM returned valid JSON
            logger.info(f"✅ Successfully parsed LLM JSON response: {parsed_result}")
            
            # Validate JSON structure
            if not isinstance(parsed_result, dict):
                logger.error(f"LLM returned non-dict JSON: {type(parsed_result)} - falling back")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            if "intent" not in parsed_result:
                logger.error(f"LLM JSON missing 'intent' field: {parsed_result} - falling back")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            # Add calendar extraction for update intents if missing but mentioned in message
            if parsed_result.get("intent") == "update" and "calendar_name" not in parsed_result:
                user_lower = user_message.lower()
                if any(cal_word in user_lower for cal_word in ['calendar', 'tonya', 'personal']):
                    import re
                    calendar_patterns = [
                        r'to calendar ["\']([^"\']+)["\']',
                        r'calendar ["\']([^"\']+)["\']',
                    ]
                    for pattern in calendar_patterns:
                        match = re.search(pattern, user_lower)
                        if match:
                            parsed_result["calendar_name"] = match.group(1).title()
                            logger.info(f"✅ Added missing calendar_name to LLM result: {match.group(1).title()}")
                            break
            
            return parsed_result

        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            logger.error(f"User message was: '{user_message}'")
            
            # Intelligent fallback based on user message keywords
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ['move', 'update', 'change']):
                logger.info("Exception fallback: detected update intent")
                fallback = {"intent": "update", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                if "lesson" in user_lower:
                    fallback["event_name"] = "lesson"
                elif "event" in user_lower:
                    fallback["event_name"] = "event"
                # Extract target
                if "last" in user_lower:
                    fallback["target"] = "last"
                elif "first" in user_lower:
                    fallback["target"] = "first"
                elif "all" in user_lower or "lessons" in user_lower:
                    fallback["target"] = "all"
                elif "2nd" in user_lower or "second" in user_lower:
                    fallback["target"] = "2nd"
                elif "3rd" in user_lower or "third" in user_lower:
                    fallback["target"] = "3rd"
                
                # Extract calendar move information
                import re
                logger.error(f"🔥 CRITICAL DEBUG: Starting calendar extraction for message: '{user_message}'")
                
                calendar_patterns = [
                    r'to calendar ["\']([^"\']+)["\']',  # 'to calendar "Name"'
                    r'to calendar ([^\s]+)',             # 'to calendar Name'  
                    r'calendar ["\']([^"\']+)["\']',     # 'calendar "Name"'
                    r'move.*to ([A-Z][a-zA-Z]+)',        # 'move to Name'
                    r'to\s+["\']([^"\']+)["\']',         # 'to "Name"' (simplified)
                    r'move.*["\']([^"\']+)["\']',        # any quoted name after move
                ]
                
                target_calendar = None
                for i, pattern in enumerate(calendar_patterns):
                    calendar_match = re.search(pattern, user_lower)
                    if calendar_match:
                        target_calendar = calendar_match.group(1).strip()
                        logger.error(f"🔥 ✅ CRITICAL DEBUG: Calendar pattern '{pattern}' matched: '{target_calendar}'")
                        break
                
                if target_calendar:
                    fallback["calendar_name"] = target_calendar.title()
                    logger.error(f"🔥 ✅ CRITICAL DEBUG: EXTRACTED target calendar: '{target_calendar.title()}'")
                else:
                    # Try known calendar names
                    known_calendars = ['tonya', 'personal', 'work', 'family']
                    for cal_name in known_calendars:
                        if cal_name in user_lower:
                            fallback["calendar_name"] = cal_name.title()
                            logger.error(f"🔥 ✅ CRITICAL DEBUG: Found known calendar: '{cal_name.title()}'")
                            break
                
                logger.error(f"🔥 📋 CRITICAL DEBUG: Final fallback result: {fallback}")
                
                # CRITICAL FIX: Add count extraction right before returning (to avoid being overridden)
                import re
                logger.error(f"🔥 🔢 FINAL COUNT EXTRACTION: Starting for '{user_message}'")
                
                # Extract count patterns (e.g., "last 3", "first 2", "next 5")
                count_patterns = [
                    r'last (\d+)',           # "last 3 lessons"
                    r'first (\d+)',          # "first 2 events"
                    r'next (\d+)',           # "next 5 meetings"
                    r'(\d+) last',           # "3 last lessons"
                    r'(\d+) first',          # "2 first events"
                ]
                
                # Also check for written numbers
                written_numbers = {
                    'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
                    'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                }
                
                count = 1  # Default to 1 event
                logger.error(f"🔥 🔢 Testing count patterns against: '{user_lower}'")
                
                for pattern in count_patterns:
                    match = re.search(pattern, user_lower)
                    if match:
                        count = int(match.group(1))
                        logger.error(f"🔥 ✅ EXTRACTED COUNT: {count} from pattern '{pattern}' in '{user_message}'")
                        break
                    else:
                        logger.error(f"🔥 🔢 Pattern '{pattern}' did not match")
                
                # Check for written numbers if no digit found
                if count == 1:
                    logger.error(f"🔥 🔢 No numeric count found, checking written numbers")
                    for word, num in written_numbers.items():
                        if f'last {word}' in user_lower or f'{word} last' in user_lower:
                            count = num
                            logger.error(f"🔥 ✅ EXTRACTED COUNT: {count} from written number '{word}' in '{user_message}'")
                            break
                
                logger.error(f"🔥 🔢 Final count value: {count}")
                
                if count > 1:
                    fallback["count"] = count
                    logger.error(f"🔥 ✅ ADDED COUNT TO FALLBACK: {count}")
                    
                    # Also extract time_shift if count > 1
                    time_shift_patterns = [
                        r'(\d+)\s*hr?\s*(later|late|forward|ahead)',          # "1 hr later", "1 hr late"
                        r'(\d+)\s*hour?s?\s*(later|late|forward|ahead)',      # "1 hour later"
                        r'(\d+)\s*min(?:ute)?s?\s*(later|late|forward|ahead)', # "30 minutes later"
                        r'(\d+)\s*hr?\s*(earlier|back|before)',               # "1 hr earlier"
                        r'(\d+)\s*hour?s?\s*(earlier|back|before)',           # "1 hour earlier"
                        r'(\d+)\s*min(?:ute)?s?\s*(earlier|back|before)',     # "30 minutes earlier"
                    ]
                    
                    time_shift = None
                    for pattern in time_shift_patterns:
                        match = re.search(pattern, user_lower)
                        if match:
                            amount = int(match.group(1))
                            direction = match.group(2) if len(match.groups()) > 1 else 'later'
                            if direction in ['earlier', 'back', 'before']:
                                amount = -amount
                            
                            # Determine unit
                            if 'hr' in pattern or 'hour' in pattern:
                                time_shift = f"{amount} hour{'s' if abs(amount) != 1 else ''}"
                            else:
                                time_shift = f"{amount} minute{'s' if abs(amount) != 1 else ''}"
                            
                            logger.error(f"🔥 ✅ EXTRACTED TIME SHIFT: '{time_shift}' from pattern '{pattern}' in '{user_message}'")
                            break
                    
                    if time_shift:
                        fallback["time_shift"] = time_shift
                        logger.error(f"🔥 ✅ ADDED TIME SHIFT TO FALLBACK: {time_shift}")
                else:
                    logger.error(f"🔥 🔢 Count is 1, not adding to fallback")
                
                logger.error(f"🔥 📋 FINAL ENHANCED FALLBACK RESULT: {fallback}")
                return fallback
                
            elif any(word in user_lower for word in ['today', 'what', 'plan', 'schedule', 'agenda', 'list', 'show']):
                logger.info("Exception fallback: detected query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            elif any(word in user_lower for word in ['add', 'create', 'make', 'will have']):
                logger.info("Exception fallback: detected create intent")
                
                # Check for batch creation (multiple times mentioned)
                import re
                time_patterns = [r'\d{1,2}\s*pm', r'\d{1,2}\s*am', r'\d{1,2}:\d{2}']
                times_found = []
                for pattern in time_patterns:
                    times_found.extend(re.findall(pattern, user_lower))
                
                # Also look for bare numbers in context like "at 2, 4, 5 and 6pm"
                bare_numbers = re.findall(r'at\s+(\d+)(?:,\s*(\d+))*(?:\s+and\s+(\d+))?(?:pm|am)', user_lower)
                if bare_numbers:
                    # Extract all numbers from the pattern
                    numbers_in_sequence = re.findall(r'\b(\d+)\b(?=.*(?:pm|am))', user_lower)
                    if len(numbers_in_sequence) > 1:
                        # Add pm/am suffix based on the ending
                        suffix = 'pm' if 'pm' in user_lower else 'am'
                        for num in numbers_in_sequence:
                            times_found.append(f"{num}{suffix}")
                
                logger.error(f"🔥 TIME DEBUG: Found times: {times_found}")
                
                if len(times_found) > 1:
                    # Batch create
                    logger.info(f"Exception fallback: detected batch create with {len(times_found)} times")
                    fallback = {"intent": "batch_create", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                    
                    # Extract date - check for tomorrow
                    if "tomorrow" in user_lower:
                        from datetime import timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        fallback["date"] = tomorrow.strftime("%Y-%m-%d")
                    
                    # Extract event name
                    if "lesson" in user_lower:
                        fallback["event_name"] = "lesson"
                    elif "meeting" in user_lower:
                        fallback["event_name"] = "meeting"
                    else:
                        fallback["event_name"] = "event"
                    
                    # Try to extract calendar name
                    if "tonya" in user_lower:
                        fallback["calendar_name"] = "Tonya"
                    elif "personal" in user_lower:
                        fallback["calendar_name"] = "Personal"
                    
                    # Parse times from message
                    events = []
                    for time_str in times_found:
                        # Convert time to 24h format
                        time_clean = time_str.replace(' ', '')
                        if 'pm' in time_clean and not time_clean.startswith('12'):
                            hour = int(time_clean.split('pm')[0]) + 12
                            start_time = f"{hour:02d}:00"
                            end_time = f"{hour+1:02d}:00"
                        elif 'am' in time_clean:
                            hour = int(time_clean.split('am')[0])
                            if hour == 12:
                                hour = 0
                            start_time = f"{hour:02d}:00"
                            end_time = f"{hour+1:02d}:00"
                        else:
                            # Handle other formats like "2" -> assume PM for afternoon times
                            try:
                                hour = int(time_clean)
                                if hour >= 2 and hour <= 11:  # 2-11 likely PM
                                    hour += 12
                                start_time = f"{hour:02d}:00"
                                end_time = f"{hour+1:02d}:00"
                            except:
                                continue
                        
                        events.append({
                            "start_time": start_time,
                            "end_time": end_time
                        })
                    
                    if events:
                        fallback["events"] = events
                    
                    logger.error(f"🔥 📋 CRITICAL DEBUG: Batch create fallback result: {fallback}")
                    return fallback
                else:
                    # Single create
                    fallback = {"intent": "create", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                    
                    # Extract date
                    if "tomorrow" in user_lower:
                        from datetime import timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        fallback["date"] = tomorrow.strftime("%Y-%m-%d")
                    
                    # Extract event name
                    if "lesson" in user_lower:
                        fallback["event_name"] = "lesson"
                    elif "meeting" in user_lower:
                        fallback["event_name"] = "meeting"
                    else:
                        fallback["event_name"] = "event"
                    
                    # Extract time if present
                    if times_found:
                        time_str = times_found[0].replace(' ', '')
                        if 'pm' in time_str and not time_str.startswith('12'):
                            hour = int(time_str.split('pm')[0]) + 12
                            fallback["start_time"] = f"{hour:02d}:00"
                            fallback["end_time"] = f"{hour+1:02d}:00"
                        elif 'am' in time_str:
                            hour = int(time_str.split('am')[0])
                            if hour == 12:
                                hour = 0
                            fallback["start_time"] = f"{hour:02d}:00"
                            fallback["end_time"] = f"{hour+1:02d}:00"
                    
                    # Try to extract calendar name
                    if "tonya" in user_lower:
                        fallback["calendar_name"] = "Tonya"
                    elif "personal" in user_lower:
                        fallback["calendar_name"] = "Personal"
                    
                    return fallback
                    
            elif any(word in user_lower for word in ['delete', 'remove']):
                logger.info("Exception fallback: detected delete intent")
                fallback = {"intent": "delete", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                if "lesson" in user_lower:
                    fallback["event_name"] = "lesson"
                elif "event" in user_lower:
                    fallback["event_name"] = "event"
                return fallback
            elif any(word in user_lower for word in ['today', 'what', 'plan', 'schedule', 'agenda', 'list', 'show']):
                logger.info("Exception fallback: detected query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            else:
                logger.info("Exception fallback: defaulting to query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
        
        except Exception as e:
            logger.error(f"Error in fallback processing: {str(e)}")
            return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
