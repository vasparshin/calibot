"""
Confirmation handler for managing all confirmation workflows consistently.
Consolidates confirmation logic from routes, queue handler, and multi-event operations.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from app.services.telegram import edit_message_text

logger = logging.getLogger(__name__)

class ConfirmationHandler:
    """Handles all confirmation workflows including single, multi-event, and queue confirmations."""

    def __init__(self, telegram_service, conversation_state, calendar_service=None):
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.calendar_service = calendar_service

    async def send_message(self, chat_id: int, message: str, keyboard: Optional[Dict] = None) -> None:
        """Send message with optional keyboard."""
        if keyboard:
            await self.telegram_service.send_telegram_message(chat_id, message, reply_markup=keyboard)
        else:
            await self.telegram_service.send_telegram_message(chat_id, message)
        self.conversation_state.add_message(chat_id, "assistant", message)

    async def edit_message(self, chat_id: int, message_id: int, message: str, keyboard: Optional[Dict] = None) -> None:
        """Edit message and remove keyboard."""
        if keyboard:
            await edit_message_text(chat_id, message_id, message, reply_markup=keyboard)
        else:
            await edit_message_text(chat_id, message_id, message, reply_markup={})

    async def handle_single_confirmation(self, chat_id: int, message_id: int, confirmed: bool, action: str = "process") -> None:
        """Handle single event confirmation response."""
        if confirmed:
            status_text = f"✅ **Confirmed** - Processing {action}..."
            await self.edit_message(chat_id, message_id, status_text)
        else:
            status_text = "❌ **Cancelled** - Request has been cancelled"
            await self.edit_message(chat_id, message_id, status_text)

    async def handle_multi_confirmation(self, chat_id: int, message_id: int, confirmation_type: str, action: str = "process") -> None:
        """Handle multi-event confirmation response."""
        status_texts = {
            "all": "✅ **Complete change** - Processing all events...",
            "one": "1️⃣ **One by One Selected** - Processing events individually...",
            "cancel": "❌ **Cancelled** - Operation has been cancelled"
        }

        status_text = status_texts.get(confirmation_type, f"Choice: {confirmation_type}")
        await self.edit_message(chat_id, message_id, status_text)

    async def handle_queue_confirmation(self, chat_id: int, message_id: int, action: str) -> None:
        """Handle queue confirmation response."""
        action_texts = {
            "confirm": "✅ **Confirmed**",
            "skip": "⏭️ **Skipping current event** - Moving to next...",
            "cancel": "❌ **Cancelled** - Operation cancelled"
        }

        status_text = action_texts.get(action, f"Action: {action}")
        await self.edit_message(chat_id, message_id, status_text)

    async def send_confirmation_request(self, chat_id: int, message: str, keyboard: Dict) -> None:
        """Send confirmation request with keyboard."""
        await self.send_message(chat_id, message, keyboard)

    async def send_follow_up_message(self, chat_id: int, message: str, keyboard: Optional[Dict] = None) -> None:
        """Send follow-up message (used for queue processing)."""
        await self.send_message(chat_id, message, keyboard)

    def validate_confirmation_word(self, message: str) -> Optional[str]:
        """Validate and normalize confirmation words."""
        message_lower = message.lower().strip()

        confirmation_map = {
            'yes': 'yes',
            'y': 'yes',
            'confirm': 'yes',
            'ok': 'yes',
            'no': 'no',
            'n': 'no',
            'cancel': 'no',
            'all': 'all',
            'one': 'one',
            'skip': 'skip',
            'stop': 'cancel'
        }

        return confirmation_map.get(message_lower)

    def find_original_confirmation_message(self, chat_id: int) -> Optional[str]:
        """Find the original confirmation message in conversation history."""
        recent_messages = self.conversation_state.get_recent_messages(chat_id, 3)

        for msg in recent_messages:
            if (msg.get("role") == "assistant" and
                "Are you sure you want to" in msg.get("content", "")):
                return msg.get("content", "")

        return None

    def has_pending_operation(self, chat_id: int, operation_type: str = None) -> bool:
        """Check if there's a pending operation for the chat."""
        # This would be implemented based on the specific operation tracking system
        # For now, return False as a placeholder
        return False

    async def clear_pending_operations(self, chat_id: int) -> None:
        """Clear all pending operations for a chat."""
        # Implementation would depend on the specific operation tracking
        logger.info(f"Cleared pending operations for chat {chat_id}")

    async def process_confirmation_response(self, chat_id: int, confirmation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process confirmation response based on context."""
        # This is a generic processor that would be specialized based on context
        # Context would include operation type, event data, etc.

        result = {
            "success": True,
            "confirmation": confirmation,
            "action_taken": f"Processed {confirmation} confirmation",
            "requires_user_action": False
        }

        if confirmation == "cancel":
            await self.clear_pending_operations(chat_id)
            result["message"] = "Operation cancelled successfully."
        elif confirmation in ["yes", "all"]:
            result["message"] = "Processing your request..."
        elif confirmation == "one":
            result["message"] = "Processing one by one..."
            result["requires_user_action"] = True

        return result
