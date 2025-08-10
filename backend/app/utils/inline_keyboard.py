"""
Inline keyboard helpers for consistent button formatting.
Implements BOT_RULES.md button specifications.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class InlineKeyboardHelper:
    """Helper class for creating consistent inline keyboards"""
    
    @staticmethod
    def create_multi_event_confirmation_keyboard(action: str = "process") -> Dict:
        """
        Create inline keyboard for multi-event operations
        Buttons: "🔄 All", "1️⃣ One by One", "❌ Cancel" (single row per BOT_RULES.md)
        """
        action_title = action.title()
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔄 All", "callback_data": f"confirm_all_{action}"},
                    {"text": "1️⃣ One by One", "callback_data": f"confirm_one_{action}"},
                    {"text": "❌ Cancel", "callback_data": f"cancel_{action}"}
                ]
            ]
        }
        return keyboard
    
    @staticmethod
    def create_single_event_confirmation_keyboard(action: str = "process") -> Dict:
        """
        Create inline keyboard for single event operations
        Buttons: "✅ Yes", "❌ No"
        """
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Yes", "callback_data": f"confirm_{action}"},
                    {"text": "❌ No", "callback_data": f"cancel_{action}"}
                ]
            ]
        }
        return keyboard
    
    @staticmethod
    def create_duplicate_confirmation_keyboard() -> Dict:
        """
        Create inline keyboard for duplicate detection
        Buttons: "✅ Create Anyway", "❌ Cancel"
        """
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Create Anyway", "callback_data": "confirm_duplicates"},
                    {"text": "❌ Cancel", "callback_data": "cancel_duplicates"}
                ]
            ]
        }
        return keyboard
    
    @staticmethod
    def create_queue_navigation_keyboard(current_index: int, total_count: int, action: str = "process") -> Dict:
        """
        Create inline keyboard for queue navigation (one-by-one processing)
        Buttons: "✅ Yes", "❌ Skip", "🛑 Stop All"
        """
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Yes", "callback_data": f"queue_confirm_{current_index}"},
                    {"text": "❌ Skip", "callback_data": f"queue_skip_{current_index}"}
                ],
                [
                    {"text": "🛑 Stop All", "callback_data": f"queue_stop_all"}
                ]
            ]
        }
        return keyboard
    
    @staticmethod
    def parse_callback_data(callback_data: str) -> Dict[str, str]:
        """
        Parse callback data to extract action and parameters
        Returns dict with action type and relevant parameters
        """
        if not callback_data:
            return {"action": "unknown"}
        
        parts = callback_data.split("_")
        
        if len(parts) < 2:
            return {"action": "unknown"}
        
        action_type = parts[0]  # confirm, cancel, queue
        action_detail = parts[1]  # all, one, duplicates, etc.
        
        result = {
            "action": action_type,
            "detail": action_detail
        }
        
        # Add specific parsing for different callback types
        if action_type == "confirm":
            if action_detail == "all":
                result["operation"] = parts[2] if len(parts) > 2 else "process"
                result["type"] = "multi_all"
            elif action_detail == "one":
                result["operation"] = parts[2] if len(parts) > 2 else "process"
                result["type"] = "multi_one"
            elif action_detail == "duplicates":
                result["type"] = "duplicates"
            else:
                result["operation"] = action_detail
                result["type"] = "single"
        
        elif action_type == "cancel":
            result["operation"] = action_detail if action_detail != "duplicates" else None
            result["type"] = "cancel"
        
        elif action_type == "queue":
            if action_detail == "confirm":
                result["index"] = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                result["type"] = "queue_confirm"
            elif action_detail == "skip":
                result["index"] = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                result["type"] = "queue_skip"
            elif action_detail == "stop":
                result["type"] = "queue_stop"
        
        return result
    
    @staticmethod
    def is_callback_response(text: str) -> bool:
        """Check if text is likely a callback response vs user text input"""
        # This helps distinguish between callback button presses and text responses
        callback_patterns = [
            "confirm_", "cancel_", "queue_", 
            "all_", "one_", "duplicates",
            "stop_all"
        ]
        
        return any(pattern in text.lower() for pattern in callback_patterns)
    
    @staticmethod
    def create_error_keyboard() -> Dict:
        """Create simple keyboard for error scenarios"""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔄 Try Again", "callback_data": "retry"},
                    {"text": "❌ Cancel", "callback_data": "cancel_error"}
                ]
            ]
        }
        return keyboard
