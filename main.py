"""
PBCA Agent - Privacy-Preserving AI Assistant
Main Entry Point
"""

import sys
import logging
import asyncio
import argparse
from agent.agent import Agent
from telegram_gateway.bot import TelegramGateway
from scheduler.scheduler import Scheduler
from memory.audit_logger import init_database
from config.settings import TELEGRAM_BOT_TOKEN


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class PBCAAgent:
    """Main application coordinator"""
    
    def __init__(self):
        self.agent = Agent()
        self.scheduler = None
        self.telegram_gateway = None
        self.voice_gateway = None
    
    async def telegram_message_handler(self, user_id: int, message: str) -> str:
        """Handle messages from Telegram"""
        return await self.agent.process_message(str(user_id), message)
    
    def scheduler_task_callback(self, action: str, parameters: dict) -> dict:
        """Handle scheduled tasks"""
        logger.info(f"[SCHEDULER] Executing scheduled task: {action}")
        # Create a simple step and execute
        from planner.planner import ActionStep
        step = ActionStep(action, parameters)
        return self.agent.execute_action(step)
    
    def start(self):
        """Start all components"""
        logger.info("=" * 50)
        logger.info("PBCA Agent Starting...")
        logger.info("=" * 50)
        
        # Initialize database
        logger.info("[SETUP] Initializing audit database...")
        init_database()
        
        # Start scheduler
        logger.info("[SETUP] Starting scheduler...")
        self.scheduler = Scheduler(self.scheduler_task_callback)
        self.scheduler.start()
        
        # Setup Telegram bot
        logger.info("[SETUP] Setting up Telegram bot...")
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.error("=" * 50)
            logger.error("ERROR: Please set TELEGRAM_BOT_TOKEN in config/settings.py")
            logger.error("Get your token from: https://t.me/BotFather")
            logger.error("=" * 50)
            sys.exit(1)
        
        self.telegram_gateway = TelegramGateway(self.telegram_message_handler)
        self.telegram_gateway.setup()
        
        logger.info("=" * 50)
        logger.info("✅ PBCA Agent is running!")
        logger.info("=" * 50)
        logger.info("Components:")
        logger.info("  • Privacy Enforcer: Active")
        logger.info("  • Causal Planner: Active")
        logger.info("  • Tool Executor: Active")
        logger.info("  • Scheduler: Running")
        logger.info("  • Telegram Bot: Polling")
        logger.info("=" * 50)
        logger.info("Security Guarantees:")
        logger.info("  • No open inbound ports")
        logger.info("  • No arbitrary shell execution")
        logger.info("  • Privacy violations blocked")
        logger.info("  • All actions logged")
        logger.info("=" * 50)
        logger.info("Send a message to your Telegram bot to get started!")
        logger.info("=" * 50)
        
        # Start Telegram bot (blocking) - ensure event loop exists
        try:
            import asyncio
            try:
                # Try to get the event loop, create if doesn't exist (Python 3.14 issue)
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            self.telegram_gateway.start()
        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN] Received shutdown signal")
            self.stop()
    
    def start_voice_mode(self, require_wake_word: bool = False):
        """Start the agent in voice mode for hands-free operation."""
        logger.info("=" * 50)
        logger.info("PBCA Agent Starting in VOICE MODE...")
        logger.info("=" * 50)
        
        # Initialize database
        init_database()
        
        # Start scheduler
        self.scheduler = Scheduler(self.scheduler_task_callback)
        self.scheduler.start()
        
        try:
            from voice.voice_gateway import start_voice_mode as _start_voice
            logger.info("[SETUP] Starting Voice Gateway...")
            logger.info("Components:")
            logger.info("  • Privacy Enforcer: Active")
            logger.info("  • Causal Planner: Active")
            logger.info("  • Voice Gateway: Listening")
            logger.info("  • Wake Word: " + ("Enabled" if require_wake_word else "Disabled"))
            logger.info("=" * 50)
            _start_voice(self.agent, require_wake_word=require_wake_word)
        except ImportError as e:
            logger.error(f"Voice module dependencies missing: {e}")
            logger.error("Install with: pip install openai-whisper sounddevice pyttsx3 scipy")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN] Received shutdown signal")
            self.stop()
    
    def stop(self):
        """Stop all components"""
        logger.info("[SHUTDOWN] Stopping components...")
        
        if self.scheduler:
            self.scheduler.stop()
        
        logger.info("[SHUTDOWN] Goodbye!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PBCA Agent — Privacy-Preserving AI Assistant")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode (hands-free)")
    parser.add_argument("--wake-word", action="store_true", help="Require wake word 'hey pbca' in voice mode")
    args = parser.parse_args()
    
    app = PBCAAgent()
    
    try:
        if args.voice:
            app.start_voice_mode(require_wake_word=args.wake_word)
        else:
            app.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
