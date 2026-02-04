"""
Simplified main.py for debugging
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.info("Step 1: Importing agent...")
from agent.agent import Agent

logger.info("Step 2: Importing telegram_gateway...")
from telegram_gateway.bot import TelegramGateway

logger.info("Step 3: Importing scheduler...")
from scheduler.scheduler import Scheduler

logger.info("Step 4: Importing audit logger...")
from memory.audit_logger import init_database

logger.info("Step 5: Importing settings...")
from config.settings import TELEGRAM_BOT_TOKEN

logger.info("Step 6: Initializing database...")
init_database()

logger.info("Step 7: Creating agent...")
agent = Agent()

logger.info("Step 8: Creating message handler...")
async def telegram_message_handler(user_id: int, message: str) -> str:
    return await agent.process_message(str(user_id), message)

logger.info("Step 9: Creating Telegram gateway...")
telegram_gateway = TelegramGateway(telegram_message_handler)

logger.info("Step 10: Setting up Telegram bot...")
telegram_gateway.setup()

logger.info("Step 11: Starting bot polling...")
telegram_gateway.start()
