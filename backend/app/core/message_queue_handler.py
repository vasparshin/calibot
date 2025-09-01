"""
Message queue handler for managing message deduplication and queuing.
Prevents duplicate processing and ensures sequential operation execution.
"""

import logging
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from app.config import (
    DUPLICATE_WINDOW_SECONDS, 
    MESSAGE_QUEUE, 
    PROCESSING_STATUS, 
    LAST_MESSAGE
)

logger = logging.getLogger(__name__)

class MessageQueueHandler:
    """Handles message deduplication and queuing to prevent concurrent operations."""
    
    def __init__(self):
        self.message_queues = MESSAGE_QUEUE
        self.processing_status = PROCESSING_STATUS
        self.last_messages = LAST_MESSAGE
    
    def is_duplicate_message(self, chat_id: str, message: str) -> bool:
        """Check if message is a duplicate of the last message within the time window."""
        last_message, last_timestamp = self.last_messages[chat_id]
        current_time = time.time()
        
        # Check if same message within time window
        if (message == last_message and 
            current_time - last_timestamp < DUPLICATE_WINDOW_SECONDS):
            logger.info(f"🔒 Duplicate message ignored for chat {chat_id}: '{message}'")
            return True
        
        return False
    
    def is_processing(self, chat_id: str) -> bool:
        """Check if chat is currently processing an operation."""
        return self.processing_status[chat_id]
    
    def set_processing(self, chat_id: str, is_processing: bool) -> None:
        """Set processing status for a chat."""
        self.processing_status[chat_id] = is_processing
        logger.info(f"🔒 Chat {chat_id} processing status: {is_processing}")
    
    def queue_message(self, chat_id: str, message: str) -> None:
        """Add message to queue for later processing."""
        current_time = time.time()
        self.message_queues[chat_id].append((message, current_time))
        logger.info(f"🔒 Message queued for chat {chat_id}: '{message}' (queue size: {len(self.message_queues[chat_id])})")
    
    def get_queued_messages(self, chat_id: str) -> List[Tuple[str, float]]:
        """Get all queued messages for a chat."""
        return self.message_queues[chat_id]
    
    def clear_queue(self, chat_id: str) -> None:
        """Clear the message queue for a chat."""
        self.message_queues[chat_id].clear()
        logger.info(f"🔒 Message queue cleared for chat {chat_id}")
    
    def update_last_message(self, chat_id: str, message: str) -> None:
        """Update the last message for a chat."""
        current_time = time.time()
        self.last_messages[chat_id] = (message, current_time)
    
    async def process_message(self, chat_id: str, message: str, process_func) -> Optional[dict]:
        """Process a message with deduplication and queuing logic."""
        try:
            # Check for duplicate message
            if self.is_duplicate_message(chat_id, message):
                return {"status": "ignored", "reason": "duplicate"}
            
            # Update last message
            self.update_last_message(chat_id, message)
            
            # Check if already processing
            if self.is_processing(chat_id):
                # Queue message for later processing
                self.queue_message(chat_id, message)
                return {"status": "queued", "reason": "processing_in_progress"}
            
            # Set processing status
            self.set_processing(chat_id, True)
            
            try:
                # Process the message
                result = await process_func(chat_id, message)
                return result
            finally:
                # Always clear processing status
                self.set_processing(chat_id, False)
                
                # Process any queued messages
                await self.process_queued_messages(chat_id, process_func)
                
        except Exception as e:
            logger.error(f"Error in message processing: {e}")
            self.set_processing(chat_id, False)
            raise
    
    async def process_queued_messages(self, chat_id: str, process_func) -> None:
        """Process all queued messages for a chat."""
        queued_messages = self.get_queued_messages(chat_id)
        if not queued_messages:
            return
        
        logger.info(f"🔒 Processing {len(queued_messages)} queued messages for chat {chat_id}")
        
        # Process each queued message
        for message, timestamp in queued_messages:
            try:
                # Check if still a duplicate
                if not self.is_duplicate_message(chat_id, message):
                    self.update_last_message(chat_id, message)
                    self.set_processing(chat_id, True)
                    
                    try:
                        await process_func(chat_id, message)
                        logger.info(f"🔒 Processed queued message for chat {chat_id}: '{message}'")
                    finally:
                        self.set_processing(chat_id, False)
                else:
                    logger.info(f"🔒 Skipped queued duplicate message for chat {chat_id}: '{message}'")
                    
            except Exception as e:
                logger.error(f"Error processing queued message: {e}")
                self.set_processing(chat_id, False)
        
        # Clear the queue after processing
        self.clear_queue(chat_id)

    def force_reset_processing(self, chat_id: str) -> None:
        """Force reset processing status for a chat (recovery mechanism)."""
        try:
            self.processing_status[chat_id] = False
            logger.info(f"🔒 FORCE RESET: Processing status reset for chat {chat_id}")
        except Exception as e:
            logger.error(f"🔒 FORCE RESET ERROR: Failed to reset processing status for chat {chat_id}: {e}")

# Global instance
message_queue_handler = MessageQueueHandler()
