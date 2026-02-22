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
  "intent": "one of: draft_email, send_email, check_calendar, schedule_meeting, list_files, create_file, create_directory, delete_file, open_app, reminder, status, help, conversation, web_search, check_system, start_timer, get_clipboard, set_clipboard, take_screenshot, list_processes, kill_process, set_volume, mute_volume, get_volume, compress_files, extract_files, read_pdf, read_url, organize_directory, triage_inbox, record_meeting, stop_recording, summarize_meeting, review_code, perform_rpa_task, search_files",
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

User: "check CPU usage" or "system stats" or "how much RAM am I using"
{
  "intent": "check_system",
  "entities": {"metric": "all"},
  "constraints": []
}

User: "set a timer for 5 minutes"
{
  "intent": "start_timer",
  "entities": {"duration": "5 minutes", "label": "Timer"},
  "constraints": []
}

User: "take a screenshot"
{
  "intent": "take_screenshot",
  "entities": {},
  "constraints": ["approval_required"]
}

User: "what's on my clipboard" or "paste clipboard"
{
  "intent": "get_clipboard",
  "entities": {},
  "constraints": []
}

User: "list running processes" or "show processes"
{
  "intent": "list_processes",
  "entities": {},
  "constraints": []
}

User: "kill notepad" or "close chrome"
{
  "intent": "kill_process",
  "entities": {"name": "notepad"},
  "constraints": ["approval_required"]
}

User: "set volume to 50" or "volume 80%"
{
  "intent": "set_volume",
  "entities": {"level": 50},
  "constraints": []
}

User: "mute" or "mute sound"
{
  "intent": "mute_volume",
  "entities": {},
  "constraints": []
}

User: "compress my Documents folder" or "zip downloads"
{
  "intent": "compress_files",
  "entities": {"path": "Documents"},
  "constraints": []
}

User: "read resume.pdf" or "open my pdf"
{
  "intent": "read_pdf",
  "entities": {"path": "resume.pdf"},
  "constraints": []
}

User: "read this url https://example.com"
{
  "intent": "read_url",
  "entities": {"url": "https://example.com"},
  "constraints": []
}

User: "organize my Downloads folder"
{
  "intent": "organize_directory",
  "entities": {"directory": "Downloads"},
  "constraints": ["approval_required"]
}

User: "triage my inbox" or "check emails"
{
  "intent": "triage_inbox",
  "entities": {},
  "constraints": []
}

User: "start recording meeting" or "record meeting"
{
  "intent": "record_meeting",
  "entities": {},
  "constraints": []
}

User: "stop recording" or "summarize meeting"
{
  "intent": "stop_recording",
  "entities": {},
  "constraints": []
}

User: "review my auth.py" or "review code in main.py"
{
  "intent": "review_code",
  "entities": {"path": "auth.py"},
  "constraints": []
}

User: "click on the submit button" or "fill the form"
{
  "intent": "perform_rpa_task",
  "entities": {"action": "click", "description": "click submit button"},
  "constraints": ["approval_required"]
}

User: "find resume.pdf" or "where is my resume" or "locate config.json" or "search for budget spreadsheet"
{
  "intent": "search_files",
  "entities": {"query": "resume.pdf"},
  "constraints": []
}

User: "find the folder called Projects" or "where did I save the Python file called scraper"
{
  "intent": "search_files",
  "entities": {"query": "Projects", "type": "folder"},
  "constraints": []
}

User: "find all files named invoice"
{
  "intent": "search_files",
  "entities": {"query": "invoice"},
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
