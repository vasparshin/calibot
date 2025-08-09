"""
Unified AIService: consolidates previous ai_service functions and NLPAgent logic.
Provides:
- check_relevancy(user_message, history)
- extract_intent(user_message, history)
- get_ai_response(event_data, history)
- get_small_talk_response(user_message, history)
"""
from datetime import datetime
import json
import logging
from typing import Dict, List
from litellm import acompletion
from app.config import OPENAI_API_KEY, OPENAI_MODEL, LITELLM_MODEL
from app.utils.helpers import format_conversation_history
from app.prompts.intent_extraction_prompt import INTENT_EXTRACTION_PROMPT
from app.prompts.relevancy_classifier_prompt import RELEVANCY_CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.intent_prompt = INTENT_EXTRACTION_PROMPT
        self.relevancy_prompt = RELEVANCY_CLASSIFIER_PROMPT
        self.intent_model = LITELLM_MODEL
        self.response_model = OPENAI_MODEL

    async def check_relevancy(self, user_message: str, history: List[Dict]) -> dict:
        formatted_history = format_conversation_history(history)
        try:
            response = await acompletion(
                model=self.intent_model,
                messages=[
                    {"role": "system", "content": self.relevancy_prompt.format(conversation_history=formatted_history)},
                    {"role": "user", "content": f"User message: {user_message}"}
                ],
            )
            content = response["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Relevancy check failed: {e}")
            return {"relevant": False, "reason": "processing_error"}

    async def extract_intent(self, user_message: str, history: List[Dict]) -> dict:
        try:
            formatted_history = format_conversation_history(history)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            system_message = self.intent_prompt.format(conversation_history=formatted_history, current_date=current_datetime)
            response = await acompletion(
                model=self.intent_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500
            )
            raw = response['choices'][0]['message']['content']
            cleaned = raw.strip()
            if cleaned.startswith('```') and cleaned.endswith('```'):
                lines = cleaned.split('\n')
                if len(lines) > 2:
                    cleaned = '\n'.join(lines[1:-1])
            # Attempt single JSON parse
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Multiple JSON lines -> batch create
                objs = []
                for line in [ln.strip() for ln in cleaned.split('\n') if ln.strip()]:
                    try:
                        objs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                if objs:
                    return {"intent": "batch_create", "events": objs, "confirmation_needed": False}
            # Fallback heuristic
            lower = user_message.lower()
            if any(w in lower for w in ['add', 'create', 'schedule']):
                return {"intent": "create", "event_name": "New Event", "date": datetime.now().strftime('%Y-%m-%d'), "confirmation_needed": True}
            if any(w in lower for w in ['what', 'show', 'list']):
                return {"intent": "query", "date": datetime.now().strftime('%Y-%m-%d'), "confirmation_needed": False}
            return {"intent": "query", "confirmation_needed": False}
        except Exception as e:
            logger.error(f"Intent extraction error: {e}")
            return {"intent": "unknown", "error": str(e), "confirmation_needed": True}

    async def get_ai_response(self, event_data: Dict, conversation_history: List[Dict]) -> str:
        if not conversation_history:
            return "Sorry, I'm not sure how to respond to that."
        current_date = datetime.now().strftime("%Y-%m-%d")
        messages = [
            {"role": "system", "content": f"Act as calendar assistant. Current date: {current_date}. Event data: {event_data}"},
            {"role": "user", "content": conversation_history[-1]["content"]}
        ]
        response = await acompletion(
            api_key=OPENAI_API_KEY,
            model=self.response_model,
            messages=messages,
            max_tokens=200
        )
        return response["choices"][0]["message"]["content"]

    async def get_small_talk_response(self, user_message: str, conversation_history: List[Dict]) -> str:
        current_date = datetime.now().strftime("%Y-%m-%d")
        formatted_history = format_conversation_history(conversation_history)
        messages = [
            {"role": "system", "content": f"Casual small talk mode. Date: {current_date}. History: {formatted_history}"},
            {"role": "user", "content": user_message}
        ]
        response = await acompletion(
            api_key=OPENAI_API_KEY,
            model=self.response_model,
            messages=messages,
            max_tokens=200
        )
        return response["choices"][0]["message"]["content"]

# Singleton instance
ai_service = AIService()