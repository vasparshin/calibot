from datetime import datetime
from typing import Dict

class ConversationState:
    def __init__(self):
        self.conversations: Dict[int, list] = {}
        
    def add_message(self, user_id: int, role: str, content: str, message_type: str = "text"):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # CRITICAL FIX: Limit conversation history to prevent LLM confusion
        # Keep only the last 20 messages to maintain context without overwhelming the LLM
        if len(self.conversations[user_id]) >= 20:
            # Remove oldest messages, keeping the most recent 20
            self.conversations[user_id] = self.conversations[user_id][-19:]
        
        self.conversations[user_id].append({
            "role": role,
            "content": content,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_conversation_history(self, user_id: int, max_messages: int = 2) -> list:
        # CRITICAL FIX: Default to only 2 messages for LLM processing
        # This prevents the LLM from being confused by too much context
        return self.conversations.get(user_id, [])[-max_messages:]
    
    def get_recent_messages(self, user_id: int, count: int = 2) -> list:
        """Get the most recent messages for a user"""
        # CRITICAL FIX: Default to only 2 messages for better LLM performance
        return self.conversations.get(user_id, [])[-count:]
    
    def get_operation_history(self, user_id: int, max_operations: int = 1) -> list:
        """Get recent operations for undo functionality"""
        # CRITICAL FIX: Only keep the last operation for undo
        # This prevents confusion and ensures clean undo behavior
        operations = []
        if user_id in self.conversations:
            for msg in reversed(self.conversations[user_id]):
                if msg.get("type") == "operation" and len(operations) < max_operations:
                    operations.append(msg)
        return operations
    
    def remove_system_message(self, user_id: int, content_pattern: str):
        """Remove system messages containing the pattern"""
        if user_id in self.conversations:
            self.conversations[user_id] = [
                msg for msg in self.conversations[user_id]
                if not (msg.get("role") == "system" and content_pattern in msg.get("content", ""))
            ]
    
    def get_data(self, user_id: int, key: str):
        """Get data for a user by key."""
        if user_id not in self.conversations:
            return None
        # Look for data in the conversation metadata
        for msg in reversed(self.conversations[user_id]):
            if msg.get("type") == "data" and msg.get("key") == key:
                return msg.get("data")
        return None
    
    def set_data(self, user_id: int, key: str, data):
        """Set data for a user by key."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Remove existing data with this key
        self.conversations[user_id] = [
            msg for msg in self.conversations[user_id]
            if not (msg.get("type") == "data" and msg.get("key") == key)
        ]
        
        # CRITICAL FIX: Only add new data if it's not None
        # If data is None, we just remove the existing data (clear it)
        if data is not None:
            self.conversations[user_id].append({
                "role": "system",
                "type": "data",
                "key": key,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    
    def delete_data(self, user_id: int, key: str):
        """Delete data for a user by key."""
        if user_id not in self.conversations:
            return
        
        # Remove data with this key
        self.conversations[user_id] = [
            msg for msg in self.conversations[user_id]
            if not (msg.get("type") == "data" and msg.get("key") == key)
        ]

conversation_state = ConversationState()
