async def _cache_operation_for_undo(chat_id: int, intent_data: Dict[str, Any], operation_result: Dict[str, Any]) -> None:
    """Cache the completed operation for undo functionality."""
    try:
        operation_type = intent_data.get("intent", "unknown")
        
        # Only cache operations that can be undone
        if operation_type in ["create", "delete", "update"]:
            cache_data = {
                "operation_type": operation_type,
                "intent_data": intent_data.copy(),
                "operation_result": operation_result.copy(),
                "timestamp": time.time(),
                "chat_id": chat_id
            }
            
            # Store in conversation state under special key
            conversation_state.set_data(chat_id, "last_operation", cache_data)
            logger.info(f"🔄 UNDO CACHE: Stored {operation_type} operation for chat {chat_id}")
        
    except Exception as e:
        logger.warning(f"Failed to cache operation for undo: {e}")

async def _cleanup_stale_keyboards(chat_id: int) -> None:
    """Remove stale inline keyboards when user sends new message.
    
    This prevents users from pressing old buttons after sending new messages,
    which could cause workflow confusion. MANDATORY per user requirement.
    """
    try:
        # CRITICAL FIX: Enhanced cleanup to prevent "going back in time" with old buttons
        
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
        
        # Clear any pending confirmations that might have buttons
        pending_confirmations = conversation_state.get_data(chat_id, "pending_confirmation")
        if pending_confirmations:
            logger.info(f"🧹 CLEANUP: Clearing pending confirmations for chat {chat_id} due to new user message")
            conversation_state.delete_data(chat_id, "pending_confirmation")
        
        # Clear any temporary operation states
        temp_operation = conversation_state.get_data(chat_id, "temp_operation")
        if temp_operation:
            logger.info(f"🧹 CLEANUP: Clearing temp operation for chat {chat_id} due to new user message")
            conversation_state.delete_data(chat_id, "temp_operation")
            
        # Note: We can't directly remove keyboards from existing messages without message IDs
        # But clearing ALL pending operations prevents ANY old buttons from working
        
        logger.info(f"🧹 CLEANUP: Completed stale button cleanup for chat {chat_id} - all old buttons now inactive")
        
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
