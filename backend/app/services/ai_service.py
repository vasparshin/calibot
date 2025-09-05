from datetime import datetime
from app.config import OPENAI_API_KEY, LITELLM_MODEL
# Using inline prompts instead of separate files
AGENT_SYSTEM_PROMPT = """You are CaliBOT, a helpful calendar assistant. Respond naturally to calendar-related queries.

Event data: {event_data}
Current date: {current_date}

Provide helpful, concise responses about calendar events."""

SMALL_TALK_SYSTEM_PROMPT = """You are CaliBOT, a friendly calendar assistant. Respond to small talk and greetings naturally.

User message: {user_message}
Conversation history: {conversation_history}
Current date: {current_date}

Keep responses brief and friendly, then guide back to calendar topics."""
from app.utils.helpers import format_conversation_history
from litellm import acompletion
from typing import Dict
import httpx
import logging
import json
import litellm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_ai_response(event_data: Dict, conversation_history: list) -> str:
    
    if len(conversation_history) == 0:
        return "Sorry, I'm not sure how to respond to that."
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT.format(event_data=event_data, current_date=current_date)}]
    user_message = conversation_history[-1]["content"]
    messages.append({"role": "user", "content": user_message})
    
    response = await acompletion(
        api_key=OPENAI_API_KEY, model=LITELLM_MODEL, messages=messages, max_tokens=200
    )
    logger.info(f'------------------------------------>Response: {response["choices"][0]["message"]["content"]}')
    return response["choices"][0]["message"]["content"]


async def get_small_talk_response(user_message: str, conversation_history: list) -> str:
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    formatted_history = format_conversation_history(conversation_history)
    messages = [{"role": "system", "content": SMALL_TALK_SYSTEM_PROMPT.format(user_message=user_message, conversation_history=formatted_history, current_date=current_date)}]
    messages.append({"role": "user", "content": user_message})
    
    response = await acompletion(
        model=LITELLM_MODEL, messages=messages, max_tokens=200
    )
    
    # CRITICAL FIX: Handle LiteLLM ModelResponse objects properly
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message') and choice.message:
            if hasattr(choice.message, 'content'):
                return choice.message.content
    
    # Fallback for dict-style response
    if isinstance(response, dict) and 'choices' in response:
        return response["choices"][0]["message"]["content"]
    
    return "I'm not sure how to respond to that."