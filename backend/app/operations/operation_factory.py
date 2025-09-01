"""
Operation factory for creating and executing operations based on intent.
Provides unified interface for all operation types.
"""

import logging
from typing import Dict, Any, Optional

from .create_operation import CreateOperation
from .update_operation import UpdateOperation
from .delete_operation import DeleteOperation
from .query_operation import QueryOperation
from .undo_operation import UndoOperation

logger = logging.getLogger(__name__)

class OperationFactory:
    """Factory for creating and executing operations based on intent."""

    def __init__(self, telegram_service, conversation_state, calendar_service, calendar_agent=None):
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.calendar_service = calendar_service
        self.calendar_agent = calendar_agent

        # Initialize operation instances
        self.operations = {
            "create": CreateOperation(telegram_service, conversation_state, calendar_service, calendar_agent),
            "batch_create": CreateOperation(telegram_service, conversation_state, calendar_service, calendar_agent),
            "update": UpdateOperation(telegram_service, conversation_state, calendar_service, calendar_agent),
            "delete": DeleteOperation(telegram_service, conversation_state, calendar_service, calendar_agent),
            "query": QueryOperation(telegram_service, conversation_state, calendar_service, calendar_agent),
            "undo": UndoOperation(telegram_service, conversation_state, calendar_service, calendar_agent)
        }

    async def execute_operation(self, chat_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation based on intent."""
        try:
            intent = event_data.get("intent")
            logger.info(f"🔧 OperationFactory: Executing intent '{intent}' for chat {chat_id}")

            if not intent:
                logger.warning("🔧 OperationFactory: No intent specified")
                return {
                    "success": False,
                    "error": "No intent specified",
                    "message": "Sorry, I couldn't determine what operation you want to perform."
                }

            operation = self.operations.get(intent)
            logger.info(f"🔧 OperationFactory: Found operation for intent '{intent}': {type(operation).__name__ if operation else 'None'}")

            if not operation:
                logger.warning(f"🔧 OperationFactory: Unknown intent: {intent}")
                return {
                    "success": False,
                    "error": f"Unknown intent: {intent}",
                    "message": "Sorry, I don't know how to handle that type of request."
                }

            # Execute the operation with hooks
            logger.info(f"🔧 OperationFactory: Executing {type(operation).__name__} for intent '{intent}'")
            result = await operation.run_with_hooks(chat_id, event_data)
            logger.info(f"🔧 OperationFactory: Operation result: {result}")
            return result

        except Exception as e:
            logger.error(f"🔧 OperationFactory: Error executing operation for intent {event_data.get('intent')}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your request."
            }

    async def handle_confirmation(self, chat_id: int, confirmation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle confirmation responses for pending operations."""
        try:
            # Get pending operation context
            pending_op = self.get_pending_operation(chat_id)

            if not pending_op:
                return {
                    "success": False,
                    "message": "No pending operation found."
                }

            operation_type = pending_op.get("type")
            operation = self.operations.get(operation_type)

            if operation and hasattr(operation, 'handle_confirmation'):
                return await operation.handle_confirmation(chat_id, confirmation, pending_op)
            else:
                return {
                    "success": False,
                    "message": "Cannot handle confirmation for this operation type."
                }

        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error processing confirmation."
            }

    def get_pending_operation(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get pending operation for chat."""
        # This would check various sources for pending operations
        # For now, check conversation state
        return self.conversation_state.get_data(chat_id, "pending_operation")

    def clear_pending_operation(self, chat_id: int) -> None:
        """Clear pending operation for chat."""
        self.conversation_state.set_data(chat_id, "pending_operation", None)

    async def create_operation(self, intent: str) -> Optional[object]:
        """Create operation instance for given intent."""
        operation_class = {
            "create": CreateOperation,
            "batch_create": CreateOperation,
            "update": UpdateOperation,
            "delete": DeleteOperation,
            "query": QueryOperation,
            "undo": UndoOperation
        }.get(intent)

        if operation_class:
            return operation_class(
                self.telegram_service,
                self.conversation_state,
                self.calendar_service,
                self.calendar_agent
            )

        return None

    def get_supported_intents(self) -> list[str]:
        """Get list of supported intents."""
        return list(self.operations.keys())

    async def validate_operation(self, intent: str, event_data: Dict[str, Any]) -> bool:
        """Validate if operation can be executed with given data."""
        operation = self.operations.get(intent)

        if not operation:
            return False

        return await operation.validate_input(event_data)
