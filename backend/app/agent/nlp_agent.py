from datetime import datetime
from litellm import acompletion
from app.utils.helpers import format_conversation_history
from app.config import LITELLM_MODEL
from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
from app.prompts.relevancy_classifier_prompt import RELEVANCY_CLASSIFIER_PROMPT
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
            # CRITICAL FIX: Use comprehensive response handling like extract_intent
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        relevancy_result = choice.message.content
                    else:
                        raise ValueError("Message missing content field")
                else:
                    raise ValueError("Choice missing message field")
            else:
                raise ValueError("Response missing choices field")
            
            return json.loads(relevancy_result)
        except Exception as e:
            return {"relevant": False, "reason": "Failed to process response"}

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

    async def extract_intent(self, user_message, conversation_history):
        """Process user message and extract calendar intent and details"""
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
                # Enhanced LLM input logging - show full content for debugging
                logger.info(f"🔍 LLM CALL DEBUG - Messages being sent to {self.model}:")
                for i, msg in enumerate(messages):
                    role = msg['role']
                    content = msg['content']
                    content_length = len(content)
                    
                    logger.info(f"🔍 Message {i+1} ({role}): Length {content_length} chars")
                    
                    # For ALL messages, show COMPLETE content - no truncation
                    if role == 'system':
                        logger.info(f"🔍 COMPLETE SYSTEM MESSAGE:")
                        # Split into readable chunks for very long content
                        if content_length > 1000:
                            chunk_size = 500
                            for chunk_i in range(0, content_length, chunk_size):
                                chunk = content[chunk_i:chunk_i + chunk_size]
                                chunk_num = chunk_i // chunk_size + 1
                                logger.info(f"🔍 System chunk {chunk_num}: {chunk}")
                        else:
                            logger.info(f"🔍 System content: {content}")
                    
                    # For user messages, always show complete content 
                    elif role == 'user':
                        logger.info(f"🔍 COMPLETE USER MESSAGE: '{content}'")
                
                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    max_tokens=200,  # Reduced for focused JSON responses
                    temperature=0.1,  # Tiny bit of randomness to avoid getting stuck
                )
                
                # Enhanced response logging - FIXED to handle ModelResponse objects
                logger.info(f"🔍 LLM RESPONSE DEBUG - Raw response type: {type(response)}")
                logger.info(f"🔍 LLM RESPONSE DEBUG - Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                
                # Safe response structure exploration for debugging
                try:
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
                                logger.info(f"🔍 LLM RESPONSE DEBUG - Content length: {len(content)} chars")
                    elif hasattr(response, 'choices') and response.choices:
                        logger.info(f"🔍 LLM RESPONSE DEBUG - ModelResponse choices length: {len(response.choices)}")
                        if response.choices:
                            choice = response.choices[0]
                            logger.info(f"🔍 LLM RESPONSE DEBUG - ModelResponse choice type: {type(choice)}")
                            if hasattr(choice, 'message') and choice.message:
                                message = choice.message
                                logger.info(f"🔍 LLM RESPONSE DEBUG - ModelResponse message type: {type(message)}")
                                if hasattr(message, 'content'):
                                    content = message.content
                                    logger.info(f"🔍 LLM RESPONSE DEBUG - ModelResponse content: '{content}'")
                                    logger.info(f"🔍 LLM RESPONSE DEBUG - ModelResponse content length: {len(content)} chars")
                except Exception as debug_e:
                    logger.error(f"🔍 LLM RESPONSE DEBUG - Error in debug logging: {debug_e}")
                    # Don't let debug errors affect the main processing
                
                return response

            response = await _call_llm()

            # CRITICAL FIX: Handle ALL possible LiteLLM response structures
            logger.info(f"🔍 RESPONSE STRUCTURE DEBUG - Type: {type(response)}")
            logger.info(f"🔍 RESPONSE STRUCTURE DEBUG - Dir: {dir(response) if hasattr(response, '__dict__') else 'No dir'}")
            
            # Handle multiple possible response structures
            result = None
            
            # Method 1: Direct attribute access (ModelResponse object)
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        result = choice.message.content
                        logger.info(f"🔍 Method 1 success: Got content via attributes")
            
            # Method 2: Dict-like access (if response is dict-like)
            if result is None and isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        result = choice['message']['content']
                        logger.info(f"🔍 Method 2 success: Got content via dict access")
            
            # Method 3: Try to convert to dict and access
            if result is None and hasattr(response, '__dict__'):
                try:
                    response_dict = response.__dict__
                    if 'choices' in response_dict and response_dict['choices']:
                        choice = response_dict['choices'][0]
                        if hasattr(choice, '__dict__') and 'message' in choice.__dict__:
                            message = choice.__dict__['message']
                            if hasattr(message, '__dict__') and 'content' in message.__dict__:
                                result = message.__dict__['content']
                                logger.info(f"🔍 Method 3 success: Got content via __dict__ access")
                except Exception as e:
                    logger.error(f"🔍 Method 3 failed: {e}")
            
            # Method 4: Last resort - try to access any content-like field
            if result is None:
                try:
                    # Try to find any field that might contain the response
                    for attr in dir(response):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(response, attr)
                                if isinstance(value, str) and value.strip().startswith('{'):
                                    result = value
                                    logger.info(f"🔍 Method 4 success: Found content in {attr}")
                                    break
                            except:
                                continue
                except Exception as e:
                    logger.error(f"🔍 Method 4 failed: {e}")
            
            if result is None:
                logger.error(f"🔍 ALL METHODS FAILED - Response structure: {response}")
                logger.error(f"🔍 Response type: {type(response)}")
                logger.error(f"🔍 Response dir: {dir(response) if hasattr(response, '__dict__') else 'No dir'}")
                raise ValueError("Could not extract content from response")

            logger.info(f"🔍 COMPLETE LLM RESPONSE: '{result}'")
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
                
                # Log what the LLM returned for debugging
                logger.info(f"🔍 LLM returned: {parsed_result}")
                
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
        

