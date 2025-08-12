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

            async def _call_llm():
                # Use clean LLM call for better compatibility
                return await acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=800,  # Increased for more complete responses
                    temperature=0.0,  # Zero temperature for maximum consistency
                )

            response = await _call_llm()

            result = response['choices'][0]['message']['content']
            logger.info(f"Raw LLM response: '{result}'")
            logger.info(f"Response length: {len(result)}")
            logger.info(f"Response type: {type(result)}")
            
            # Try to clean the response if it has extra formatting
            cleaned_result = result.strip()
            if cleaned_result.startswith('```') and cleaned_result.endswith('```'):
                # Remove code block formatting
                lines = cleaned_result.split('\n')
                if len(lines) > 2:
                    cleaned_result = '\n'.join(lines[1:-1])
            
            logger.info(f"Cleaned response: '{cleaned_result}'")
            
            # Primary JSON parsing - expect the LLM to return proper JSON
            try:
                parsed_result = json.loads(cleaned_result)
                logger.info(f"✅ Successfully parsed LLM JSON response: {parsed_result}")
                
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
                
                # Check for specific malformed responses
                if cleaned_result.strip(' "') in ['intent', 'query']:
                    logger.error(f"🚨 LLM returned malformed partial response: '{cleaned_result}'")
                
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
                    
                    # 🔥 ADD CALENDAR EXTRACTION TO THE FALLBACK
                    # Extract calendar move information with improved logging
                    import re
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
                    
                elif any(word in user_lower for word in ['today', 'what', 'plan']):
                    logger.info("Exception fallback: detected query intent")
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                else:
                    logger.info("Exception fallback: defaulting to query intent")
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
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
                return fallback
                
            elif any(word in user_lower for word in ['add', 'create', 'schedule', 'make', 'will have']):
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
            else:
                logger.info("Exception fallback: defaulting to query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
        
        except Exception as e:
            logger.error(f"Error in fallback processing: {str(e)}")
            return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
