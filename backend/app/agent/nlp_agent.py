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

            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500
            )

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
                    return fallback
                    
                elif any(word in user_lower for word in ['schedule', 'today', 'what', 'plan']):
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
                logger.error(f"DETECTED INVALID LLM RESPONSE - minimal fallback")
                logger.error(f"Raw: '{result}', Cleaned: '{cleaned_result}', Length: {len(cleaned_result)}")
                
                # Minimal fallback based on keywords
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan']):
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
                elif any(word in user_lower for word in ['delete', 'remove']):
                    return {"intent": "delete", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                elif any(word in user_lower for word in ['move', 'update', 'change']):
                    return {"intent": "update", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": True}
                else:
                    return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            # Try to parse as single JSON first
            try:
                parsed_result = json.loads(cleaned_result)
                logger.info(f"JSON parsing successful, result type: {type(parsed_result)}")
                
                # Ensure the parsed result is actually a dict/object, not just a string
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-object JSON: {type(parsed_result)} - {parsed_result}")
                    # This is likely the "intent" or "query" string response - trigger fallback
                    logger.error(f"Detected string response instead of JSON object - triggering intelligent fallback")
                    parsed_result = None
                else:
                    logger.info(f"Valid JSON dict received: {parsed_result}")
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
                
                # If nothing worked, use intelligent fallback based on user message
                logger.error(f"Multiple JSON parsing also failed, using intelligent fallback")
                logger.error(f"Raw response content: '{result}'")
            
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
