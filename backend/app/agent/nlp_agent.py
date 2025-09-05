from datetime import datetime
from litellm import acompletion
from app.utils.helpers import format_conversation_history
from app.config import LITELLM_MODEL
import json
import logging
import asyncio
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPAgent:
    def __init__(self):
        self.model = LITELLM_MODEL
        self._prompt_cache = None
    
    def _load_prompt(self) -> str:
        """Load the combined extraction prompt from the .txt file."""
        if self._prompt_cache is None:
            try:
                # Get the directory of the current file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # Navigate to prompts directory and load the .txt file
                prompt_path = os.path.join(current_dir, '..', 'prompts', 'combined_extraction_prompt.txt')
                prompt_path = os.path.normpath(prompt_path)
                
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._prompt_cache = f.read()
                logger.info(f"Loaded prompt from: {prompt_path}")
            except Exception as e:
                logger.error(f"Failed to load prompt file: {e}")
                # Fallback to a basic prompt if file loading fails
                self._prompt_cache = """You are a calendar assistant that determines if a user message is relevant to calendar tasks AND extracts the intent and details in a single analysis.

Return JSON format:
{"relevant": true/false, "intent": "query|create|update|delete|undo", "event_name": "", "date": "today", "confirmation_needed": false, ...other_fields...}

For irrelevant messages:
{"relevant": false, "reason": "explanation", "reply": "response"}

Always return complete, valid JSON."""
        
        return self._prompt_cache





        
    # Removed unused check_relevancy method - now using combined extraction

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

            # Load prompt from .txt file and format it
            prompt_template = self._load_prompt()
            system_message = prompt_template.format(
                conversation_history=formatted_history,
                current_date=current_datetime,
                current_date_iso=current_date_iso,
                tomorrow_date_iso=tomorrow_date_iso,
                yesterday_date_iso=yesterday_date_iso,
                next_week_date_iso=next_week_date_iso
            )

            logger.info(f"extract_relevancy_and_intent: Called with message='{user_message}', history_length={len(conversation_history)}")

            async def _call_llm():
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                # CRITICAL FIX: Add unique identifier to prevent duplicate logging
                call_id = f"combined_extract_{int(time.time() * 1000)}"
                logger.info(f"extract_relevancy_and_intent: Making LLM call {call_id}")
                
                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    max_tokens=300,  # Increased for combined response
                    temperature=0.1,
                )
                
                logger.info(f"extract_relevancy_and_intent: LLM call {call_id} completed")
                return response

            response = await _call_llm()

            # Extract content from LiteLLM ModelResponse
            result = None
            extraction_method = "unknown"
            
            # Primary method: ModelResponse object attribute access
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        result = choice.message.content
                        extraction_method = "ModelResponse.choices[0].message.content"
            
            # Fallback method: Dict-like access for older response formats
            if result is None and isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        result = choice['message']['content']
                        extraction_method = "dict.choices[0].message.content"
            
            if result is None:
                raise ValueError("Could not extract content from LLM response")

            logger.info(f"LiteLLM: Response extracted using {extraction_method}")

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
                    raise ValueError("Response is not a dictionary")
                
                # Ensure required fields exist
                if "relevant" not in parsed_result:
                    parsed_result["relevant"] = True
                
                if "intent" not in parsed_result:
                    parsed_result["intent"] = "query"
                
                logger.info(f"extract_relevancy_and_intent: Completed successfully, relevant={parsed_result.get('relevant')}, intent={parsed_result.get('intent')}")
                return parsed_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}, raw response: {cleaned_result}")
                return {"relevant": True, "intent": "query", "error": "JSON parsing failed"}
                
        except Exception as e:
            logger.error(f"extract_relevancy_and_intent: Error processing message: {e}")
            return {"relevant": True, "intent": "query", "error": str(e)}

    # Removed extract_intent method - now using combined extraction approach
        

