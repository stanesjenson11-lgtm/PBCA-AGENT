"""
Timer / Countdown Tool
Start a countdown timer that notifies via Telegram when done.
Supports cancel and snooze via Telegram inline buttons.
"""

import logging
import threading
import time
import asyncio

logger = logging.getLogger(__name__)

# Active timers
_active_timers = {}
_timer_counter = 0

# Telegram bot reference (set by agent/main at startup)
_telegram_app = None
_telegram_chat_id = None


def set_telegram_notifier(app, chat_id):
    """Called by bot.py to register Telegram for timer notifications."""
    global _telegram_app, _telegram_chat_id
    _telegram_app = app
    _telegram_chat_id = chat_id
    logger.info(f"[TIMER] Telegram notifier registered for chat {chat_id}")


class TimerTool:
    """Start countdown timers with Telegram notifications."""

    def execute(self, entities: dict) -> dict:
        """
        Start a timer.

        Args:
            entities: {
                'duration': int (seconds) or str (e.g. '5 minutes'),
                'label': str (optional, e.g. 'tea timer'),
                'chat_id': int (optional, Telegram chat ID for notification)
            }
        """
        global _timer_counter

        duration_raw = entities.get("duration", entities.get("time", "60"))
        label = entities.get("label", entities.get("title", "Timer"))
        chat_id = entities.get("_chat_id", _telegram_chat_id)

        # Parse duration
        seconds = self._parse_duration(duration_raw)
        if seconds <= 0:
            return {"success": False, "error": f"Invalid duration: {duration_raw}"}
        if seconds > 86400:  # 24 hours max
            return {"success": False, "error": "Maximum timer duration is 24 hours."}

        _timer_counter += 1
        timer_id = _timer_counter

        # Start background timer
        thread = threading.Thread(
            target=self._timer_thread,
            args=(timer_id, seconds, label, chat_id),
            daemon=True
        )
        _active_timers[timer_id] = {
            "label": label,
            "duration": seconds,
            "thread": thread,
            "start_time": time.time(),
            "snoozed": False
        }
        thread.start()

        # Format friendly duration
        friendly = self._format_duration(seconds)

        return {
            "success": True,
            "timer_id": timer_id,
            "message": f"⏱️ Timer '{label}' started for {friendly}."
        }

    def _timer_thread(self, timer_id: int, seconds: int, label: str, chat_id=None):
        """Background timer thread — sends Telegram notification when done."""
        time.sleep(seconds)

        # Check if timer was cancelled during sleep
        if timer_id not in _active_timers:
            return

        msg = f"⏰ Timer '{label}' is done!"
        logger.info(f"[TIMER] {msg}")
        print(f"\n{msg}")

        # Try TTS notification
        try:
            from voice.tts_engine import speak
            speak(f"Timer {label} is done!")
        except Exception:
            pass

        # Send Telegram notification with snooze/dismiss buttons
        self._send_telegram_alert(timer_id, label, chat_id)

        # Cleanup
        _active_timers.pop(timer_id, None)

    def _send_telegram_alert(self, timer_id: int, label: str, chat_id=None):
        """Send timer alert to Telegram with snooze/cancel buttons."""
        global _telegram_app, _telegram_chat_id

        target_chat = chat_id or _telegram_chat_id
        if not _telegram_app or not target_chat:
            logger.warning("[TIMER] No Telegram notifier registered. Timer alert only shown in console.")
            return

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ Snooze 5 min", callback_data=f"timer_snooze_{timer_id}_5"),
                    InlineKeyboardButton("⏰ Snooze 10 min", callback_data=f"timer_snooze_{timer_id}_10"),
                ],
                [
                    InlineKeyboardButton("✅ Dismiss", callback_data=f"timer_dismiss_{timer_id}"),
                ]
            ])

            message = f"⏰ **Timer Alert!**\n\n'{label}' is done!\n\nSnooze or dismiss?"

            # Run the async send in its own event loop (we're in a thread)
            async def _send():
                await _telegram_app.bot.send_message(
                    chat_id=target_chat,
                    text=message,
                    reply_markup=keyboard
                )

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_send())
            loop.close()

            logger.info(f"[TIMER] Telegram alert sent for timer {timer_id}")

        except Exception as e:
            logger.error(f"[TIMER] Failed to send Telegram alert: {e}")
            # Fallback: try without buttons
            try:
                async def _send_plain():
                    await _telegram_app.bot.send_message(
                        chat_id=target_chat,
                        text=f"⏰ Timer '{label}' is done!"
                    )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_send_plain())
                loop.close()
            except Exception as e2:
                logger.error(f"[TIMER] Fallback Telegram send also failed: {e2}")

    def _parse_duration(self, raw) -> int:
        """Parse duration from various formats."""
        if isinstance(raw, (int, float)):
            return int(raw)

        raw = str(raw).lower().strip()

        # Try direct int
        try:
            return int(raw)
        except ValueError:
            pass

        # Parse "5 minutes", "1 hour", "30 seconds"
        import re
        match = re.match(r"(\d+)\s*(second|sec|s|minute|min|m|hour|hr|h)", raw)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if unit.startswith("h"):
                return value * 3600
            elif unit.startswith("m"):
                return value * 60
            else:
                return value

        return 0

    def _format_duration(self, seconds: int) -> str:
        """Format seconds into friendly string."""
        if seconds >= 3600:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            return f"{h}h {m}m" if m else f"{h} hour{'s' if h > 1 else ''}"
        elif seconds >= 60:
            m = seconds // 60
            s = seconds % 60
            return f"{m}m {s}s" if s else f"{m} minute{'s' if m > 1 else ''}"
        else:
            return f"{seconds} second{'s' if seconds > 1 else ''}"

    def get_capabilities(self) -> list:
        return ["start_timer"]


# Module-level functions
_tool = TimerTool()


def start_timer(entities: dict = None) -> dict:
    return _tool.execute(entities or {"duration": 60})


def cancel_timer(timer_id: int) -> dict:
    """Cancel an active timer."""
    if timer_id in _active_timers:
        info = _active_timers.pop(timer_id)
        return {"success": True, "message": f"✅ Timer '{info['label']}' cancelled."}
    return {"success": False, "error": f"No active timer with ID {timer_id}"}


def snooze_timer(timer_id: int, minutes: int = 5) -> dict:
    """Snooze: start a new timer with the same label."""
    # Get the label from old timer if it exists
    label = "Snoozed Timer"
    if timer_id in _active_timers:
        label = _active_timers[timer_id]["label"]
        _active_timers.pop(timer_id)

    return _tool.execute({
        "duration": minutes * 60,
        "label": f"{label} (snoozed)"
    })
