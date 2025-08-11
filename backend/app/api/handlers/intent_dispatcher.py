"""Intent dispatcher scaffold (phase 1).
Currently unused; future phases will route intents to handlers.
"""
from __future__ import annotations
from typing import Dict, Any

class IntentDispatcher:
    def __init__(self, calendar_service, conversation_state):
        self.calendar_service = calendar_service
        self.conversation_state = conversation_state

    async def dispatch(self, chat_id: int, event_data: Dict[str, Any]):
        # Placeholder for future structured dispatch logic
        return {"status": "not_implemented"}
