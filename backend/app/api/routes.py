"""
Optimized routes.py using the new operation-based architecture.
Significantly reduced from 1444 lines to a focused, maintainable implementation.
"""

from fastapi import APIRouter, Request, HTTPException
import os
from datetime import datetime
import logging
from typing import Dict, List

from app import __version__

from app.config import GOOGLE_CLIENT_SECRET_FILE, GOOGLE_API_SCOPES
from app.services.telegram import (
    TelegramBotService,
    send_telegram_message,
    answer_callback_query,
    edit_message_text
)
from app.services.google_calendar import GoogleCalendarService
from app.services.conversation import conversation_state
from app.agent.nlp_agent import NLPAgent
from app.agent.calendar_agent import CalendarAgent
from app.core.confirmation_handler import ConfirmationHandler
from app.core.response_manager import ResponseManager
from app.operations.operation_factory import OperationFactory
from app.core.message_queue_handler import message_queue_handler

# Initialize services
router = APIRouter()
telegram_service = TelegramBotService()
calendar_service = GoogleCalendarService()
calendar_agent = CalendarAgent()
ai_agent = NLPAgent()
confirmation_handler = ConfirmationHandler(telegram_service, conversation_state, calendar_service)
response_manager = ResponseManager()
operation_factory = OperationFactory(telegram_service, conversation_state, calendar_service, calendar_agent)

logger = logging.getLogger(__name__)

def _clean_message_for_conversation_state(message: str) -> str:
    """Clean message content before adding to conversation state to prevent LLM corruption.
    
    AGGRESSIVE cleaning to prevent any formatting issues that could corrupt LLM prompts.
    """
    if not message:
        return ""
    
    # AGGRESSIVE: For any multi-line message with complex formatting, simplify drastically
    if '\n' in message and len(message.split('\n')) > 2:
        # Multi-line messages are high risk for LLM corruption
        if "Found" in message and "potential duplicate" in message:
            return "Found potential duplicate events - asking for confirmation"
        elif "Successfully" in message and ("updated" in message or "created" in message or "deleted" in message):
            return "Operation completed successfully"
        elif "•" in message:
            return "Event operation completed with details"
        else:
            # Get just the first meaningful line
            lines = [line.strip() for line in message.split('\n') if line.strip()]
            return lines[0][:100] if lines else "Operation completed"
    
    # AGGRESSIVE: For any message with bullet points, simplify
    if "•" in message:
        if "Found" in message and "potential duplicate" in message:
            return "Found potential duplicate events - asking for confirmation"
        elif "Successfully" in message:
            return "Operation completed successfully"
        else:
            return "Event operation completed"
    
    # AGGRESSIVE: For any message with complex formatting, simplify
    if any(char in message for char in ['[', ']', '(', ')', '✅', '❌', '*', '_']):
        # Remove all special formatting
        cleaned = message
        for char in ['[', ']', '(', ')', '✅', '❌', '*', '_', '`']:
            cleaned = cleaned.replace(char, '')
        
        # Clean up and truncate
        cleaned = ' '.join(cleaned.split())
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + "..."
        return cleaned
    
    # For simple messages, do basic cleanup
    cleaned = message.replace('\n', ' ').replace('\r', '')
    cleaned = ' '.join(cleaned.split())  # Remove multiple spaces
    
    # Truncate very long messages
    if len(cleaned) > 150:
        cleaned = cleaned[:147] + "..."
    
    return cleaned


async def _cleanup_stale_keyboards(chat_id: int) -> None:
    """Remove stale inline keyboards when user sends new message.
    
    This prevents users from pressing old buttons after sending new messages,
    which could cause workflow confusion.
    """
    try:
        # Get recent messages with keyboards from conversation state
        history = conversation_state.get_conversation_history(chat_id)
        
        # Look for recent assistant messages that might have keyboards
        # We'll use the Telegram API to get recent messages and remove keyboards
        # Since we can't easily track which messages have keyboards, 
        # we'll clear any pending operations that would have keyboards
        
        # Clear any pending queue operations
        from app.core.global_instances import get_global_queue_handler
        queue_handler = get_global_queue_handler()
        
        if queue_handler.has_pending_queue(str(chat_id)):
            logger.info(f"🧹 CLEANUP: Clearing pending queue for chat {chat_id} due to new user message")
            queue_handler.clear_queue(str(chat_id))
        
        # Clear any pending duplicate operations
        pending_duplicates = conversation_state.get_data(chat_id, "pending_duplicates")
        if pending_duplicates:
            logger.info(f"🧹 CLEANUP: Clearing pending duplicates for chat {chat_id} due to new user message")
            conversation_state.delete_data(chat_id, "pending_duplicates")
            
        # Note: We can't directly remove keyboards from existing messages without message IDs
        # But clearing the pending operations prevents the buttons from working
        
    except Exception as e:
        logger.error(f"🧹 CLEANUP ERROR: Failed to cleanup stale keyboards for chat {chat_id}: {e}")


def _cleanup_conversation_state_if_corrupted(chat_id: int, conversation_state) -> None:
    """Clean up conversation state if it's causing LLM failures.
    
    This emergency cleanup prevents stuck states after formatting corruption.
    """
    try:
        history = conversation_state.get_conversation_history(chat_id)
        
        # If conversation history is getting long, trim it
        if len(history) > 10:
            logger.warning(f"🧹 Conversation history for chat {chat_id} has {len(history)} messages, trimming to prevent corruption")
            # Keep only the last 6 messages (3 user + 3 assistant pairs)
            conversation_state.conversations[chat_id] = history[-6:]
        
        # Check for problematic patterns in recent messages
        recent_messages = history[-3:] if len(history) >= 3 else history
        for msg in recent_messages:
            content = msg.get('content', '')
            if isinstance(content, str) and (
                len(content) > 500 or 
                content.count('\n') > 5 or 
                '•' in content and '[' in content and ']' in content
            ):
                logger.warning(f"🧹 Found problematic message in conversation history, performing emergency cleanup for chat {chat_id}")
                # Emergency cleanup: keep only simple messages
                simple_history = []
                for msg in history:
                    if msg.get('role') == 'user':
                        simple_history.append(msg)
                    elif msg.get('role') == 'assistant':
                        # Simplify assistant messages
                        simple_msg = {
                            'role': 'assistant',
                            'content': 'Operation completed',
                            'timestamp': msg.get('timestamp')
                        }
                        simple_history.append(simple_msg)
                
                conversation_state.conversations[chat_id] = simple_history[-4:]  # Keep last 2 pairs
                break
                
    except Exception as e:
        logger.error(f"🧹 Error during conversation cleanup for chat {chat_id}: {e}")
        # Emergency reset
        try:
            conversation_state.conversations[chat_id] = []
            logger.warning(f"🧹 Emergency reset conversation state for chat {chat_id}")
        except:
            pass


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram messages and callback queries."""
    try:
        update_data = await request.json()
        logger.debug(f"Received Telegram update: {update_data}")

        # Handle callback queries (inline keyboard button presses)
        if "callback_query" in update_data:
            return await handle_callback_query(update_data["callback_query"])

        # Handle regular messages
        if "message" not in update_data:
            return {"status": "ok"}

        message = update_data["message"]
        chat_id = message["chat"]["id"]
        message_id = str(message.get("message_id", ""))

        if "text" not in message:
            await send_telegram_message(chat_id, "I'm sorry, I didn't understand that. Can you please rephrase your message?")
            return {"status": "ok"}

        user_message = message["text"]
        logger.info(f"👤 User message from chat {chat_id}: '{user_message}'")
        
        # CRITICAL FIX: Remove any stale inline keyboards when user sends new message
        # This prevents users from pressing old buttons after sending new messages
        await _cleanup_stale_keyboards(chat_id)
        
        # Add debug logging for duplicate detection
        logger.info(f"🔍 WEBHOOK DEBUG: Processing message '{user_message}' for chat {chat_id} (ID: {message_id})")
        logger.info(f"🔍 WEBHOOK DEBUG: Message queue handler instance: {id(message_queue_handler)}")

        # Process the message with message ID for duplicate detection
        result = await process_user_message(chat_id, user_message, message_id)
        
        # Add debug logging for result
        logger.info(f"🔍 WEBHOOK DEBUG: Message processing result: {result}")
        
        # CRITICAL FIX: If message was ignored as duplicate, send a helpful response
        if result and result.get("status") == "ignored":
            logger.info(f"🔍 WEBHOOK DEBUG: Sending duplicate message response to user")
            await send_telegram_message(chat_id, "I received your message. Please wait a moment while I process it...")
        
        return result

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_callback_query(callback_query):
    """Handle inline keyboard button presses."""
    try:
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        callback_data = callback_query.get("data", "")
        callback_query_id = callback_query["id"]

        logger.info(f"🔘 Callback query from chat {chat_id}: {callback_data}")

        # Always answer to stop Telegram spinner
        await answer_callback_query(callback_query_id, "Processing...")

        # Add detailed logging for callback debugging
        logger.info(f"🔘 Processing callback: {callback_data}")

        # Handle different callback types
        if callback_data in ["confirm_duplicates", "cancel_duplicates"]:
            return await handle_duplicate_confirmation_callback(chat_id, message_id, callback_data, callback_query)
        elif callback_data.startswith("confirm_all_") or callback_data.startswith("confirm_one_") or callback_data.startswith("cancel_"):
            return await handle_multi_event_confirmation_callback(chat_id, message_id, callback_data, callback_query)
        elif callback_data.startswith("queue_"):
            return await handle_queue_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("confirm_"):
            return await handle_confirmation_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("schedule_"):
            return await handle_schedule_callback(chat_id, message_id, callback_data)
        elif callback_data == "update_one_by_one":
            return await handle_multi_event_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("confirm_update_"):
            return await handle_multi_event_callback(chat_id, message_id, callback_data)
        else:
            logger.warning(f"Unknown callback data: {callback_data}")
            return {"status": "ok"}

    except Exception as e:
        logger.error(f"Callback query error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_multi_event_confirmation_callback(chat_id: int, message_id: int, callback_data: str, callback_query: dict = None):
    """Handle multi-event confirmation callbacks (confirm_all_*, confirm_one_*, cancel_*)."""
    try:
        logger.info(f"🔘 Multi-event callback: {callback_data}")
        
        # Parse callback data
        if callback_data.startswith("confirm_all_"):
            action = callback_data.replace("confirm_all_", "")
            choice = "all"
        elif callback_data.startswith("confirm_one_"):
            action = callback_data.replace("confirm_one_", "")
            choice = "one"
        elif callback_data.startswith("cancel_"):
            action = callback_data.replace("cancel_", "")
            choice = "cancel"
        else:
            logger.warning(f"Unknown multi-event callback format: {callback_data}")
            return {"status": "ok"}
        
        logger.info(f"🔘 Parsed: action={action}, choice={choice}")
        
        processing_message_id = None  # Initialize variable

        # Remove buttons from the original message (preserve content)
        # Get the original message from callback_query and edit to remove only keyboard
        if callback_query and callback_query.get("message", {}).get("text"):
            original_message = callback_query["message"]["text"]
            # Just remove buttons, don't add processing text to summary
            await edit_message_text(
                chat_id, 
                message_id, 
                original_message,  # Keep original content unchanged
                reply_markup={}   # Remove buttons only
            )
            
            # REMOVED: No useless processing message needed
            processing_message_id = None
        else:
            # REMOVED: No useless processing message - just remove buttons
            await edit_message_text(
                chat_id, 
                message_id, 
                message.get('text', 'Operation confirmed'),
                reply_markup={}
            )
            processing_message_id = message_id

        # Handle the choice using the appropriate service
        if action in ["update", "delete", "create"]:
            # CRITICAL FIX: Add "create" action for duplicate handling
            # Use global queue handler to maintain queue state
            from app.core.global_instances import get_global_queue_handler
            queue_handler = get_global_queue_handler()
            
            # Special handling for create action (duplicates)
            if action == "create":
                if choice == "cancel":
                    # Cancel duplicate creation
                    message = "Operation cancelled. No duplicate events were created."
                    if processing_message_id:
                        await edit_message_text(chat_id, processing_message_id, message)
                    else:
                        await send_telegram_message(chat_id, message)
                    return {"status": "ok"}
                elif choice in ["all", "one"]:
                    # Process duplicates using operation factory
                    pending_data = conversation_state.get_data(chat_id, "pending_duplicates")
                    if pending_data:
                        if choice == "all":
                            # Create all duplicates
                            result = await operation_factory.handle_confirmation(chat_id, "duplicates", pending_data)
                        else:
                            # CRITICAL FIX: Implement one-by-one duplicate creation
                            # Convert duplicates to events and use queue handler for one-by-one processing
                            duplicates = pending_data.get("duplicates", [])
                            events_to_create = []
                            
                            for dup in duplicates:
                                if "new_event" in dup:
                                    events_to_create.append(dup["new_event"])
                            
                            if events_to_create:
                                # Create a queue for one-by-one duplicate creation
                                from app.core.global_instances import get_global_queue_handler
                                queue_handler = get_global_queue_handler()
                                
                                # Create queue with create action
                                queue_handler.create_queue(
                                    str(chat_id), 
                                    events_to_create, 
                                    "create", 
                                    one_by_one=True
                                )
                                
                                # Get first confirmation
                                confirmation_result = queue_handler.get_next_event_confirmation(str(chat_id))
                                
                                success_message = confirmation_result.get("message", "Starting one-by-one duplicate creation...")
                                if processing_message_id:
                                    if confirmation_result.get("keyboard"):
                                        await edit_message_text(chat_id, processing_message_id, success_message, reply_markup=confirmation_result["keyboard"])
                                    else:
                                        await edit_message_text(chat_id, processing_message_id, success_message)
                                else:
                                    if confirmation_result.get("keyboard"):
                                        await send_telegram_message(chat_id, success_message, reply_markup=confirmation_result["keyboard"])
                                    else:
                                        await send_telegram_message(chat_id, success_message)
                            else:
                                error_message = "No events found for one-by-one creation."
                                if processing_message_id:
                                    await edit_message_text(chat_id, processing_message_id, error_message)
                                else:
                                    await send_telegram_message(chat_id, error_message)
                            return {"status": "ok"}
                        
                        success_message = result.get("message", "Duplicate events processed")
                        if processing_message_id:
                            await edit_message_text(chat_id, processing_message_id, success_message)
                        else:
                            await send_telegram_message(chat_id, success_message)
                    else:
                        error_message = "No pending duplicate operation found."
                        if processing_message_id:
                            await edit_message_text(chat_id, processing_message_id, error_message)
                        else:
                            await send_telegram_message(chat_id, error_message)
                    return {"status": "ok"}
            
            logger.info(f"🔍 CALLBACK DEBUG: Using queue handler instance ID: {id(queue_handler)}")
            logger.info(f"🔍 CALLBACK DEBUG: Queue handler has {len(queue_handler.pending_queues)} pending queues")
            logger.info(f"🔍 CALLBACK DEBUG: Queue keys: {list(queue_handler.pending_queues.keys())}")
            logger.info(f"🔍 CALLBACK DEBUG: Looking for chat_id: {str(chat_id)}")
            logger.info(f"🔍 CALLBACK DEBUG: Has pending queue: {queue_handler.has_pending_queue(str(chat_id))}")
            
            if choice == "all":
                logger.info(f"🔍 CALLBACK DEBUG: Processing ALL events for {action}")
                result = await queue_handler._process_all_events(str(chat_id))
                success_message = result.get("message", f"Processed all {action} operations")
                
                # Replace the processing message with success message
                if processing_message_id:
                    await edit_message_text(chat_id, processing_message_id, success_message)
                else:
                    await send_telegram_message(chat_id, success_message)
                return {"status": "ok"}
            elif choice == "one":
                # Start one-by-one processing
                # CRITICAL FIX: Set the queue to one-by-one mode before getting confirmation
                if queue_handler.has_pending_queue(str(chat_id)):
                    queue = queue_handler.pending_queues[str(chat_id)]
                    queue['one_by_one_mode'] = True
                    queue['current_index'] = 0  # Reset to first event
                
                result = queue_handler.get_next_event_confirmation(str(chat_id))
                if result.get("keyboard"):
                    await send_telegram_message(chat_id, result["message"], reply_markup=result["keyboard"])
                else:
                    await send_telegram_message(chat_id, result["message"])
                return {"status": "ok"}
            elif choice == "cancel":
                # Cancel operation
                if queue_handler.has_pending_queue(str(chat_id)):
                    queue = queue_handler.pending_queues[str(chat_id)]
                    total_events = len(queue.get('events', []))
                    del queue_handler.pending_queues[str(chat_id)]
                    message = f"Operation cancelled. No events were {action}d."
                else:
                    message = "Operation cancelled."
                
                # Replace the processing message with result message
                if processing_message_id:
                    await edit_message_text(chat_id, processing_message_id, message)
                else:
                    await send_telegram_message(chat_id, message)
        
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Multi-event callback error: {e}")
        await send_telegram_message(chat_id, f"Error processing {callback_data}: {str(e)}")
        return {"status": "error"}

async def handle_confirmation_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle confirmation callbacks."""
    try:
        logger.info(f"🔘 Single confirmation callback: {callback_data}")
        
        # Parse confirmation type
        confirmation = callback_data.replace("confirm_", "")
        
        # CRITICAL FIX: Check for actual confirmation vs cancellation
        # For single event operations, "confirm_delete" means YES (confirm the deletion)
        # For single event operations, "cancel_delete" means NO (cancel the deletion)
        is_confirmed = callback_data.startswith("confirm_")  # This is YES
        is_cancelled = callback_data.startswith("cancel_")   # This is NO
        
        logger.info(f"🔘 Parsed confirmation: '{confirmation}', confirmed: {is_confirmed}, cancelled: {is_cancelled}")

        # Use confirmation handler with correct boolean
        await confirmation_handler.handle_single_confirmation(chat_id, message_id, is_confirmed)

        # Process the confirmation through operation factory with correct action
        if is_confirmed:
            result = await operation_factory.handle_confirmation(chat_id, confirmation, {})
        else:
            # Handle cancellation
            result = {"success": True, "message": "Operation cancelled.", "requires_user_action": False}

        if result.get("requires_user_action"):
            # Send follow-up message if needed
            await confirmation_handler.send_follow_up_message(
                chat_id,
                result.get("message", "Processing..."),
                result.get("keyboard")
            )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Confirmation callback error: {e}")
        return {"status": "error"}

async def handle_duplicate_confirmation_callback(chat_id: int, message_id: int, callback_data: str, callback_query: dict = None):
    """Handle duplicate event confirmation callbacks (confirm_duplicates, cancel_duplicates)."""
    try:
        logger.info(f"🔘 Duplicate event callback: {callback_data}")
        
        # Parse confirmation type
        confirmation = callback_data.replace("confirm_", "").replace("cancel_", "")
        
        # CRITICAL FIX: Check for actual confirmation vs cancellation
        is_confirmed = callback_data.startswith("confirm_")  # This is YES
        is_cancelled = callback_data.startswith("cancel_")   # This is NO
        
        logger.info(f"🔘 Parsed confirmation: '{confirmation}', confirmed: {is_confirmed}, cancelled: {is_cancelled}")

        # Use confirmation handler with correct boolean
        await confirmation_handler.handle_duplicate_confirmation(chat_id, message_id, is_confirmed)

        # Process the confirmation through operation factory with correct action
        if is_confirmed:
            # CRITICAL FIX: Get pending data and pass it to operation factory
            pending_data = conversation_state.get_data(chat_id, "pending_duplicates")
            if pending_data:
                result = await operation_factory.handle_confirmation(chat_id, confirmation, pending_data)
            else:
                result = {"success": False, "message": "No pending duplicate operation found."}
        else:
            # Handle cancellation
            result = {"success": True, "message": "Operation cancelled.", "requires_user_action": False}

        if result.get("requires_user_action"):
            # Send follow-up message if needed
            await confirmation_handler.send_follow_up_message(
                chat_id,
                result.get("message", "Processing..."),
                result.get("keyboard")
            )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Duplicate event confirmation callback error: {e}")
        return {"status": "error"}

async def handle_queue_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle queue navigation callbacks."""
    try:
        logger.info(f"🔘 Queue callback: {callback_data}")
        
        # Parse queue action
        action = callback_data.replace("queue_", "")
        logger.info(f"🔘 Queue action: {action}")

        # Use global queue handler for queue actions
        from app.core.global_instances import get_global_queue_handler
        queue_handler = get_global_queue_handler()
        
        if action.startswith("confirm_"):
            # Handle individual event confirmation (e.g., "confirm_0", "confirm_1")
            event_index = action.replace("confirm_", "")
            if event_index.isdigit():
                # Process this specific event confirmation
                result = await queue_handler.process_queue_response(str(chat_id), "yes")
                if result.get("success"):
                    if result.get("queue_complete"):
                        # All events processed - replace current message with final result
                        await edit_message_text(chat_id, message_id, result["message"], reply_markup={})
                    else:
                        # More events to process - replace current message with next event confirmation
                        next_confirmation = result.get("next_confirmation")
                        if next_confirmation and next_confirmation.get("keyboard"):
                            await edit_message_text(chat_id, message_id, next_confirmation["message"], reply_markup=next_confirmation["keyboard"])
                        else:
                            await edit_message_text(chat_id, message_id, result["message"], reply_markup={})
                else:
                    await edit_message_text(chat_id, message_id, result.get("message", "Error processing event"), reply_markup={})
                    
        elif action.startswith("skip_"):
            # Handle skip event (e.g., "skip_0", "skip_1")
            result = await queue_handler.process_queue_response(str(chat_id), "skip")
            if result.get("success"):
                if result.get("queue_complete"):
                    # All events processed - replace current message with final result
                    await edit_message_text(chat_id, message_id, result["message"], reply_markup={})
                else:
                    # More events to process - replace current message with next event confirmation
                    next_confirmation = result.get("next_confirmation")
                    if next_confirmation and next_confirmation.get("keyboard"):
                        await edit_message_text(chat_id, message_id, next_confirmation["message"], reply_markup=next_confirmation["keyboard"])
                    else:
                        await edit_message_text(chat_id, message_id, result["message"], reply_markup={})
            else:
                await edit_message_text(chat_id, message_id, result.get("message", "Error skipping event"), reply_markup={})
                
        elif action == "stop_all":
            # Cancel remaining queue
            if queue_handler.has_pending_queue(str(chat_id)):
                queue_handler.clear_queue(str(chat_id))
                await edit_message_text(chat_id, message_id, "Operation cancelled. Remaining events were not processed.", reply_markup={})
            else:
                await edit_message_text(chat_id, message_id, "No pending operations to cancel.", reply_markup={})

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Queue callback error: {e}")
        await send_telegram_message(chat_id, f"Error processing queue action: {str(e)}")
        return {"status": "error"}

async def handle_schedule_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle schedule button callbacks."""
    try:
        # Parse schedule type
        schedule_type = callback_data.replace("schedule_", "")

        # Remove keyboard from original message
        await edit_message_text(chat_id, message_id, "📅 Loading schedule...", reply_markup={})

        # Handle schedule request
        result = await handle_schedule_request(chat_id, schedule_type)

        # Send result as new message
        if result.get("success"):
            await send_telegram_message(chat_id, result["message"])
        else:
            error_msg = result.get("message", "Failed to get schedule")
            await send_telegram_message(chat_id, error_msg)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Schedule callback error: {e}")
        return {"status": "error"}

async def handle_multi_event_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle multi-event operation callbacks."""
    try:
        # Use confirmation handler for multi-event operations
        if callback_data == "update_one_by_one":
            await confirmation_handler.handle_multi_confirmation(chat_id, message_id, "one", "update")
        elif callback_data.startswith("confirm_update_"):
            # Extract confirmation number and handle as single confirmation
            parts = callback_data.split("_")
            if len(parts) >= 3 and parts[-1].isdigit():
                confirmation_num = int(parts[-1])
                confirmed = parts[1] == "update"  # This might need adjustment based on actual logic
                await confirmation_handler.handle_single_confirmation(chat_id, message_id, confirmed, f"update event {confirmation_num}")
        else:
            logger.warning(f"Unhandled multi-event callback: {callback_data}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Multi-event callback error: {e}")
        return {"status": "error"}

async def process_user_message(chat_id: int, user_message: str, message_id: str):
    """Process user message through the optimized pipeline with deduplication and queuing."""
    try:
        # Use message queue handler for deduplication and queuing
        result = await message_queue_handler.process_message(
            str(chat_id), 
            user_message, 
            _process_single_message,
            message_id # Pass message_id to the queue handler
        )
        
        if result and result.get("status") == "ignored":
            logger.info(f"🔒 Ignored duplicate message from chat {chat_id}")
            return {"status": "ok"}
        elif result and result.get("status") == "queued":
            logger.info(f"🔒 Message queued for chat {chat_id}: {result.get('reason')}")
            return {"status": "ok"}
        
        return result or {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Message processing error: {e}")
        await send_telegram_message(chat_id, "I'm experiencing technical difficulties. Please try again in a moment.")
        return {"status": "error"}

async def _process_single_message(chat_id: str, user_message: str):
    """Process a single message (internal function for queue handler)."""
    chat_id_int = int(chat_id)
    
    try:
        # Check authentication
        if not await check_authentication(chat_id_int):
            return {"status": "ok"}

        # Add message to conversation
        conversation_state.add_message(chat_id_int, "user", user_message)

        # Check relevancy first for small talk handling
        history = conversation_state.get_conversation_history(chat_id_int)
        logger.info(f"🔍 RELEVANCY DEBUG: About to check relevancy for message: '{user_message}'")
        logger.info(f"🔍 RELEVANCY DEBUG: Conversation history length: {len(history)} messages")
        
        # Log the actual conversation history content to debug formatting issues
        for i, msg in enumerate(history[-3:]):  # Last 3 messages only
            logger.info(f"🔍 CONVERSATION DEBUG {i}: Role={msg.get('role')}, Content='{msg.get('content', '')[:100]}{'...' if len(str(msg.get('content', ''))) > 100 else ''}'")
            if len(str(msg.get('content', ''))) > 200:
                logger.warning(f"🔍 CONVERSATION WARNING: Message {i} is very long ({len(str(msg.get('content', '')))} chars) - potential corruption source")
        
        try:
            relevancy_result = await ai_agent.check_relevancy(user_message, history)
            logger.info(f"🔍 RELEVANCY DEBUG: Relevancy check completed successfully: {relevancy_result}")
        except Exception as relevancy_error:
            logger.error(f"🔍 RELEVANCY DEBUG: Relevancy check failed: {relevancy_error}")
            # If relevancy check fails, assume it's relevant and continue to intent extraction
            relevancy_result = {"relevant": True}
        
        if not relevancy_result.get("relevant", True):
            # Handle small talk or irrelevant messages
            logger.info(f"🔍 SMALL_TALK DEBUG: Message marked as irrelevant, getting small talk response")
            from app.services.ai_service import get_small_talk_response
            
            try:
                small_talk_response = await get_small_talk_response(user_message, history)
                logger.info(f"🔍 SMALL_TALK DEBUG: Small talk response completed: {small_talk_response}")
            except Exception as small_talk_error:
                logger.error(f"🔍 SMALL_TALK DEBUG: Small talk response failed: {small_talk_error}")
                small_talk_response = None
            if small_talk_response and small_talk_response.strip():
                await send_telegram_message(chat_id_int, small_talk_response.strip())
                clean_message = _clean_message_for_conversation_state(small_talk_response.strip())
                conversation_state.add_message(chat_id_int, "assistant", clean_message)
            else:
                await send_telegram_message(chat_id_int, "Hi! I'm CaliBOT, your calendar assistant. How can I help you with your schedule today?")
                conversation_state.add_message(chat_id_int, "assistant", "Hi! I'm CaliBOT, your calendar assistant. How can I help you with your schedule today?")
            return {"status": "ok"}

        # CRITICAL: Clean up conversation state if it might be corrupted
        _cleanup_conversation_state_if_corrupted(chat_id_int, conversation_state)

        # Extract intent using NLP agent for calendar-related messages
        logger.info(f"🔍 INTENT DEBUG: About to extract intent for message: '{user_message}'")
        logger.info(f"🔍 INTENT DEBUG: Using conversation history with {len(history)} messages")
        
        try:
            intent_result = await ai_agent.extract_intent(user_message, history)
            logger.info(f"🔍 INTENT DEBUG: Intent extraction completed successfully: {intent_result}")
        except Exception as intent_error:
            error_str = str(intent_error)
            if "'content'" in error_str:
                # CRITICAL: This is the LLM response structure corruption issue
                logger.error(f"🧹 Detected LLM response structure corruption for chat {chat_id_int}: {intent_error}")
                # Emergency conversation state cleanup
                try:
                    conversation_state.conversations[chat_id_int] = []
                    logger.warning(f"🧹 Emergency reset conversation state for chat {chat_id_int} due to LLM corruption")
                except:
                    pass
                
                await send_telegram_message(chat_id_int, "I'm having trouble processing your request right now. Let's start fresh - what can I help you with?")
                return {"status": "ok"}
            else:
                # Other intent extraction errors
                logger.error(f"Intent extraction error for chat {chat_id_int}: {intent_error}")
                await send_telegram_message(chat_id_int, "Sorry, I had trouble understanding your request. Could you please try again?")
                return {"status": "ok"}

        if not intent_result or not isinstance(intent_result, dict):
            await send_telegram_message(chat_id_int, "Sorry, I had trouble understanding your request. Could you please try again?")
            return {"status": "ok"}

        # Debug logging for operation execution
        logger.info(f"🎯 Executing operation for intent: {intent_result.get('intent')}")
        logger.info(f"🎯 Intent data: {intent_result}")

        # Execute operation through factory
        result = await operation_factory.execute_operation(chat_id_int, intent_result)

        # Debug logging for operation result
        logger.info(f"📊 Operation result: success={result.get('success')}, requires_llm={result.get('requires_llm_formatting')}, requires_action={result.get('requires_user_action')}")

        # Handle result
        if result.get("requires_llm_formatting"):
            # LLM-driven query result - pass data back to LLM for final response formatting
            await handle_llm_formatted_query(chat_id_int, intent_result, result, history)
        elif result.get("requires_user_action"):
            # CRITICAL FIX: Always send messages for requires_user_action
            # This includes duplicate confirmations and other user action requests
            message = result.get("message", "Please confirm your action:")
            keyboard = result.get("keyboard")
            
            # Send message with keyboard if present
            if keyboard:
                await send_telegram_message(chat_id_int, message, reply_markup=keyboard)
            else:
                await send_telegram_message(chat_id_int, message)
            
            # CRITICAL FIX: Clean message before adding to conversation state to prevent LLM corruption
            clean_message = _clean_message_for_conversation_state(message)
            conversation_state.add_message(chat_id_int, "assistant", clean_message)
        elif result.get("success"):
            # Send success message and add to conversation state for undo functionality
            message = result["message"]
            await send_telegram_message(chat_id_int, message)
            # CRITICAL FIX: Clean message before adding to conversation state to prevent LLM corruption
            clean_message = _clean_message_for_conversation_state(message)
            conversation_state.add_message(chat_id_int, "assistant", clean_message)  # CRITICAL: Store for undo
        else:
            # Send error message and add to conversation state
            error_msg = result.get("message", "An error occurred while processing your request.")
            await send_telegram_message(chat_id_int, error_msg)
            # CRITICAL FIX: Clean message before adding to conversation state to prevent LLM corruption
            clean_message = _clean_message_for_conversation_state(error_msg)
            conversation_state.add_message(chat_id_int, "assistant", clean_message)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Single message processing error: {e}")
        # CRITICAL FIX: Ensure processing status is reset even when exceptions occur
        try:
            message_queue_handler.set_processing(chat_id, False)
            logger.info(f"🔒 CRITICAL FIX: Reset processing status for chat {chat_id} after exception")
        except Exception as reset_error:
            logger.error(f"🔒 CRITICAL ERROR: Failed to reset processing status for chat {chat_id}: {reset_error}")
        
        await send_telegram_message(chat_id_int, "I'm experiencing technical difficulties. Please try again in a moment.")
        return {"status": "error"}

async def handle_llm_formatted_query(chat_id: int, original_intent: Dict, query_result: Dict, conversation_history: List):
    """Handle LLM-driven query results by passing data back to LLM for final response formatting."""
    try:
        # Extract query data
        query_data = query_result.get("query_result", {})

        # Check for authentication requirement
        if query_data.get("auth_required"):
            auth_message = "Please authenticate with Google Calendar first: /start"
            await send_telegram_message(chat_id, auth_message)
            return

        # Format events data for LLM
        events_data = format_events_for_llm(query_data.get("events", []))
        query_params = query_data.get("query_params", {})

        # Create LLM prompt for response formatting
        formatting_prompt = f"""
You received this query from the user: "{original_intent.get('original_message', '')}"

I retrieved the following calendar data:
{events_data}

Query parameters used: {query_params}

Based on the user's request and the retrieved data, provide a natural, helpful response.
If no events were found, explain this clearly and suggest alternatives if appropriate.

CRITICAL: Format ALL events using this EXACT format (MANDATORY):
• [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)

Examples:
• [Math Lesson](https://calendar.google.com/calendar/event?eid=abc123) on Monday, September 02, 2025 at 09:00 AM - 10:00 AM (Personal)
• [Team Meeting](https://calendar.google.com/calendar/event?eid=def456) on Tuesday, September 03, 2025 at 02:00 PM - 03:00 PM (Work)

RULES:
- ALWAYS use bullet points (•)
- ALWAYS create hyperlinks with [Event Name](link)
- ALWAYS use full date format: Day, Month DD, YYYY
- ALWAYS use 12-hour time format with AM/PM
- ALWAYS include calendar name in parentheses
- Use the Link field from the event data for hyperlinks

Return only the response message that should be sent to the user.
"""

        # Get LLM response
        try:
            llm_response = await ai_agent.generate_response(formatting_prompt, conversation_history)
            if llm_response and llm_response.strip():
                response_message = llm_response.strip()
                await send_telegram_message(chat_id, response_message)
                # CRITICAL FIX: Clean message before adding to conversation state to prevent LLM corruption
                clean_message = _clean_message_for_conversation_state(response_message)
                conversation_state.add_message(chat_id, "assistant", clean_message)  # CRITICAL: Store for undo
            else:
                fallback_message = "I found some information but couldn't format it properly. Please try rephrasing your request."
                await send_telegram_message(chat_id, fallback_message)
                clean_message = _clean_message_for_conversation_state(fallback_message)
                conversation_state.add_message(chat_id, "assistant", clean_message)
        except Exception as llm_error:
            logger.error(f"LLM formatting error: {llm_error}")
            # Fallback: provide basic formatted response
            await send_basic_query_response(chat_id, query_data)

    except Exception as e:
        logger.error(f"Error in LLM formatted query: {e}")
        await send_telegram_message(chat_id, "I encountered an error while processing your query. Please try again.")

def format_events_for_llm(events: List[Dict]) -> str:
    """Format events data for LLM consumption."""
    if not events:
        return "No events found matching the query criteria."

    formatted_events = []
    for i, event in enumerate(events, 1):
        event_info = f"""
Event {i}:
- Title: {event.get('summary', 'Untitled')}
- Start: {event.get('start', 'Unknown')}
- End: {event.get('end', 'Unknown')}
- Calendar: {event.get('calendar_name', 'Unknown')}
- Link: {event.get('link', 'N/A')}
"""
        formatted_events.append(event_info)

    return f"Found {len(events)} event(s):\n" + "\n".join(formatted_events)

async def send_basic_query_response(chat_id: int, query_data: Dict):
    """Send a basic formatted response when LLM formatting fails."""
    try:
        events = query_data.get("events", [])
        event_count = query_data.get("event_count", 0)

        if event_count == 0:
            await send_telegram_message(chat_id, "No events found matching your query.")
        elif event_count == 1:
            event = events[0]
            message = f"Found 1 event:\n\n{event.get('summary', 'Untitled')} at {event.get('start', 'Unknown time')}"
            await send_telegram_message(chat_id, message)
        else:
            message = f"Found {event_count} events:\n\n"
            for i, event in enumerate(events[:5], 1):  # Show first 5 events
                message += f"{i}. {event.get('summary', 'Untitled')} at {event.get('start', 'Unknown time')}\n"
            if event_count > 5:
                message += f"\n... and {event_count - 5} more events"
            await send_telegram_message(chat_id, message)
    except Exception as e:
        logger.error(f"Error in basic query response: {e}")
        await send_telegram_message(chat_id, "I found some events but had trouble formatting the response.")

async def check_authentication(chat_id: int) -> bool:
    """Check if user is authenticated and handle auth flow."""
    try:
        auth_check = calendar_service.is_authenticated()

        if not auth_check:
            try:
                auth_url = calendar_service.get_auth_url(force_fresh=True)
                await send_telegram_message(
                    chat_id,
                    f"To use this bot, please authenticate your Google account: [Click here]({auth_url})\n\n"
                    f"If you encounter any authentication errors, please check the OAuth configuration or contact support."
                )
            except ValueError as ve:
                logger.error(f"OAuth configuration error: {ve}")
                await send_telegram_message(
                    chat_id,
                    "❌ Authentication system is not properly configured. Please contact the administrator.\n\n"
                    f"Error details: {str(ve)}"
                )
            except Exception as e:
                logger.error(f"Unexpected authentication error: {e}")
                await send_telegram_message(
                    chat_id,
                    "❌ Authentication system is temporarily unavailable. Please try again later or contact support.\n\n"
                    "For immediate assistance, visit: https://calibot-utq6.onrender.com/auth/status"
                )
            return False

        return True

    except Exception as e:
        logger.error(f"Authentication check error: {e}")
        await send_telegram_message(chat_id, "Authentication system error. Please try again later.")
        return False

async def handle_schedule_request(chat_id: int, request: str) -> dict:
    """Handle schedule-related requests."""
    try:
        # Use schedule service if available
        from app.services.schedule_service import ScheduleService
        schedule_service = ScheduleService(calendar_service)

        schedule_type = schedule_service.detect_schedule_query(request)

        if schedule_type:
            if schedule_type == "today":
                result = await schedule_service.get_today_schedule(chat_id)
            elif schedule_type == "tomorrow":
                result = await schedule_service.get_tomorrow_schedule(chat_id)
            elif schedule_type in ["day after tomorrow", "next week"]:
                result = await schedule_service.get_schedule_for_relative_date(schedule_type, chat_id)
            else:
                return None

            if result.get("success"):
                return {
                    "success": True,
                    "message": result["message"],
                    "handled": True
                }
            else:
                error_msg = result.get("message", "Failed to get schedule")
                if result.get("auth_required"):
                    error_msg = "Please authenticate with Google Calendar first: /start"
                return {
                    "success": False,
                    "message": error_msg,
                    "handled": True
                }

        return None

    except Exception as e:
        logger.error(f"Schedule request error: {e}")
        return {
            "success": False,
            "message": "Sorry, there was an error loading your schedule.",
            "handled": True
        }

# OAuth endpoints (unchanged)
@router.get("/oauth2callback")
async def oauth_callback(request: Request):
    """Handle Google OAuth callback."""
    logger.info(f"Received OAuth callback with code: {request.query_params.get('code')}")
    return await calendar_service.handle_oauth_callback(request)

@router.get("/auth/status")
async def auth_status():
    """Check authentication status and OAuth configuration"""
    try:
        status = {
            "authenticated": calendar_service.is_authenticated(),
            "credentials_file_configured": bool(GOOGLE_CLIENT_SECRET_FILE),
            "credentials_file_exists": bool(GOOGLE_CLIENT_SECRET_FILE and os.path.exists(GOOGLE_CLIENT_SECRET_FILE)),
            "redirect_uri": calendar_service.redirect_uri,
            "scopes": GOOGLE_API_SCOPES
        }

        # Add OAuth client configuration details
        if GOOGLE_CLIENT_SECRET_FILE and os.path.exists(GOOGLE_CLIENT_SECRET_FILE):
            try:
                import json
                with open(GOOGLE_CLIENT_SECRET_FILE, 'r') as f:
                    client_config = json.load(f)

                if 'web' in client_config:
                    web_config = client_config['web']
                    status["oauth_client_type"] = "web"
                    status["client_id"] = web_config.get('client_id', 'Not found')
                    status["configured_redirect_uris"] = web_config.get('redirect_uris', [])
                    status["redirect_uri_match"] = calendar_service.redirect_uri in web_config.get('redirect_uris', [])
                else:
                    status["oauth_client_type"] = "unknown"
                    status["error"] = "OAuth client not configured as 'Web application'"

            except Exception as e:
                status["credentials_file_error"] = str(e)

        if not status["authenticated"]:
            try:
                auth_url = calendar_service.get_auth_url(force_fresh=True)
                status["auth_url"] = auth_url
            except Exception as e:
                status["auth_error"] = str(e)

        return status
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {"error": str(e)}

@router.get("/auth/login")
async def login():
    """Initiate OAuth login flow"""
    try:
        if calendar_service.is_authenticated():
            return {"message": "Already authenticated", "authenticated": True}

        auth_url = calendar_service.get_auth_url(force_fresh=True)
        return {"auth_url": auth_url, "message": "Please visit the auth_url to authenticate"}
    except ValueError as ve:
        logger.error(f"OAuth configuration error in login endpoint: {ve}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth configuration error: {str(ve)}. Please ensure the OAuth client is configured as 'Web application' in Google Cloud Console."
        )
    except Exception as e:
        logger.error(f"Error initiating login: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")

@router.get("/auth/fresh")
async def get_fresh_auth_url():
    """Get a guaranteed fresh OAuth authentication URL with cache-busting"""
    try:
        if calendar_service.is_authenticated():
            return {
                "message": "Already authenticated",
                "authenticated": True,
                "fresh_auth_url": calendar_service.get_auth_url(force_fresh=True),
                "note": "You can use the fresh_auth_url to re-authenticate if needed"
            }

        auth_url = calendar_service.get_auth_url(force_fresh=True)
        return {
            "auth_url": auth_url,
            "message": "Fresh OAuth URL generated with cache-busting",
            "instructions": "Please visit the auth_url to authenticate. This URL includes cache-busting to prevent old URL issues."
        }
    except Exception as e:
        logger.error(f"Error generating fresh auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate fresh auth URL: {str(e)}")

# Calendar endpoints
@router.get("/calendars")
async def get_calendars():
    """Get all available calendars with theme information"""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Authentication required")

    calendars = await calendar_service.get_available_calendars()
    return {"calendars": calendars}

@router.post("/calendars/suggest")
async def suggest_calendar(data: dict):
    """Get calendar suggestions based on event data or query"""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Authentication required")

    event_data = data.get("event_data", {})
    query = data.get("query", "")

    suggestions = await calendar_service.suggest_calendar(event_data, query)
    return {"suggestions": suggestions}

# Root endpoint
@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CaliBOT - AI Calendar Bot is running",
        "version": __version__,
        "status": "operational"
    }
