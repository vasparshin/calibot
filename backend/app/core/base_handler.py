"""
Base handler class providing common functionality for all operation handlers.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.telegram import edit_message_text

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all operation handlers providing common functionality."""

    def __init__(self, telegram_service, conversation_state, calendar_service=None, calendar_agent=None):
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.calendar_service = calendar_service
        self.calendar_agent = calendar_agent

    async def send_message(self, chat_id: int, message: str, keyboard: Optional[Dict] = None) -> None:
        """Send message with optional keyboard through telegram service."""
        try:
            if keyboard:
                await self.telegram_service.send_telegram_message(chat_id, message, reply_markup=keyboard)
            else:
                await self.telegram_service.send_telegram_message(chat_id, message)
            self.conversation_state.add_message(chat_id, "assistant", message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def edit_message(self, chat_id: int, message_id: int, message: str, keyboard: Optional[Dict] = None) -> None:
        """Edit message with optional keyboard through telegram service."""
        try:
            if keyboard:
                await edit_message_text(chat_id, message_id, message, reply_markup=keyboard)
            else:
                await edit_message_text(chat_id, message_id, message, reply_markup={})
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            raise

    def add_to_conversation(self, chat_id: int, role: str, content: str, message_type: str = "text") -> None:
        """Add message to conversation state."""
        self.conversation_state.add_message(chat_id, role, content, message_type)

    def get_recent_messages(self, chat_id: int, count: int = 5) -> List[Dict]:
        """Get recent conversation messages."""
        return self.conversation_state.get_recent_messages(chat_id, count)

    def get_conversation_history(self, chat_id: int) -> List[Dict]:
        """Get full conversation history."""
        return self.conversation_state.get_conversation_history(chat_id)

    def set_conversation_data(self, chat_id: int, key: str, value: Any) -> None:
        """Set conversation data."""
        self.conversation_state.set_data(chat_id, key, value)

    def get_conversation_data(self, chat_id: int, key: str) -> Any:
        """Get conversation data."""
        return self.conversation_state.get_data(chat_id, key)

    def remove_system_message(self, chat_id: int, content_filter: str) -> None:
        """Remove system message containing specific content."""
        self.conversation_state.remove_system_message(chat_id, content_filter)

    def log_operation(self, operation: str, chat_id: int, details: Dict[str, Any] = None) -> None:
        """Log operation with consistent format."""
        details_str = f" - {details}" if details else ""
        logger.info(f"🔧 {operation.upper()}: Chat {chat_id}{details_str}")

    def validate_event_data(self, event_data: Dict) -> bool:
        """Validate basic event data structure."""
        required_fields = ['intent']
        for field in required_fields:
            if field not in event_data:
                logger.warning(f"Missing required field: {field}")
                return False
        return True

    def format_timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.now().isoformat()

    async def handle_error(self, chat_id: int, error: Exception, operation: str = "operation") -> None:
        """Handle and log errors consistently."""
        logger.error(f"Error in {operation}: {error}")
        error_message = f"Sorry, there was an error during {operation}. Please try again."
        await self.send_message(chat_id, error_message)
