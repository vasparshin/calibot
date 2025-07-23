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
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = response['choices'][0]['message']['content']
            parsed_result = json.loads(result)
            return parsed_result
        except Exception as e:
            print(f"Error extracting intent: {e}")
            return {
                "intent": "unknown",
                "error": str(e),
                "confirmation_needed": True
            }
