"""
Telegram Bot Gateway
Secure polling-based message handler with user verification
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID


class TelegramGateway:
    """Telegram bot gateway with security"""
    
    def __init__(self, message_handler_callback):
        """
        Initialize Telegram gateway
        
        Args:
            message_handler_callback: Function to handle messages
                                    Signature: callback(user_id, message) -> response
        """
        self.message_handler = message_handler_callback
        self.application = None
        self.authorized_user_id = int(AUTHORIZED_USER_ID)
    
    def verify_user(self, user_id: int) -> bool:
        """Verify user is authorized"""
        return user_id == self.authorized_user_id
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        # Remove control characters
        sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\t')
        return sanitized.strip()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Verify user
        if not self.verify_user(user_id):
            await update.message.reply_text(
                "⛔ Unauthorized. This bot is private."
            )
            logging.warning(f"Unauthorized access attempt from user {user_id}")
            return
        
        # Sanitize input
        sanitized_message = self.sanitize_input(message_text)
        
        logging.info(f"Message from {user_id}: {sanitized_message}")
        
        try:
            # Call agent handler
            response = await self.message_handler(user_id, sanitized_message)
            await update.message.reply_text(response)
        
        except Exception as e:
            logging.error(f"Error handling message: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}\nPlease try again or contact support."
            )
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if not self.verify_user(user_id):
            await update.message.reply_text("⛔ Unauthorized")
            return
        
        await update.message.reply_text(
            "✅ PBCA Agent Status:\n"
            "• Bot: Online\n"
            "• LLM: Connected (Mistral via Ollama)\n"
            "• Privacy: Enforced\n"
            "• Scheduler: Running"
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        
        if not self.verify_user(user_id):
            await update.message.reply_text("⛔ Unauthorized")
            return
        
        help_text = """🤖 PBCA Agent Help

**Natural Language Commands:**
• "Draft a mail to John that [message]"
• "Check my calendar today"
• "List files in my Documents folder"
• "Create a file called notes.txt"
• "Schedule a meeting tomorrow at 3 PM"
• "Remind me every Monday at 9 AM"

**Commands:**
• /status - Check agent status
• /help - Show this help message

All sensitive actions require your approval before execution."""
        
        await update.message.reply_text(help_text)
    
    def setup(self):
        """Setup bot handlers"""
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("help", self.handle_help))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        logging.info("Telegram bot handlers configured")
    
    def start(self):
        """Start polling (non-blocking)"""
        if not self.application:
            self.setup()
        
        logging.info("Starting Telegram bot polling...")
        # Increase timeouts to prevent ReadTimeout errors
        self.application.run_polling(
            drop_pending_updates=True,
            timeout=30,          # Long polling timeout
            read_timeout=60,     # HTTP read timeout (must be > timeout)
            connect_timeout=60,  # Connection timeout
            write_timeout=60     # Write timeout
        )
    
    async def send_message(self, user_id: int, text: str):
        """Send message to user"""
        try:
            await self.application.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logging.error(f"Failed to send message: {e}")


if __name__ == "__main__":
    # Test bot
    logging.basicConfig(level=logging.INFO)
    
    async def test_handler(user_id, message):
        return f"Echo: {message}"
    
    gateway = TelegramGateway(test_handler)
    print("Starting test bot...")
    gateway.start()
