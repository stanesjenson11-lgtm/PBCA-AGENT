"""
Text-to-Speech Engine
Uses pyttsx3 for fully offline speech synthesis.
No cloud calls — runs entirely on local CPU.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# Lazy-loaded engine
_tts_engine = None
_tts_lock = threading.Lock()


def _get_engine():
    """
    Get or create the pyttsx3 engine.
    Thread-safe with a lock since pyttsx3 is not thread-safe.
    """
    global _tts_engine
    if _tts_engine is None:
        try:
            import pyttsx3
            _tts_engine = pyttsx3.init()

            # Configure voice properties
            _tts_engine.setProperty("rate", 170)     # Speed (words per minute)
            _tts_engine.setProperty("volume", 0.9)   # Volume (0.0 to 1.0)

            # Try to use a natural-sounding voice
            voices = _tts_engine.getProperty("voices")
            if voices:
                # Prefer a female voice for clarity (usually index 1 on Windows)
                for i, voice in enumerate(voices):
                    if "zira" in voice.name.lower() or "female" in voice.name.lower():
                        _tts_engine.setProperty("voice", voice.id)
                        logger.info(f"[TTS] Using voice: {voice.name}")
                        break
                else:
                    # Default to first available
                    _tts_engine.setProperty("voice", voices[0].id)
                    logger.info(f"[TTS] Using default voice: {voices[0].name}")

            logger.info("[TTS] pyttsx3 engine initialized.")
        except ImportError:
            raise RuntimeError(
                "pyttsx3 is not installed. Install with: pip install pyttsx3"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to init TTS engine: {e}")
    return _tts_engine


def speak(text: str):
    """
    Speak text aloud using pyttsx3 (blocking).

    Args:
        text: The text to speak.
    """
    with _tts_lock:
        try:
            engine = _get_engine()
            logger.info(f"[TTS] Speaking: '{text[:80]}...'")
            print(f"🔊 {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"[TTS] Speech failed: {e}")
            print(f"🔇 (TTS Error) {text}")


def speak_async(text: str):
    """
    Speak text aloud in a background thread (non-blocking).

    Args:
        text: The text to speak.
    """
    thread = threading.Thread(target=speak, args=(text,), daemon=True)
    thread.start()
    return thread


def set_rate(rate: int = 170):
    """Set speech rate (words per minute)."""
    with _tts_lock:
        engine = _get_engine()
        engine.setProperty("rate", rate)


def set_volume(volume: float = 0.9):
    """Set speech volume (0.0 to 1.0)."""
    with _tts_lock:
        engine = _get_engine()
        engine.setProperty("volume", max(0.0, min(1.0, volume)))


def list_voices() -> list:
    """List available TTS voices on this system."""
    engine = _get_engine()
    voices = engine.getProperty("voices")
    return [{"id": v.id, "name": v.name, "languages": v.languages} for v in voices]


if __name__ == "__main__":
    print("Testing TTS Engine...")
    print("Available voices:")
    for v in list_voices():
        print(f"  - {v['name']}")
    speak("Hello! I am Zeic, your privacy-preserving AI assistant. How can I help you today?")
    print("TTS test complete.")
