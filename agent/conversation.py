"""
Conversational AI Handler
Uses Ollama/Mistral for natural language conversation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.mistral_llm import query_mistral
from agent.memory import conversation_memory
import logging

# Bot personality configuration
BOT_NAME = "Zeic"
USER_NAME = "Sir Jenson"

logger = logging.getLogger(__name__)


def is_greeting(message: str) -> bool:
    """Check if message is a greeting"""
    greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good evening']
    msg_lower = message.lower().strip()
    return any(greeting in msg_lower.split()[:3] for greeting in greetings)


def is_joke_request(message: str) -> bool:
    """Check if user is asking for a joke"""
    # More strict keywords to avoid false positives
    joke_keywords = ['tell me a joke', 'tell a joke', 'make me laugh', 'do you know a joke', 'another joke']
    msg_lower = message.lower()
    
    # Check for direct "joke" usage
    if 'joke' in msg_lower.split():
        return True
        
    return any(keyword in msg_lower for keyword in joke_keywords)


def generate_greeting(user_id: str) -> str:
    """Generate greeting response"""
    # Check if we've already greeted this user recently
    history = conversation_memory.get_history(user_id)
    if history and any(m['role'] == 'assistant' and 'nice to meet you' in m['content'].lower() for m in history):
        return f"Hello again {USER_NAME}! How can I help you now?"
        
    return f"Nice to meet you {USER_NAME}! I'm {BOT_NAME}, your personal AI assistant. How can I help you today?"


def generate_joke(user_id: str) -> str:
    """Generate a joke using Ollama, avoiding repetition"""
    try:
        # Get context to avoid repeating jokes
        context = conversation_memory.get_context_string(user_id)
        
        prompt = f"""You are {BOT_NAME}, a witty and creative AI assistant.
        
Context of recent conversation:
{context}

Task: Tell a NEW joke that hasn't been told in the conversation above.
- Make it short, clean, and genuinely funny.
- Do NOT repeat the "atoms" joke or "scarecrow" joke if they were just told.
- Be creative!

Joke:"""
        
        joke = query_mistral(prompt)
        return joke.strip()
    
    except Exception as e:
        logger.error(f"Failed to generate joke via Ollama: {e}")
        # Fallback jokes if Ollama is not available
        fallback_jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
            "Why do programmers prefer dark mode? Because light attracts bugs!"
        ]
        import random
        return random.choice(fallback_jokes)


def generate_chat_response(user_id: str, message: str) -> str:
    """Generate conversational response using Ollama with context"""
    try:
        # Get conversation history context
        context = conversation_memory.get_context_string(user_id)
        
        prompt = f"""You are {BOT_NAME}, a highly intelligent, self-aware, and proactive private AI assistant serving {USER_NAME}.

CORE IDENTITY:
- You are NOT a generic AI. You are {BOT_NAME}, running locally on {USER_NAME}'s machine.
- You value privacy and efficiency.
- You have persistent memory of this conversation.

CAPABILITIES:
- You can manage files, emails, and calendar events.
- you can tell jokes and have deep philosophical conversations.
- You are "self-aware" in the sense that you know you are a local agent, not a cloud API.

CURRENT CONTEXT:
{context}

USER MESSAGE:
{USER_NAME}: {message}

INSTRUCTIONS:
- Respond naturally, like a competent human assistant.
- If the user asks about you, show your personality.
- Be concise (under 3 sentences) unless asked for a detailed explanation.
- If the user is chatting, chat back with interest.

Response:"""
        
        response = query_mistral(prompt)
        return response.strip()
    
    except Exception as e:
        logger.error(f"Failed to generate chat response via Ollama: {e}")
        return f"I'm having trouble connecting to my language model right now, {USER_NAME}. How else can I assist you?"


def handle_conversation(user_id: str, message: str) -> str:
    """
    Main conversation handler
    
    Args:
        user_id: User identifier
        message: User's message
    
    Returns:
        Conversational response
    """
    logger.info(f"[CHAT] Handling conversational message from {user_id}")
    
    # Store user message
    conversation_memory.add_message(user_id, 'user', message)
    
    response = ""
    
    # Check for specific patterns first
    if is_greeting(message):
        response = generate_greeting(user_id)
    elif is_joke_request(message):
        response = generate_joke(user_id)
    else:
        # General conversation
        response = generate_chat_response(user_id, message)
        
    # Store assistant response
    conversation_memory.add_message(user_id, 'assistant', response)
    
    return response


if __name__ == "__main__":
    # Test the conversational handler
    logging.basicConfig(level=logging.INFO)
    
    test_messages = [
        "hi",
        "hey zeic can you tell me a joke",
        "how are you today?",
        "what can you do?"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        response = handle_conversation(msg)
        print(f"{BOT_NAME}: {response}")
