# PBCA Agent

**Privacy-Preserving AI Assistant with Local LLM, Telegram Control, and Secure Automation**

A local, persistent AI assistant that combines Mistral-7B inference, Telegram messaging, secure system automation, task scheduling, and strict privacy enforcement—without exposing ports or allowing unsafe execution.

## 🔒 Security Model

### Mandatory Constraints

- ✅ **No public inbound ports** - Only outbound Telegram polling
- ✅ **No arbitrary shell execution** - All commands are whitelisted
- ✅ **No direct LLM system access** - All actions pass through permission layer
- ✅ **Fail closed** - Block execution if any validation fails
- ✅ **Local-only sensitive data** - No cloud storage or transmission
- ✅ **Complete audit trail** - All actions logged to SQLite

### 8-Step Security Pipeline

Every user request flows through:

1. **Receive** - Message from Telegram
2. **Parse** - Natural language → Structured JSON (with grammar correction)
3. **Plan** - Generate action sequence using causal graph
4. **Enforce** - Privacy scan (regex + keyword blocking)
5. **Approve** - Human-in-the-loop for sensitive actions
6. **Execute** - Whitelisted tool execution
7. **Log** - Audit trail to SQLite
8. **Respond** - Send result back to user

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** with Mistral-7B model

### 1. Install Ollama & Mistral

```bash
# Windows (PowerShell as Administrator)
winget install Ollama.Ollama

# Or download from: https://ollama.com/download

# Pull Mistral model
ollama pull mistral
```

### 2. Clone & Setup

```bash
cd pbca-agent

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Telegram Bot

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Get your bot token
3. Get your user ID from [@userinfobot](https://t.me/userinfobot)
4. Edit `config/settings.py`:

```python
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
AUTHORIZED_USER_ID = "987654321"  # Your Telegram user ID
```

### 4. Run the Agent

```bash
python main.py
```

The agent will:
- Initialize the audit database
- Start the scheduler
- Connect to Telegram
- Begin polling for messages

## 💬 Usage Examples

### Email Automation

**Casual request with grammar correction:**

```
You: hey can you draft a mail to John that the meeting has been postponed the timing will be let to know soon

Agent: 📧 Draft Email Preview:
To: john.doe@company.com
Subject: Meeting Update
Body: The meeting has been postponed. The new timing will be communicated soon.

Reply 'send' to send, 'edit subject: New Subject' to change, or 'cancel'

You: send

Agent: ✅ Email sent to john.doe@company.com
```

### File Operations

**List files:**
```
You: can you read my Documents folder?

Agent: 📁 C:\Users\YourName\Documents (15 items):
  📄 report.pdf (2048 bytes)
  📁 Projects
  📄 notes.txt (512 bytes)
  ...
```

**Create file:**
```
You: create a file called todo.txt with my tasks

Agent: What should I write in todo.txt?

You: buy groceries, call dentist, finish report

Agent: Creating todo.txt with your todo list. Confirm? (yes/no)

You: yes

Agent: ✅ Created todo.txt in C:\Users\YourName\Documents
```

**Delete file (requires confirmation):**
```
You: delete old-file.log

Agent: ⚠️ Delete old-file.log? This cannot be undone. Reply 'yes' to confirm

You: yes

Agent: ✅ Deleted old-file.log. Logged to audit trail.
```

### Calendar Operations

**Check calendar:**
```
You: check my calendar today

Agent: 📅 Events on 2026-02-03:
  • Team Meeting (02:00 PM - 03:00 PM)
  • Client Call (04:30 PM - 05:00 PM)
```

**Schedule meeting:**
```
You: schedule a meeting tomorrow at 3 PM

Agent: ✅ Created event: Meeting
```

### Multi-Step Automation

**Complex workflow:**
```
You: Find a free slot tomorrow and draft an email to Sarah requesting a meeting

Agent: [Checks calendar]
       [Finds free slot: 2:00 PM - 3:00 PM]
       [Searches contact "Sarah"]
       [Drafts email]
       
📧 Draft Email Preview:
To: sarah.jones@company.com
Subject: Meeting Request
Body: Hi Sarah, I'd like to schedule a meeting with you. Would you be available tomorrow at 2:00 PM?

Reply 'send' to send or 'cancel'
```

### Scheduled Reminders

```
You: Remind me every Monday at 9 AM to check reports

Agent: ⏰ Scheduled task created: Daily reminder
Task will run every Monday at 09:00
Approval required before first execution. Reply 'approve' to confirm.

You: approve

Agent: ✅ Task approved and scheduled
```

## 🔌 Commands

### Natural Language

The agent understands casual conversation:

- "Draft an email to [person] that [message]"
- "Check my calendar [today/tomorrow/date]"
- "List files in [directory]"
- "Create a file called [name]"
- "Delete [filename]"
- "Schedule a meeting [when]"
- "Remind me [schedule]"

### Bot Commands

- `/status` - Check agent health and components
- `/help` - Show command reference

## 📁 Project Structure

```
pbca-agent/
├── agent/
│   ├── agent.py              # Main orchestration pipeline
│   ├── intent_parser.py      # NLP → JSON with grammar correction
│   └── mistral_llm.py        # Local Ollama interface
├── planner/
│   ├── causal_graph.py       # Action dependencies
│   └── planner.py            # Execution ordering
├── privacy/
│   ├── policies.json         # Privacy rules (regex patterns)
│   ├── detector.py           # Violation scanning
│   └── enforcer.py           # Blocking logic
├── tools/
│   ├── email_tool.py         # Email with contact lookup
│   ├── calendar_tool.py      # Calendar operations
│   ├── desktop_tool.py       # File & app operations
│   └── contacts.json         # Contact database
├── scheduler/
│   └── scheduler.py          # Cron-like task scheduler
├── telegram/
│   └── bot.py                # Telegram polling gateway
├── memory/
│   ├── audit_logger.py       # Audit trail
│   └── audit_log.db          # SQLite database
├── config/
│   └── settings.py           # Configuration
├── main.py                   # Entry point
├── requirements.txt
└── README.md
```

## 🛡️ Privacy & Security

### Privacy Enforcement

The agent automatically blocks:

- **Passwords** - `password: abc123`
- **API Keys** - `api_key: sk-abc123...`
- **OTPs** - `verification code 123456`
- **Credit Cards** - `4111 1111 1111 1111`
- **SSNs** - `123-45-6789`
- **Blocked Topics** - "salary", "bank account", etc.

Example:

```
You: My password is secret123

Agent: 🔒 Privacy violation detected:
- Password detection (matched: 'password is secret123')

[Action blocked and logged]
```

### Whitelisted Tools

Only these actions are allowed:

- **Email**: `search_contact`, `draft_email`, `send_email` (with approval)
- **Calendar**: `check_calendar`, `create_event` (with conflict check)
- **Files**: `list_files`, `create_file`, `delete_file` (with approval)
- **Apps**: `open_app` (whitelisted apps only)

### Audit Trail

All actions logged to `memory/audit_log.db`:

- Timestamp
- Source (telegram/scheduler)
- User ID
- Intent
- Action taken
- Result
- Blocked reason (if applicable)

View recent logs:

```python
from memory.audit_logger import get_recent_logs
logs = get_recent_logs(10)
```

## 🔧 Configuration

Edit `config/settings.py` to customize:

**Telegram:**
```python
TELEGRAM_BOT_TOKEN = "your_token"
AUTHORIZED_USER_ID = "your_user_id"
```

**Approval Requirements:**
```python
REQUIRE_APPROVAL_FOR_SEND = True
REQUIRE_APPROVAL_FOR_DELETE = True
REQUIRE_APPROVAL_FOR_CREATE = True
```

**Whitelisted Apps:**
```python
WHITELISTED_APPS = [
    "notepad", "notepad.exe",
    "calc", "calc.exe",
    "explorer", "explorer.exe"
]
```

**Safe Directories:**
```python
SAFE_DIRECTORIES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]
```

## 📝 Adding Contacts

Edit `tools/contacts.json`:

```json
[
  {
    "name": "John",
    "email": "john.doe@company.com",
    "aliases": ["John Doe", "J. Doe"]
  },
  {
    "name": "Sarah",
    "email": "sarah.jones@company.com",
    "aliases": ["Sarah Jones"]
  }
]
```

## 🧪 Testing

Test individual components:

```bash
# Test Ollama
python agent/mistral_llm.py

# Test privacy detector
python privacy/detector.py

# Test intent parsing
python agent/intent_parser.py

# Test tools
python tools/email_tool.py
python tools/desktop_tool.py
python tools/calendar_tool.py
```

## ⚠️ Troubleshooting

### Ollama Not Found

```
Error: Ollama not found
```

**Solution:** Install Ollama from https://ollama.com/download and ensure `ollama` is in PATH.

### Bot Token Not Set

```
ERROR: Please set TELEGRAM_BOT_TOKEN
```

**Solution:** Edit `config/settings.py` and set your bot token from @BotFather.

### Privacy Violations Blocking Everything

**Solution:** Adjust patterns in `privacy/policies.json` to be less restrictive.

### Can't Access Certain Directories

```
Access denied: [path] is not in safe directories
```

**Solution:** Add the directory to `SAFE_DIRECTORIES` in `config/settings.py`.

## 📚 Architecture Details

### Natural Language Flow

1. User sends casual message via Telegram
2. Intent parser extracts action + entities
3. LLM corrects grammar for email bodies/descriptions
4. Privacy enforcer scans original and corrected text
5. Planner creates ordered action sequence
6. Agent executes with approval gates
7. Results formatted and sent back

### Grammar Correction

Input:
```
"the meeting has been postponed the timing will be let to know soon"
```

Corrected:
```
"The meeting has been postponed. The new timing will be communicated soon."
```

Used for: Email bodies, calendar descriptions, file content

### Fail-Safe Behavior

If ANY of these fail:
- Intent parsing invalid JSON
- Privacy violation detected
- Action not whitelisted
- User not authorized
- Database write fails

Then:
1. Abort immediately
2. Log failure with context
3. Notify user with clear error
4. Do NOT retry automatically

## 🎯 Design Principles

1. **Privacy First** - Block sensitive data before execution
2. **Fail Closed** - Default to blocking, not allowing
3. **Human in the Loop** - Approval for destructive actions
4. **Complete Audit** - Log everything for accountability
5. **No Surprises** - Clear previews before execution
6. **Local Only** - No cloud dependencies for LLM or data

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Areas to enhance:

- More sophisticated NLP parsing
- Additional tool integrations
- Advanced scheduling patterns
- Email backend integration (SMTP)
- Calendar backend (Google Calendar API)
- Web dashboard for audit logs

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **Mistral AI** - Open-source LLM
- **python-telegram-bot** - Telegram integration

---

**Built with security and privacy as core principles** 🔒
