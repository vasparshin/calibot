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
                # Temporarily removing response_format to debug
                # response_format={"type": "json_object"}
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
            
            # If response is just "intent" or similar, create a fallback
            if len(cleaned_result) < 20 or not cleaned_result.startswith('{'):
                logger.error(f"Invalid LLM response, creating fallback. Raw: '{result}'")
                # Try to infer intent from user message
                user_lower = user_message.lower()
                if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list']):
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
            
            # Try to parse as single JSON first
            try:
                parsed_result = json.loads(cleaned_result)
                return parsed_result
            except json.JSONDecodeError:
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
                
                # If nothing worked, log the original error and continue to fallback
                logger.error(f"Multiple JSON parsing also failed")
                logger.error(f"Raw response content: '{response['choices'][0]['message']['content'] if 'choices' in response else 'No choices in response'}'")
            
            # Create a smart fallback based on user message
            user_lower = user_message.lower()
            if any(word in user_lower for word in ['schedule', 'today', 'what', 'show', 'list']):
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
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            return {
                "intent": "unknown",
                "error": str(e),
                "confirmation_needed": True
            }
