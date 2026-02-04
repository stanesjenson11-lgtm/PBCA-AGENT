"""
Simple test to verify imports work
"""

print("Testing imports...")

try:
    print("1. Testing telegram import...")
    from telegram import Update
    from telegram.ext import Application
    print("   ✅ telegram package OK")
except Exception as e:
    print(f"   ❌ telegram package error: {e}")

try:
    print("2. Testing local modules...")
    from agent.agent import Agent
    from telegram_gateway.bot import TelegramGateway
    print("   ✅ local modules OK")
except Exception as e:
    print(f"   ❌ local modules error: {e}")

try:
    print("3. Testing Ollama...")
    import subprocess
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
    if "mistral" in result.stdout:
        print("   ✅ Ollama and Mistral OK")
    else:
        print(f"   ⚠️  Ollama OK but Mistral not found. Run: ollama pull mistral")
except FileNotFoundError:
    print("   ❌ Ollama not installed. Install from: https://ollama.com/download")
except Exception as e:
    print(f"   ⚠️  Ollama check error: {e}")

print("\nAll basic checks complete!")
