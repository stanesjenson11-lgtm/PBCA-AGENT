"""
Minimal Telegram Bot Test
"""
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = "8100385271:AAHKX3l90lAPEvJ2G6ib5Sn_-8uHwGlz6UI"



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    await update.message.reply_text(f"You said: {update.message.text}")

def main():
    """Run the bot."""
    print("Starting minimal bot test...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Run
    print("Bot is running. Send it a message!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
