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
            if cleaned_result.strip() == '"intent"' or cleaned_result.strip() == '"query"':
                logger.error(f"DETECTED EXACT BAD RESPONSE: '{cleaned_result}' - immediate fallback")
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan', 'calendar']):
                    return {
                        "intent": "query",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "confirmation_needed": False
                    }
                elif 'yes' in user_lower:
                    return {
                        "intent": "confirm",
                        "confirmation_needed": False
                    }
                else:
                    return {
                        "intent": "query",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "confirmation_needed": False
                    }
            
            # Enhanced detection for invalid LLM responses
            is_invalid_response = (
                len(cleaned_result) < 20 or 
                not cleaned_result.startswith('{') or 
                cleaned_result.strip() in ['"intent"', 'intent', '"query"', 'query'] or
                cleaned_result == '"intent"' or 
                cleaned_result == '"query"' or
                cleaned_result.strip('"') in ['intent', 'query'] or
                cleaned_result.strip().strip('"') in ['intent', 'query']
            )
            
            if is_invalid_response:
                logger.error(f"DETECTED INVALID LLM RESPONSE - triggering fallback")
                logger.error(f"Raw: '{result}', Cleaned: '{cleaned_result}', Length: {len(cleaned_result)}")
                logger.error(f"Starts with curly: {cleaned_result.startswith('{')}")
                logger.error(f"Stripped: '{cleaned_result.strip()}'")
                
                # Try to infer intent from user message
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan', 'calendar']):
                    return {
                        "intent": "query",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "confirmation_needed": False
                    }
                elif any(word in user_lower for word in ['add', 'create', 'make', 'schedule']):
                    return {
                        "intent": "create", 
                        "event_name": "New Event",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "confirmation_needed": True
                    }
                else:
                    return {
                        "intent": "query",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "confirmation_needed": False
                    }
            
            # Try to parse as single JSON first
            try:
                parsed_result = json.loads(cleaned_result)
                logger.info(f"JSON parsing successful, result type: {type(parsed_result)}")
                
                # Ensure the parsed result is actually a dict/object, not just a string
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-object JSON: {type(parsed_result)} - {parsed_result}")
                    # Trigger fallback by setting parsed_result to None
                    parsed_result = None
                else:
                    logger.info(f"Valid JSON dict received: {parsed_result}")
                    return parsed_result
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing failed: {json_error}")
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
            if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list', 'plan']):
                return {
                    "intent": "query",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "confirmation_needed": False
                }
            elif any(word in user_lower for word in ['add', 'create', 'make', 'schedule']):
                return {
                    "intent": "create",
                    "event_name": "New Event", 
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "confirmation_needed": True
                }
            else:
                return {
                    "intent": "query",
                    "confirmation_needed": False
                }
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            return {
                "intent": "unknown",
                "error": str(e),
                "confirmation_needed": True
            }
