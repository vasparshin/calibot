"""
API handlers for various calendar operations.
This module contains handler functions for processing different types of calendar requests.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def process_update_delete_with_confirmation(
    chat_id: int,
    event_data: Dict,
    calendar_service,
    event_queue_handler,
    multi_event_handler,
    send_telegram_message,
    conversation_state,
) -> Dict[str, Any]:
    """Handle update/delete operations with proper confirmation workflow"""
    try:
        intent = event_data.get("intent")
        logger.info(f"🔧 HANDLERS.PY DEBUG - process_update_delete_with_confirmation called with intent: {intent}")
        
        if intent in ["update", "delete"]:
            logger.info(f"🔧 HANDLERS.PY DEBUG - Processing {intent} operation with event_data: {event_data}")
            
            # Use the multi-event handler to find and process matching events
            if intent == "update":
                logger.info(f"🔧 HANDLERS.PY DEBUG - Calling handle_update_operation")
                result = await multi_event_handler.handle_update_operation(chat_id, event_data)
                logger.info(f"🔧 HANDLERS.PY DEBUG - handle_update_operation returned: {result}")
            else:  # delete
                logger.info(f"🔧 HANDLERS.PY DEBUG - Calling handle_delete_operation")
                result = await multi_event_handler.handle_delete_operation(chat_id, event_data)
                logger.info(f"🔧 HANDLERS.PY DEBUG - handle_delete_operation returned: {result}")
            
            if result.get("requires_user_action"):
                # Send confirmation message with keyboard
                keyboard = result.get("keyboard")
                if keyboard:
                    await send_telegram_message(chat_id, result["message"], reply_markup=keyboard)
                else:
                    await send_telegram_message(chat_id, result["message"])
                conversation_state.add_message(chat_id, "assistant", result["message"])
            else:
                # Send direct result
                await send_telegram_message(chat_id, result["message"])
                conversation_state.add_message(chat_id, "assistant", result["message"])
            
            return {"handled": True, "status": "ok"}
        
        logger.info(f"🔧 HANDLERS.PY DEBUG - Intent {intent} not in update/delete, returning handled=False")
        return {"handled": False}
        
    except Exception as e:
        logger.error(f"🔧 HANDLERS.PY ERROR - Error in process_update_delete_with_confirmation: {e}")
        return {"handled": False, "error": str(e)}


# Placeholder functions for other imports that might be missing
async def query_and_filter_events(*args, **kwargs):
    """Placeholder for query_and_filter_events"""
    logger.warning("query_and_filter_events called but not implemented")
    return {}

async def find_duplicates(*args, **kwargs):
    """Placeholder for find_duplicates"""
    logger.warning("find_duplicates called but not implemented") 
    return []

async def process_batch_creation(*args, **kwargs):
    """Placeholder for process_batch_creation"""
    logger.warning("process_batch_creation called but not implemented")
    return {"handled": False}

async def create_single_event(
    chat_id: int,
    event_data: Dict,
    calendar_service,
    send_telegram_message,
    conversation_state,
) -> Dict[str, Any]:
    """Create a single event and format the response consistently"""
    try:
        # Create the event using calendar service
        calendar_response = await calendar_service.create_event(event_data)
        
        if calendar_response["success"]:
            # Use MessageFormatter for consistent formatting
            try:
                from app.utils.message_formatter import MessageFormatter
                
                # Format the event data for display
                event_for_display = {
                    'summary': event_data.get('event_name', 'Event'),
                    'start': f"{event_data.get('date', '')}T{event_data.get('start_time', '')}:00",
                    'end': f"{event_data.get('date', '')}T{event_data.get('end_time', '')}:00",
                    'calendar_name': calendar_response.get('calendar_used', 'Calendar'),
                    'id': calendar_response.get('event_id', ''),
                    'htmlLink': calendar_response.get('event_link', '')
                }
                
                # Use the centralized formatter for consistency
                formatted_event = MessageFormatter.format_single_event_display(event_for_display, include_hyperlink=True)
                success_msg = f"Event created successfully:\n\n{formatted_event}"
                
            except ImportError:
                # Fallback if MessageFormatter not available
                event_name = event_data.get('event_name', 'Event')
                date = event_data.get('date', 'today')
                start_time = event_data.get('start_time', '')
                end_time = event_data.get('end_time', '')
                calendar_name = calendar_response.get('calendar_used', 'Calendar')
                
                success_msg = f"Event created successfully:\n\n• {event_name} on {date} at {start_time} - {end_time} ({calendar_name})"
            
            await send_telegram_message(chat_id, success_msg)
            conversation_state.add_message(chat_id, "assistant", success_msg)
            
            return {"handled": True, "status": "ok"}
        else:
            error_msg = f"Failed to create event: {calendar_response.get('message', 'Unknown error')}"
            await send_telegram_message(chat_id, error_msg)
            conversation_state.add_message(chat_id, "assistant", error_msg)
            
            return {"handled": True, "status": "error", "message": error_msg}
            
    except Exception as e:
        error_msg = f"Error creating event: {str(e)}"
        await send_telegram_message(chat_id, error_msg)
        conversation_state.add_message(chat_id, "assistant", error_msg)
        
        return {"handled": False, "error": str(e)}

class IntentDispatcher:
    """Placeholder for IntentDispatcher"""
    def __init__(self):
        logger.warning("IntentDispatcher placeholder created")
