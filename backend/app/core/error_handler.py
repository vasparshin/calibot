"""
Error handler for consistent error management across the application.
Centralizes error handling patterns and logging.
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling and logging."""

    ERROR_TYPES = {
        'authentication': 'Authentication system is not properly configured',
        'auth_expired': 'Your Google authentication has expired',
        'auth_unavailable': 'Authentication system is temporarily unavailable',
        'processing': 'Technical difficulties occurred during processing',
        'validation': 'Unable to understand the request format',
        'network': 'Network connectivity issues',
        'calendar_api': 'Calendar service is temporarily unavailable',
        'telegram_api': 'Messaging service is temporarily unavailable',
        'database': 'Data storage service is temporarily unavailable',
        'configuration': 'System configuration error',
        'rate_limit': 'Too many requests, please wait before trying again',
        'permission': 'Insufficient permissions to perform this operation',
        'not_found': 'Requested resource not found',
        'duplicate': 'Operation would create duplicate data',
        'invalid_operation': 'Requested operation is not valid in current state'
    }

    @staticmethod
    def log_error(error: Exception, operation: str, chat_id: Optional[int] = None, details: Dict[str, Any] = None) -> str:
        """Log error with consistent format and return error ID."""
        error_id = f"{int(datetime.now().timestamp())}_{operation.replace(' ', '_')}"

        log_message = f"❌ ERROR [{error_id}]: {operation}"
        if chat_id:
            log_message += f" (Chat: {chat_id})"
        if details:
            log_message += f" - Details: {details}"

        logger.error(f"{log_message} - Exception: {error}")

        return error_id

    @staticmethod
    def format_error_message(error_type: str, details: str = None, include_support: bool = True) -> str:
        """Format error message for user display."""
        base_message = ErrorHandler.ERROR_TYPES.get(error_type, "An unexpected error occurred")

        message = f"❌ {base_message}."

        if details and error_type in ['processing', 'validation', 'network']:
            message += f" {details}."

        if include_support:
            message += " Please try again or contact support if the problem persists."

        return message

    @staticmethod
    def handle_authentication_error(error: Exception, context: str = "operation") -> Dict[str, Any]:
        """Handle authentication-specific errors."""
        logger.error(f"Authentication error during {context}: {error}")

        return {
            "success": False,
            "error_type": "authentication",
            "message": ErrorHandler.format_error_message("auth_expired"),
            "requires_auth": True,
            "can_retry": True
        }

    @staticmethod
    def handle_api_error(error: Exception, api_name: str, operation: str) -> Dict[str, Any]:
        """Handle API-specific errors."""
        logger.error(f"{api_name} API error during {operation}: {error}")

        error_type = f"{api_name.lower()}_api"
        return {
            "success": False,
            "error_type": error_type,
            "message": ErrorHandler.format_error_message(error_type),
            "requires_auth": "auth" in str(error).lower(),
            "can_retry": True
        }

    @staticmethod
    def handle_validation_error(error: Exception, field: str = None) -> Dict[str, Any]:
        """Handle validation errors."""
        details = f"Issue with {field}" if field else None
        logger.warning(f"Validation error: {error}")

        return {
            "success": False,
            "error_type": "validation",
            "message": ErrorHandler.format_error_message("validation", details),
            "can_retry": True
        }

    @staticmethod
    def handle_network_error(error: Exception, operation: str) -> Dict[str, Any]:
        """Handle network connectivity errors."""
        logger.error(f"Network error during {operation}: {error}")

        return {
            "success": False,
            "error_type": "network",
            "message": ErrorHandler.format_error_message("network"),
            "can_retry": True,
            "retry_delay": 5  # seconds
        }

    @staticmethod
    def handle_generic_error(error: Exception, operation: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle unexpected errors."""
        error_id = ErrorHandler.log_error(error, operation, chat_id)

        return {
            "success": False,
            "error_type": "processing",
            "message": ErrorHandler.format_error_message("processing", f"Error ID: {error_id}"),
            "error_id": error_id,
            "can_retry": True
        }

    @classmethod
    async def handle_and_respond(cls, error: Exception, operation: str, chat_id: int,
                               telegram_service, conversation_state, details: Dict[str, Any] = None) -> None:
        """Handle error and send appropriate response to user."""
        # Determine error type and handle accordingly
        if "auth" in str(error).lower() or "credential" in str(error).lower():
            error_result = cls.handle_authentication_error(error, operation)
        elif "network" in str(error).lower() or "connection" in str(error).lower():
            error_result = cls.handle_network_error(error, operation)
        elif "calendar" in str(error).lower():
            error_result = cls.handle_api_error(error, "Calendar", operation)
        elif "telegram" in str(error).lower():
            error_result = cls.handle_api_error(error, "Telegram", operation)
        elif "validation" in str(error).lower() or "invalid" in str(error).lower():
            error_result = cls.handle_validation_error(error)
        else:
            error_result = cls.handle_generic_error(error, operation, chat_id)

        # Send error message to user
        await telegram_service.send_telegram_message(chat_id, error_result["message"])
        conversation_state.add_message(chat_id, "assistant", error_result["message"])

    @staticmethod
    def should_retry(error_result: Dict[str, Any], attempt_count: int, max_attempts: int = 3) -> bool:
        """Determine if operation should be retried."""
        if not error_result.get("can_retry", False):
            return False

        return attempt_count < max_attempts

    @staticmethod
    def get_retry_delay(error_result: Dict[str, Any], attempt_count: int) -> int:
        """Get retry delay in seconds based on error type and attempt count."""
        base_delay = error_result.get("retry_delay", 2)
        # Exponential backoff
        return base_delay * (2 ** (attempt_count - 1))
