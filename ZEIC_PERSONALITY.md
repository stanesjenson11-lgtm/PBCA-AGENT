# Zeic - Conversational AI Assistant

## 🎭 Personality

**Name:** Zeic  
**User:** Sir Jenson  
**Style:** Helpful, professional, warm

## ✅ Features Added

### Conversational Intelligence
- **Greetings**: Responds warmly when you say "hi", "hello", or "hey"
- **Jokes**: Tell jokes on request using local Mistral AI
- **General Chat**: Natural conversation via Ollama/Mistral
- **Smart Fallback**: If a task command isn't recognized, Zeic tries to help conversationally

### How It Works
1. Message received from Telegram
2. Zeic checks if it's a greeting or joke request
3. If yes → Uses Ollama/Mistral for response
4. If no → Routes to task system (emails, files, calendar)
5. If task fails → Falls back to conversation

## 🧪 Try These

**Greetings:**
```
hi
hello
hey zeic
```

**Jokes:**
```
hey zeic can you tell me a joke
tell me something funny
make me laugh
```

**General Chat:**
```
how are you?
what can you do?
tell me about yourself
```

**Tasks** (still work as before):
```
list files in Documents
check my calendar today
draft an email to John
```

## 🔧 Technical Details

- **Model**: Uses local Mistral via Ollama
- **No Cloud**: All processing happens locally
- **Privacy**: Conversational responses also go through privacy checks
- **Fallback**: If Ollama is unavailable, uses pre-programmed responses

## 📝 Files Modified

- `agent/conversation.py` - New conversational handler
- `agent/agent.py` - Added routing logic
- `config/settings.py` - Added personality config

---

**Zeic is ready to chat!** 🤖
