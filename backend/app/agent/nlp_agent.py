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
                return await acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=500
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
            
            # IMMEDIATE check for known bad responses before any processing
            if (cleaned_result.strip() == '"intent"' or cleaned_result.strip() == '"query"' or 
                cleaned_result.strip() == 'intent' or cleaned_result.strip() == 'query'):
                logger.error(f"DETECTED MALFORMED LLM RESPONSE: '{cleaned_result}' - using intelligent fallback")
                # Enhanced fallback based on user message keywords
                user_lower = user_message.lower()
                # Attempt structured batch create parse first
                batch_parsed = self._parse_simple_batch_create(user_message)
                if batch_parsed:
                    logger.info(f"Rule-based batch_create fallback parsed: {batch_parsed}")
                    return batch_parsed
                
                if any(word in user_lower for word in ['delete', 'remove']):
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
                    # Extract time shifts and date changes
                    if 'forward' in user_lower and ('hour' in user_lower or 'hr' in user_lower):
                        fallback["time_shift"] = "1 hour"
                    if 'tomorrow' in user_lower:
                        from datetime import timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        fallback["new_date"] = tomorrow.strftime("%Y-%m-%d")
                    
                    # Extract calendar move information
                    import re
                    calendar_match = re.search(r'to calendar ["\']([^"\']+)["\']', user_lower)
                    if calendar_match:
                        target_calendar = calendar_match.group(1).strip()
                        fallback["calendar_name"] = target_calendar
                        logger.info(f"Extracted target calendar for move: {target_calendar}")
                    
                    return fallback
                    
                elif any(word in user_lower for word in ['add', 'create', 'make', 'schedule']):
                    fallback = {"intent": "create", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                    if "lesson" in user_lower:
                        fallback["event_name"] = "lesson"
                    elif "meeting" in user_lower:
                        fallback["event_name"] = "meeting"
                    elif "event" in user_lower:
                        fallback["event_name"] = "event"
                    else:
                        fallback["event_name"] = "New Event"
                    
                    # Extract time information
                    import re
                    time_match = re.search(r'(\d{1,2})\s*(pm|am|:\d{2})', user_lower)
                    if time_match:
                        time_str = time_match.group(0)
                        if ':' not in time_str:
                            hour = int(time_match.group(1))
                            meridiem = time_match.group(2) if time_match.group(2) in ['am', 'pm'] else 'am'
                            if meridiem == 'pm' and hour != 12:
                                hour += 12
                            elif meridiem == 'am' and hour == 12:
                                hour = 0
                            fallback["start_time"] = f"{hour:02d}:00"
                            fallback["end_time"] = f"{hour+1:02d}:00"
                        
                    # Extract calendar name
                    calendar_match = re.search(r'(?:in|to)\s+(?:calendar\s+)?["\']?([^"\']+)["\']?(?:\s+calendar)?', user_lower)
                    if calendar_match:
                        fallback["calendar_name"] = calendar_match.group(1).strip()
                    
                    return fallback
                    
                elif any(word in user_lower for word in ['today', 'what', 'plan']):
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                else:
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            # Enhanced detection for invalid LLM responses
            is_invalid_response = (
                len(cleaned_result) < 20 or 
                not cleaned_result.startswith('{') or 
                cleaned_result.strip() in ['"intent"', 'intent', '"query"', 'query']
            )
            
            if is_invalid_response:
                logger.error("Primary LLM response invalid – attempting one regeneration before fallback")
                regen = await _call_llm()
                regen_result = regen['choices'][0]['message']['content']
                logger.info(f"Regenerated raw LLM response: '{regen_result}'")
                cleaned_regen = regen_result.strip()
                if cleaned_regen.startswith('```') and cleaned_regen.endswith('```'):
                    lines_r = cleaned_regen.split('\n')
                    if len(lines_r) > 2:
                        cleaned_regen = '\n'.join(lines_r[1:-1])
                if (len(cleaned_regen) >= 20 and cleaned_regen.startswith('{') and cleaned_regen not in ['"intent"','intent','"query"','query']):
                    try:
                        regen_json = json.loads(cleaned_regen)
                        if isinstance(regen_json, dict) and 'intent' in regen_json:
                            logger.info("Regeneration successful – using regenerated JSON")
                            return regen_json
                    except Exception as _e:
                        logger.error(f"Regenerated parse failed: {_e}")
                # If regeneration also failed, attempt rule-based batch parsing before generic fallback
                batch_parsed = self._parse_simple_batch_create(user_message)
                if batch_parsed:
                    logger.info(f"Rule-based batch_create after regen failure: {batch_parsed}")
                    return batch_parsed
                cleaned_result = cleaned_regen  # continue downstream with latest attempt
            
            # Try to parse as single JSON first
            try:
                parsed_result = json.loads(cleaned_result)
                logger.info(f"JSON parsing successful, result type: {type(parsed_result)}")
                
                # Ensure the parsed result is actually a dict/object, not just a string
                # Basic required schema: must have 'intent'; if intent is create/update/delete expect confirmation_needed key (we'll add if missing)
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-object JSON: {type(parsed_result)} - {parsed_result}")
                    # This is likely the "intent" or "query" string response - trigger fallback
                    logger.error(f"Detected string response instead of JSON object - triggering intelligent fallback")
                    parsed_result = None
                else:
                    if 'intent' not in parsed_result:
                        logger.error("Parsed JSON missing 'intent' key – invalid, will fallback")
                    else:
                        # Normalize minimal schema
                        if parsed_result['intent'] in ['create','update','delete'] and 'confirmation_needed' not in parsed_result:
                            parsed_result['confirmation_needed'] = True
                        if parsed_result['intent'] == 'query' and 'confirmation_needed' not in parsed_result:
                            parsed_result['confirmation_needed'] = False
                        logger.info(f"Valid JSON dict received after schema normalization: {parsed_result}")
                        return parsed_result
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing failed: {json_error}")
                logger.error(f"Raw content that failed: '{cleaned_result}'")
                # Check if this is the problematic "intent" or "query" response
                if cleaned_result.strip(' "') in ['intent', 'query']:
                    logger.error(f"Detected malformed LLM response: '{cleaned_result}' - using intelligent fallback")
                parsed_result = None
            except Exception as unexpected_error:
                logger.error(f"Unexpected error in JSON parsing: {unexpected_error}")
                parsed_result = None
                
            # If single JSON parsing failed or returned non-dict, try multiple JSON
            if parsed_result is None:
                # If single JSON fails, try to parse multiple JSON objects (batch events)
                logger.info("Single JSON parsing failed, attempting multiple JSON objects parsing")
                
                # Split by lines and try to parse each as JSON
                lines = [line.strip() for line in cleaned_result.split('\n') if line.strip()]
                json_objects = []
                
                for line in lines:
                    try:
                        json_obj = json.loads(line)
                        json_objects.append(json_obj)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse line as JSON: {line}")
                        continue
                
                if json_objects:
                    logger.info(f"Successfully parsed {len(json_objects)} JSON objects for batch processing")
                    # Return the objects as a batch format
                    return {
                        "intent": "batch_create",
                        "events": json_objects,
                        "confirmation_needed": False
                    }
                
                # If nothing worked, attempt rule-based batch parsing before intelligent fallback
                logger.error(f"Multiple JSON parsing also failed, using intelligent fallback")
                logger.error(f"Raw response content: '{result}'")
                batch_parsed = self._parse_simple_batch_create(user_message)
                if batch_parsed:
                    logger.info(f"Rule-based batch_create after multiple JSON failures: {batch_parsed}")
                    return batch_parsed
            
            # Create a smart fallback based on user message
            user_lower = user_message.lower()
            
            # Simple fallback logic 
            if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan']):
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            elif any(word in user_lower for word in ['delete', 'remove']):
                return {"intent": "delete", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
            elif any(word in user_lower for word in ['move', 'update', 'change']):
                return {"intent": "update", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
            elif any(word in user_lower for word in ['add', 'create', 'make']):
                return {"intent": "create", "event_name": "New Event", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
            else:
                return {"intent": "query", "confirmation_needed": False}
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            logger.error(f"User message was: '{user_message}'")
            
            # Attempt rule-based batch parse even in exception path
            try:
                batch_parsed = self._parse_simple_batch_create(user_message)
                if batch_parsed:
                    logger.info(f"Exception path batch_create parsed: {batch_parsed}")
                    return batch_parsed
            except Exception as _bp_err:
                logger.warning(f"Batch parser failed in exception path: {_bp_err}")

            # Even on errors, provide intelligent fallback based on user message  
            user_lower = user_message.lower()
            
            # Enhanced fallback for exception cases
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
                # Extract time shifts and date changes
                if 'forward' in user_lower and ('hour' in user_lower or 'hr' in user_lower):
                    fallback["time_shift"] = "1 hour"
                if 'tomorrow' in user_lower:
                    from datetime import timedelta
                    tomorrow = datetime.now() + timedelta(days=1)
                    fallback["new_date"] = tomorrow.strftime("%Y-%m-%d")
                return fallback
                
            elif any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan']):
                logger.info("Exception fallback: detected query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            elif any(word in user_lower for word in ['add', 'create', 'make']):
                logger.info("Exception fallback: detected create intent")
                return {"intent": "create", "event_name": "New Event", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
            elif any(word in user_lower for word in ['yes', 'confirm', 'ok', 'sure']):
                logger.info("Exception fallback: detected confirmation intent")
                return {"intent": "confirm", "confirmation_needed": False}
            else:
                logger.info("Exception fallback: defaulting to query intent")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
