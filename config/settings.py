"""
PBCA Agent Configuration
Central settings for the privacy-preserving AI assistant
"""

import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8100385271:AAHKX3l90lAPEvJ2G6ib5Sn_-8uHwGlz6UI")
AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_USER_ID", "1561381989")  # Set your Telegram user ID

# Email Configuration (Gmail)
# ⚠️ REPLACE THESE WITH YOUR DETAILS
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "zeic676767@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "jkcf funv fovs qpnt")  # Generate App Password: https://myaccount.google.com/apppasswords
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Ollama Configuration
OLLAMA_MODEL = "mistral"
OLLAMA_COMMAND = "ollama"

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "memory", "audit_log.db")

# Contact Database
CONTACTS_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "contacts.json")

# Privacy Policy
PRIVACY_POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "privacy", "policies.json")

# Approval Settings
REQUIRE_APPROVAL_FOR_SEND = True
REQUIRE_APPROVAL_FOR_DELETE = True
REQUIRE_APPROVAL_FOR_CREATE = True

# Logging
LOG_LEVEL = "INFO"

# Bot Personality
BOT_NAME = "Zeic"
USER_NAME = "Sir Jenson"

# Whitelisted Applications (for desktop_tool)
WHITELISTED_APPS = [
    "notepad",
    "notepad.exe",
    "calc",
    "calc.exe",
    "explorer",
    "explorer.exe"
]

# Safe Directory Prefixes (prevent system file access)
SAFE_DIRECTORIES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]
