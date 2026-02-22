"""
Speech-to-Text Engine
Uses OpenAI Whisper (local) for offline speech recognition.
No cloud calls — runs entirely on local GPU/CPU.
"""

import logging
import numpy as np
import tempfile
import os

logger = logging.getLogger(__name__)

# Lazy-loaded model to save memory at startup
_whisper_model = None


def _load_model(model_name: str = "base"):
    """
    Lazy-load the Whisper model.
    Uses 'base' by default (~1 GB VRAM) to fit within 6 GB RTX 3050.
    Options: tiny (~390 MB), base (~1 GB), small (~2 GB).
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info(f"[STT] Loading Whisper model '{model_name}'...")
            _whisper_model = whisper.load_model(model_name)
            logger.info(f"[STT] Whisper model '{model_name}' loaded successfully.")
        except ImportError:
            raise RuntimeError(
                "openai-whisper is not installed. "
                "Install it with: pip install openai-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    return _whisper_model


def transcribe_audio_file(audio_path: str, model_name: str = "base") -> str:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_path: Path to a WAV/MP3/FLAC audio file.
        model_name: Whisper model size ('tiny', 'base', 'small').

    Returns:
        Transcribed text string.

    Raises:
        FileNotFoundError: If audio file does not exist.
        RuntimeError: If Whisper fails.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _load_model(model_name)

    try:
        logger.info(f"[STT] Transcribing: {audio_path}")
        result = model.transcribe(audio_path, fp16=False)
        text = result.get("text", "").strip()
        logger.info(f"[STT] Transcription: '{text}'")
        return text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def transcribe_audio_array(audio_array: np.ndarray, sample_rate: int = 16000,
                           model_name: str = "base") -> str:
    """
    Transcribe a numpy audio array to text.
    Passes the array DIRECTLY to Whisper — no ffmpeg needed.

    Args:
        audio_array: Numpy array of audio samples (float32, mono).
        sample_rate: Sample rate of the audio (default 16000 Hz for Whisper).
        model_name: Whisper model size.

    Returns:
        Transcribed text string.
    """
    import whisper

    model = _load_model(model_name)

    # Whisper expects float32 mono audio at 16 kHz
    if audio_array.dtype != np.float32:
        audio_array = audio_array.astype(np.float32)

    # Resample to 16 kHz if needed
    if sample_rate != 16000:
        # Simple resampling via interpolation
        duration = len(audio_array) / sample_rate
        target_len = int(duration * 16000)
        indices = np.linspace(0, len(audio_array) - 1, target_len)
        audio_array = np.interp(indices, np.arange(len(audio_array)), audio_array).astype(np.float32)

    # Pad/trim to 30 seconds as Whisper expects
    audio_array = whisper.pad_or_trim(audio_array)

    try:
        logger.info("[STT] Transcribing audio array directly (no ffmpeg needed)...")
        # Compute log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio_array).to(model.device)

        # Decode
        options = whisper.DecodingOptions(fp16=False, language="en")
        result = whisper.decode(model, mel, options)

        text = result.text.strip()
        logger.info(f"[STT] Transcription: '{text}'")
        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def listen_from_microphone(duration: int = 5, sample_rate: int = 16000,
                           model_name: str = "base") -> str:
    """
    Record audio from the default microphone and transcribe.
    Uses direct numpy array path — no ffmpeg dependency.

    Args:
        duration: Recording duration in seconds (default 5).
        sample_rate: Audio sample rate.
        model_name: Whisper model size.

    Returns:
        Transcribed text.
    """
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError(
            "sounddevice is not installed. Install with: pip install sounddevice"
        )

    logger.info(f"[STT] Listening for {duration} seconds...")
    print(f"🎤 Listening... (speak now, {duration}s)")

    try:
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()  # Block until recording is done
        print("✅ Recording complete. Transcribing...")

        # Flatten to 1D float32
        audio_data = recording.flatten().astype(np.float32)

        # Use direct array transcription (no file, no ffmpeg)
        return transcribe_audio_array(audio_data, sample_rate, model_name)

    except Exception as e:
        raise RuntimeError(f"Microphone recording failed: {e}")


def detect_wake_word(audio_text: str, wake_word: str = "hey pbca") -> bool:
    """
    Check if the transcribed text starts with the wake word.

    Args:
        audio_text: Transcribed text from STT.
        wake_word: The wake phrase to listen for.

    Returns:
        True if wake word detected.
    """
    return audio_text.lower().strip().startswith(wake_word.lower())


def strip_wake_word(audio_text: str, wake_word: str = "hey pbca") -> str:
    """
    Remove the wake word prefix from the transcribed text.

    Args:
        audio_text: Full transcribed text.
        wake_word: Wake word to remove.

    Returns:
        Text with wake word removed.
    """
    text = audio_text.strip()
    if text.lower().startswith(wake_word.lower()):
        text = text[len(wake_word):].strip()
        # Remove leading punctuation
        text = text.lstrip(",.!? ")
    return text


if __name__ == "__main__":
    # Test: record 5 seconds and transcribe
    print("Testing STT Engine...")
    try:
        text = listen_from_microphone(duration=5)
        print(f"You said: {text}")
    except Exception as e:
        print(f"Error: {e}")
