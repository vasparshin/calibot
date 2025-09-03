from datetime import datetime
from litellm import acompletion
from app.utils.helpers import format_conversation_history
from app.config import LITELLM_MODEL
from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
from app.prompts.relevancy_classifier_prompt import RELEVANCY_CLASSIFIER_PROMPT
from app.prompts.combined_extraction_prompt import COMBINED_EXTRACTION_PROMPT
import json
import logging
import asyncio
import time

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
            # CRITICAL FIX: Use same comprehensive response handling as extract_intent
            result = None
            
            # Method 1: Direct attribute access (ModelResponse object)
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        result = choice.message.content
            
            # Method 2: Dict-like access (if response is dict-like)
            if result is None and isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        result = choice['message']['content']
            
            if result is None:
                raise ValueError("Could not extract content from LLM response")
            
            return json.loads(result.strip())
        except Exception as e:
            logger.error(f"Relevancy check failed: {e}")
            return {"relevant": True, "reason": "Fallback to relevant due to processing error"}

    async def generate_response(self, prompt: str, conversation_history: list) -> str:
        """Generate a natural language response using LLM."""
        try:
            formatted_history = format_conversation_history(conversation_history)

            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"CONVERSATION HISTORY:\n{formatted_history}\n\nYou are a helpful calendar assistant. Respond naturally and helpfully."},
                    {"role": "user", "content": prompt}
                ],
            )

            # CRITICAL FIX: Use comprehensive response handling like extract_intent
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        return choice.message.content.strip()
                    else:
                        raise ValueError("Message missing content field")
                else:
                    raise ValueError("Choice missing message field")
            else:
                raise ValueError("Response missing choices field")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""

    async def extract_relevancy_and_intent(self, user_message: str, conversation_history: list) -> dict:
        """Extract both relevancy and intent in a single LLM call for efficiency."""
        try:
            formatted_history = format_conversation_history(conversation_history)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Calculate dynamic dates for prompt examples
            from datetime import timedelta
            current_date = datetime.now()
            current_date_iso = current_date.strftime("%Y-%m-%d")
            tomorrow_date_iso = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_date_iso = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            next_week_date_iso = (current_date + timedelta(days=7)).strftime("%Y-%m-%d")

            system_message = COMBINED_EXTRACTION_PROMPT.format(
                conversation_history=formatted_history,
                current_date=current_datetime,
                current_date_iso=current_date_iso,
                tomorrow_date_iso=tomorrow_date_iso,
                yesterday_date_iso=yesterday_date_iso,
                next_week_date_iso=next_week_date_iso
            )

            async def _call_llm():
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    max_tokens=300,  # Increased for combined response
                    temperature=0.1,
                )
                
                return response

            response = await _call_llm()

            # Extract content from LiteLLM ModelResponse
            result = None
            
            # Primary method: ModelResponse object attribute access
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        result = choice.message.content
            
            # Fallback method: Dict-like access for older response formats
            if result is None and isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        result = choice['message']['content']
            
            if result is None:
                raise ValueError("Could not extract content from LLM response")

            # Clean the response
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
            
            # Parse JSON response
            try:
                parsed_result = json.loads(cleaned_result)
                
                # Validate basic structure
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-dict JSON: {type(parsed_result)}")
                    raise ValueError("Non-dict response")
                
                # Check for required fields based on relevancy
                if parsed_result.get("relevant", True):
                    if 'intent' not in parsed_result:
                        logger.error(f"LLM JSON missing 'intent' field for relevant message: {parsed_result}")
                        raise ValueError("Missing intent field for relevant message")
                else:
                    if 'reason' not in parsed_result:
                        logger.error(f"LLM JSON missing 'reason' field for irrelevant message: {parsed_result}")
                        raise ValueError("Missing reason field for irrelevant message")
                
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
                        pass
                
                # Fallback: return default query intent
                logger.warning(f"Using fallback query intent due to parsing failure")
                return {
                    "relevant": True,
                    "intent": "query",
                    "event_name": "",
                    "date": current_date_iso,
                    "confirmation_needed": False
                }
                
        except Exception as e:
            logger.error(f"Combined extraction failed: {e}")
            # Fallback: return default query intent
            return {
                "relevant": True,
                "intent": "query",
                "event_name": "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "confirmation_needed": False
            }

    async def extract_intent(self, user_message, conversation_history):
        try:
            formatted_history = format_conversation_history(conversation_history)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Calculate dynamic dates for prompt examples
            from datetime import timedelta
            current_date = datetime.now()
            current_date_iso = current_date.strftime("%Y-%m-%d")
            tomorrow_date_iso = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_date_iso = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            next_week_date_iso = (current_date + timedelta(days=7)).strftime("%Y-%m-%d")

            system_message = self.system_prompt.format(
                conversation_history=formatted_history,
                current_date=current_datetime,
                current_date_iso=current_date_iso,
                tomorrow_date_iso=tomorrow_date_iso,
                yesterday_date_iso=yesterday_date_iso,
                next_week_date_iso=next_week_date_iso
            )

            async def _call_llm():
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.1,
                )
                
                return response

            response = await _call_llm()

            # Extract content from LiteLLM ModelResponse
            result = None
            
            # Primary method: ModelResponse object attribute access
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        result = choice.message.content
            
            # Fallback method: Dict-like access for older response formats
            if result is None and isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        result = choice['message']['content']
            
            if result is None:
                raise ValueError("Could not extract content from LLM response")

            # Clean the response
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
            
            # Parse JSON response
            try:
                parsed_result = json.loads(cleaned_result)
                
                # Validate basic structure
                if not isinstance(parsed_result, dict):
                    logger.error(f"LLM returned non-dict JSON: {type(parsed_result)}")
                    raise ValueError("Non-dict response")
                
                if 'intent' not in parsed_result:
                    logger.error(f"LLM JSON missing 'intent' field: {parsed_result}")
                    raise ValueError("Missing intent field")
                
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
                
                # If LLM fails to return valid JSON, return an error
                # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
                logger.error(f"🚨 LLM processing failed for message: '{user_message}'")
                logger.error(f"🚨 Raw LLM response: '{result}'")
                logger.error(f"🚨 Cleaned response: '{cleaned_result}'")
                raise ValueError("LLM failed to process user message - no fallback functionality allowed")
            
            # SUCCESS: LLM returned valid JSON
            logger.info(f"✅ Successfully parsed LLM JSON response: {parsed_result}")
            
            # Validate JSON structure
            if not isinstance(parsed_result, dict):
                logger.error(f"LLM returned non-dict JSON: {type(parsed_result)} - falling back")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            if "intent" not in parsed_result:
                logger.error(f"LLM JSON missing 'intent' field: {parsed_result} - falling back")
                return {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            
            # NO MANUAL MESSAGE PARSING - per PROJECT_RULES.md
            # LLM should provide ALL necessary information including calendar names
            # If calendar_name is missing, let the operation handle it or default appropriately
            
            return parsed_result

        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            logger.error(f"User message was: '{user_message}'")
            
            # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
            # If LLM processing fails, return an error instead of fallback logic
            raise ValueError(f"LLM failed to process user message: {str(e)} - no fallback functionality allowed")
        

