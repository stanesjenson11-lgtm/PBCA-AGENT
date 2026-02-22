"""
Voice Gateway
Enables hands-free voice interaction with the PBCA Agent.
Designed for accessibility — especially for visually impaired users.

Flow:
  1. Listen for audio input (wake-word optional)
  2. Transcribe speech → text (Whisper)
  3. Route text through Agent.process_message() (same 8-step pipeline)
  4. Speak agent response aloud (pyttsx3)
  5. Handle verbal approval prompts (yes/no via voice)
"""

import asyncio
import logging
import threading
import time

from voice.stt_engine import (
    listen_from_microphone,
    detect_wake_word,
    strip_wake_word
)
from voice.tts_engine import speak

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_LISTEN_DURATION = 6       # seconds per recording
DEFAULT_WAKE_WORD = "hey pbca"
DEFAULT_STT_MODEL = "base"


class VoiceGateway:
    """
    Voice-based interface to the PBCA Agent.
    Runs as a continuous listening loop in a background thread.
    All messages go through the same Agent.process_message() pipeline.
    """

    def __init__(self, agent, user_id: str = "voice_user",
                 wake_word: str = DEFAULT_WAKE_WORD,
                 listen_duration: int = DEFAULT_LISTEN_DURATION,
                 stt_model: str = DEFAULT_STT_MODEL,
                 require_wake_word: bool = False):
        """
        Args:
            agent: An instance of agent.agent.Agent.
            user_id: User ID for logging/audit (default 'voice_user').
            wake_word: Wake phrase to activate (e.g., 'hey pbca').
            listen_duration: How many seconds to record each time.
            stt_model: Whisper model name ('tiny', 'base', 'small').
            require_wake_word: If True, only process after wake word.
        """
        self.agent = agent
        self.user_id = user_id
        self.wake_word = wake_word
        self.listen_duration = listen_duration
        self.stt_model = stt_model
        self.require_wake_word = require_wake_word

        self._running = False
        self._thread = None
        self._loop = None

    def start(self):
        """Start the voice gateway in a background thread."""
        if self._running:
            logger.warning("[VOICE] Gateway already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("[VOICE] Voice Gateway started.")
        speak("Voice gateway activated. I am listening.")

    def stop(self):
        """Stop the voice gateway."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("[VOICE] Voice Gateway stopped.")
        speak("Voice gateway deactivated. Goodbye.")

    def _run_loop(self):
        """Main listening loop (runs in background thread)."""
        # Create a new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        logger.info("[VOICE] Entering listening loop...")
        while self._running:
            try:
                self._listen_and_respond()
            except KeyboardInterrupt:
                logger.info("[VOICE] Interrupted by user.")
                break
            except Exception as e:
                logger.error(f"[VOICE] Error in listen loop: {e}")
                speak("I encountered an error. Please try again.")
                time.sleep(2)  # Brief pause before retrying

        self._loop.close()

    def _listen_and_respond(self):
        """Single listen → process → respond cycle."""
        # Step 1: Record and transcribe
        try:
            text = listen_from_microphone(
                duration=self.listen_duration,
                model_name=self.stt_model
            )
        except RuntimeError as e:
            logger.error(f"[VOICE] STT error: {e}")
            return

        if not text or len(text.strip()) < 2:
            # Silence or noise — skip
            return

        logger.info(f"[VOICE] Heard: '{text}'")

        # Step 2: Wake word check (if enabled)
        if self.require_wake_word:
            if not detect_wake_word(text, self.wake_word):
                # Not addressed to us — ignore
                return
            text = strip_wake_word(text, self.wake_word)
            if not text:
                speak("Yes? I'm listening.")
                return

        # Step 3: Process through agent pipeline (same as Telegram)
        logger.info(f"[VOICE] Processing: '{text}'")
        try:
            response = self._loop.run_until_complete(
                self.agent.process_message(self.user_id, text)
            )
        except Exception as e:
            logger.error(f"[VOICE] Agent error: {e}")
            response = f"Sorry, I encountered an error: {e}"

        # Step 4: Speak the response
        logger.info(f"[VOICE] Responding: '{response[:100]}...'")
        speak(response)

    def process_single(self, text: str) -> str:
        """
        Process a single text command through the voice pipeline.
        Useful for testing without a microphone.

        Args:
            text: Command text.

        Returns:
            Agent response string.
        """
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                self.agent.process_message(self.user_id, text)
            )
            speak(response)
            return response
        finally:
            loop.close()


def start_voice_mode(agent, require_wake_word: bool = False):
    """
    Convenience function to start voice mode.

    Args:
        agent: Agent instance.
        require_wake_word: Whether to require 'hey pbca' before each command.
    """
    gateway = VoiceGateway(
        agent=agent,
        require_wake_word=require_wake_word
    )

    print("=" * 50)
    print("🎙️  PBCA Voice Mode")
    print("=" * 50)
    print(f"Wake word: {'Required (' + gateway.wake_word + ')' if require_wake_word else 'Disabled (always listening)'}")
    print(f"STT Model: Whisper ({gateway.stt_model})")
    print(f"Listen duration: {gateway.listen_duration}s per cycle")
    print("Press Ctrl+C to stop.")
    print("=" * 50)

    gateway.start()

    try:
        # Keep main thread alive
        while gateway._running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[VOICE] Shutting down...")
        gateway.stop()

    return gateway


if __name__ == "__main__":
    # Standalone test
    import sys
    sys.path.insert(0, "..")
    from agent.agent import Agent

    agent = Agent()
    start_voice_mode(agent, require_wake_word=False)
