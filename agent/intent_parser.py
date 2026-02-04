"""
Intent Parser
Converts natural language to structured JSON with grammar correction
"""

import json
from agent.mistral_llm import query_mistral_json, query_mistral


def parse_intent(user_message: str) -> dict:
    """
    Parse user intent from natural language
    
    Args:
        user_message: Raw user input
    
    Returns:
        Structured intent JSON:
        {
            "intent": str,
            "entities": dict,
            "constraints": list,
            "original_text": str,
            "corrected_text": str (if applicable)
        }
    
    Raises:
        ValueError: If JSON parsing fails
    """
    
    system_prompt = """You are an intent parser for a privacy-preserving AI assistant.
Convert user messages into structured JSON with this EXACT format:
{
  "intent": "one of: draft_email, send_email, check_calendar, schedule_meeting, list_files, create_file, create_directory, delete_file, open_app, reminder, status, help, conversation",
  "entities": {
    "relevant_field": "value"
  },
  "constraints": ["approval_required", "conflict_check", etc]
}

Examples:
User: "draft a mail to John that the meeting is postponed"
{
  "intent": "draft_email",
  "entities": {"recipient_name": "John", "body": "the meeting is postponed"},
  "constraints": ["contact_lookup", "approval_required"]
}

User: "how are you today?"
{
  "intent": "conversation",
  "entities": {},
  "constraints": []
}

User: "can you read my Documents folder?"
{
  "intent": "list_files",
  "entities": {"directory": "Documents"},
  "constraints": []
}

  "intent": "delete_file",
  "entities": {"filename": "old-file.log"},
  "constraints": ["approval_required"]
}

User: "create folder tax in documents"
{
  "intent": "create_directory",
  "entities": {"name": "tax", "directory": "Documents"},
  "constraints": []
}

User: "what is the weather in Tokyo?"
{
  "intent": "web_search",
  "entities": {"query": "current weather in Tokyo"},
  "constraints": []
}

User: "latest news on AI"
{
  "intent": "web_search",
  "entities": {"query": "latest AI news"},
  "constraints": []
}

Return ONLY valid JSON, no explanation."""

    prompt = f"User message: \"{user_message}\"\n\nParse this into JSON:"
    
    try:
        intent_data = query_mistral_json(prompt, system_prompt)
        
        # Add original text
        intent_data["original_text"] = user_message
        
        # Validate required fields
        if "intent" not in intent_data:
            raise ValueError("Missing 'intent' field in parsed output")
        
        if "entities" not in intent_data:
            intent_data["entities"] = {}
        
        if "constraints" not in intent_data:
            intent_data["constraints"] = []
        
        return intent_data
    
    except Exception as e:
        raise ValueError(f"Failed to parse intent: {e}")


def correct_grammar(text: str) -> str:
    """
    Use LLM to correct grammar and improve text quality
    
    Args:
        text: Raw user text
    
    Returns:
        Corrected, professional text
    """
    system_prompt = """You are a grammar correction assistant.
Fix grammar, spelling, and punctuation while maintaining the original meaning.
Make the text professional and clear.
Return ONLY the corrected text, no explanation or quotes."""
    
    prompt = f"Correct this text: {text}"
    
    try:
        corrected = query_mistral(prompt, system_prompt)
        # Remove quotes if the model added them
        corrected = corrected.strip('"').strip("'")
        return corrected
    except Exception as e:
        print(f"Grammar correction failed: {e}")
        return text  # Return original if correction fails


def parse_with_correction(user_message: str) -> dict:
    """
    Parse intent and correct any text entities (like email body)
    
    Args:
        user_message: Raw user input
    
    Returns:
        Intent dict with corrected text in entities
    """
    intent = parse_intent(user_message)
    
    # Correct grammar for email body, calendar description, file content, etc.
    if intent["intent"] == "draft_email" and "body" in intent["entities"]:
        original_body = intent["entities"]["body"]
        corrected_body = correct_grammar(original_body)
        intent["entities"]["body"] = corrected_body
        intent["entities"]["original_body"] = original_body
        intent["corrected_text"] = corrected_body
    
    elif intent["intent"] in ["schedule_meeting", "reminder"] and "description" in intent["entities"]:
        original_desc = intent["entities"]["description"]
        corrected_desc = correct_grammar(original_desc)
        intent["entities"]["description"] = corrected_desc
        intent["entities"]["original_description"] = original_desc
        intent["corrected_text"] = corrected_desc
    
    elif intent["intent"] == "create_file" and "content" in intent["entities"]:
        # Optional: correct file content if it's prose
        pass
    
    return intent


if __name__ == "__main__":
    # Test intent parsing
    test_messages = [
        "hey can you draft a mail to John that the meeting has been postponed the timing will be let to know soon",
        "can you read my Documents folder?",
        "delete old-file.log",
        "schedule a meeting tomorrow at 3 PM"
    ]
    
    for msg in test_messages:
        print(f"\nInput: {msg}")
        try:
            result = parse_with_correction(msg)
            print(f"Intent: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
