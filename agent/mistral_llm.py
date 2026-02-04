"""
Local Mistral-7B Interface via Ollama
No cloud calls - 100% local inference
"""

import subprocess
import json
from config.settings import OLLAMA_MODEL, OLLAMA_COMMAND


def query_mistral(prompt: str, system_prompt: str = None) -> str:
    """
    Query local Mistral-7B model via Ollama CLI
    
    Args:
        prompt: User prompt to send to the model
        system_prompt: Optional system instruction
    
    Returns:
        Raw text output from the model
    
    Raises:
        RuntimeError: If Ollama is not running or model not found
    """
    try:
        # Build the full prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Call Ollama via subprocess (no network calls)
        result = subprocess.run(
            [OLLAMA_COMMAND, "run", OLLAMA_MODEL, full_prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Ollama error: {result.stderr}")
        
        return result.stdout.strip()
    
    except FileNotFoundError:
        raise RuntimeError(
            "Ollama not found. Please install: https://ollama.com/download"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Ollama query timeout (30s)")


def query_mistral_json(prompt: str, system_prompt: str = None) -> dict:
    """
    Query Mistral and parse JSON response
    
    Args:
        prompt: User prompt requesting JSON output
        system_prompt: Optional system instruction
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        ValueError: If output is not valid JSON
    """
    response = query_mistral(prompt, system_prompt)
    
    # Try to extract JSON from code blocks if wrapped
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        response = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        response = response[start:end].strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from Mistral: {e}\nResponse: {response}")


if __name__ == "__main__":
    # Test the interface
    print("Testing Mistral interface...")
    result = query_mistral("Say 'Hello from Mistral!' and nothing else.")
    print(f"Response: {result}")
