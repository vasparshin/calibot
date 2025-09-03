def format_conversation_history(history: list) -> str:
        """Format the conversation history into a structured format with enhanced context"""
        if not history:
            return "No previous conversation."
        
        # CRITICAL FIX: Limit to only 2 previous messages to prevent LLM confusion
        # This prevents the LLM from being overwhelmed with too much context
        # and improves intent classification accuracy
        recent_history = history[-2:] if len(history) > 2 else history
        
        formatted_messages = []
        for i, msg in enumerate(recent_history):
            timestamp = msg.get('timestamp', '')
            role = msg['role'].capitalize()
            content = msg['content']
            
            # Add message number for reference
            message_line = f"[{i+1}] {role}: {content}"
            if timestamp:
                message_line += f" ({timestamp})"
            formatted_messages.append(message_line)
        
        formatted_history = "\n".join(formatted_messages)
        return formatted_history
    