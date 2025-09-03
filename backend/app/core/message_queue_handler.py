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
        # Track processed message IDs to prevent duplicates
        self.processed_message_ids = defaultdict(set)
    
    def is_duplicate_message(self, chat_id: str, message: str, message_id: Optional[str] = None) -> bool:
        """Check if message is a duplicate of the last message within the time window."""
        last_message, last_timestamp = self.last_messages[chat_id]
        current_time = time.time()
        
        logger.info(f"🔍 DUPLICATE DEBUG: Checking duplicate for chat {chat_id}")
        logger.info(f"🔍 DUPLICATE DEBUG: Current message: '{message}' (ID: {message_id})")
        logger.info(f"🔍 DUPLICATE DEBUG: Last message: '{last_message}' (timestamp: {last_timestamp})")
        logger.info(f"🔍 DUPLICATE DEBUG: Time difference: {current_time - last_timestamp:.2f}s")
        logger.info(f"🔍 DUPLICATE DEBUG: Duplicate window: {DUPLICATE_WINDOW_SECONDS}s")
        
        # Check if same message within time window
        if (message == last_message and 
            current_time - last_timestamp < DUPLICATE_WINDOW_SECONDS):
            logger.info(f"🔒 Duplicate message ignored for chat {chat_id}: '{message}' (within {DUPLICATE_WINDOW_SECONDS}s window)")
            return True
        
        # Check if message ID was already processed
        if message_id and message_id in self.processed_message_ids[chat_id]:
            logger.info(f"🔒 Message ID already processed for chat {chat_id}: {message_id}")
            return True
        
        logger.info(f"🔍 DUPLICATE DEBUG: Message is NOT duplicate for chat {chat_id}")
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
    
    def update_last_message(self, chat_id: str, message: str, message_id: Optional[str] = None) -> None:
        """Update the last message for a chat."""
        current_time = time.time()
        self.last_messages[chat_id] = (message, current_time)
        if message_id:
            self.processed_message_ids[chat_id].add(message_id)
            # Clean up old message IDs to prevent memory issues
            if len(self.processed_message_ids[chat_id]) > 100:
                # Keep only the most recent 50 message IDs
                self.processed_message_ids[chat_id] = set(list(self.processed_message_ids[chat_id])[-50:])
    
    async def process_message(self, chat_id: str, message: str, process_func, message_id: Optional[str] = None) -> Optional[dict]:
        """Process a message with deduplication and queuing logic."""
        try:
            logger.info(f"🔍 QUEUE DEBUG: Starting message processing for chat {chat_id}: '{message}' (ID: {message_id})")
            
            # Check for duplicate message
            if self.is_duplicate_message(chat_id, message, message_id):
                logger.info(f"🔍 QUEUE DEBUG: Message identified as duplicate for chat {chat_id}")
                logger.info(f"🔍 QUEUE DEBUG: Returning ignored status - user will not see any response")
                return {"status": "ignored", "reason": "duplicate"}
            
            logger.info(f"🔍 QUEUE DEBUG: Message is not duplicate, proceeding with processing")
            
            # Update last message
            self.update_last_message(chat_id, message, message_id)
            
            # Check if already processing
            if self.is_processing(chat_id):
                logger.info(f"🔍 QUEUE DEBUG: Chat {chat_id} is already processing, queuing message")
                # Queue message for later processing
                self.queue_message(chat_id, message)
                return {"status": "queued", "reason": "processing_in_progress"}
            
            logger.info(f"🔍 QUEUE DEBUG: Chat {chat_id} is not processing, starting new processing")
            
            # Set processing status
            self.set_processing(chat_id, True)
            
            try:
                # Process the message
                result = await process_func(chat_id, message)
                logger.info(f"🔍 QUEUE DEBUG: Message processing completed for chat {chat_id}")
                return result
            finally:
                # Always clear processing status
                self.set_processing(chat_id, False)
                logger.info(f"🔍 QUEUE DEBUG: Processing status cleared for chat {chat_id}")
                
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
            self.processed_message_ids[chat_id].clear()  # Clear processed message IDs
            logger.info(f"🔒 FORCE RESET: Processing status reset for chat {chat_id}")
        except Exception as e:
            logger.error(f"🔒 FORCE RESET ERROR: Failed to reset processing status for chat {chat_id}: {e}")

# Global instance
message_queue_handler = MessageQueueHandler()
