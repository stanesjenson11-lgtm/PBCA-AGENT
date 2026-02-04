"""
Conversation Memory Manager
Maintains conversation history for contextual responses
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history per user"""
    
    def __init__(self, max_history=10, timeout_minutes=30):
        """
        Args:
            max_history: Maximum number of messages to remember
            timeout_minutes: Clear history after this many minutes of inactivity
        """
        self.conversations = defaultdict(lambda: deque(maxlen=max_history))
        self.last_activity = {}
        self.timeout = timedelta(minutes=timeout_minutes)
    
    def add_message(self, user_id: str, role: str, content: str):
        """
        Add a message to conversation history
        
        Args:
            user_id: User identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        # Clean old conversations
        self._cleanup_old_conversations()
        
        # Add message
        self.conversations[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Update activity
        self.last_activity[user_id] = datetime.now()
        
        logger.info(f"[MEMORY] Added {role} message for user {user_id}. History size: {len(self.conversations[user_id])}")
    
    def get_history(self, user_id: str, max_messages=5):
        """
        Get recent conversation history
        
        Args:
            user_id: User identifier  
            max_messages: Maximum number of recent messages to return
        
        Returns:
            List of message dictionaries
        """
        history = list(self.conversations[user_id])
        return history[-max_messages:] if history else []
    
    def get_context_string(self, user_id: str, max_messages=3):
        """
        Get conversation history as formatted string for prompt
        
        Args:
            user_id: User identifier
            max_messages: Maximum recent messages to include
        
        Returns:
            Formatted conversation history
        """
        history = self.get_history(user_id, max_messages)
        
        if not history:
            return ""
        
        context_parts = ["Recent conversation:"]
        for msg in history:
            role_label = "Sir Jenson" if msg['role'] == 'user' else "Zeic"
            context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_history(self, user_id: str):
        """Clear conversation history for user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            del self.last_activity[user_id]
            logger.info(f"[MEMORY] Cleared history for user {user_id}")
    
    def _cleanup_old_conversations(self):
        """Remove conversations that have been inactive"""
        now = datetime.now()
        to_remove = []
        
        for user_id, last_time in self.last_activity.items():
            if now - last_time > self.timeout:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            self.clear_history(user_id)
            logger.info(f"[MEMORY] Cleaned up inactive conversation for {user_id}")


# Global conversation memory instance
conversation_memory = ConversationMemory()


if __name__ == "__main__":
    # Test conversation memory
    logging.basicConfig(level=logging.INFO)
    
    mem = ConversationMemory()
    
    # Simulate conversation
    mem.add_message("user123", "user", "Hi")
    mem.add_message("user123", "assistant", "Nice to meet you Sir Jenson!")
    mem.add_message("user123", "user", "Tell me a joke")
    mem.add_message("user123", "assistant", "Why don't scientists trust atoms? Because they make up everything!")
    mem.add_message("user123", "user", "That's funny!")
    
    # Get context
    print("\n" + mem.get_context_string("user123"))
    print(f"\nHistory size: {len(mem.get_history('user123'))}")
