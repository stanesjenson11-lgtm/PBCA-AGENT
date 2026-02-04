# PBCA Agent - Quick Start Guide

## 🚀 Installation (5 Minutes)

### Step 1: Install Ollama
```bash
# Windows
winget install Ollama.Ollama

# Pull Mistral model
ollama pull mistral
```

### Step 2: Setup Project
```bash
cd pbca-agent

# Run automated setup
setup.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Telegram
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot: `/newbot`
3. Copy your bot token
4. Get your user ID from [@userinfobot](https://t.me/userinfobot)
5. Edit `config/settings.py`:
```python
TELEGRAM_BOT_TOKEN = "1234567890:ABC..."
AUTHORIZED_USER_ID = "987654321"
```

### Step 4: Run
```bash
venv\Scripts\activate
python main.py
```

---

## 💬 Common Commands

### Email
```
"draft a mail to John that [message]"
"send the email"
```

### Files
```
"list files in Documents"
"create a file called notes.txt"
"delete old-file.log"
```

### Calendar
```
"check my calendar today"
"schedule a meeting tomorrow at 3 PM"
```

### Reminders
```
"remind me every Monday at 9 AM to [task]"
```

---

## ⚙️ Configuration

### Add Contacts
Edit `tools/contacts.json`:
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "aliases": ["Alice Smith"]
}
```

### Whitelist Apps
Edit `config/settings.py`:
```python
WHITELISTED_APPS = [
    "notepad.exe",
    "calc.exe"
]
```

### Safe Directories
```python
SAFE_DIRECTORIES = [
    "C:\\Users\\YourName\\Documents",
    "C:\\Users\\YourName\\Downloads"
]
```

---

## 🔒 Security Features

- ✅ No exposed ports
- ✅ Privacy scanning (blocks passwords, API keys, SSNs)
- ✅ Approval required for sensitive actions
- ✅ Complete audit trail in SQLite
- ✅ Local-only LLM (no cloud)

---

## ⚠️ Troubleshooting

**Ollama not found:**
```
Install from: https://ollama.com/download
```

**Bot token not set:**
```
Edit config/settings.py
Set TELEGRAM_BOT_TOKEN
```

**Can't access directory:**
```
Add to SAFE_DIRECTORIES in config/settings.py
```

---

## 📚 Documentation

- Full README: [README.md](file:///c:/Users/stane/Downloads/antigravity%20ai%20proj/pbca-agent/README.md)
- Implementation Details: See walkthrough.md
- Security Model: See implementation_plan.md

---

**Ready to use!** Send a message to your Telegram bot to start. 🤖
