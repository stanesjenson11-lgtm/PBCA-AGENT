"""
Meeting Recorder & Auto-Summarizer Tool
Record system/microphone audio, transcribe with Whisper,
and summarize with Mistral — extracting action items and decisions.
"""

import logging
import os
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class MeetingTool:
    """
    Record meeting audio locally, transcribe, and generate
    structured summaries with action items.
    """

    def __init__(self):
        self._recording = False
        self._audio_data = None
        self._record_thread = None
        self._sample_rate = 16000
        self.save_dir = os.path.join(os.path.expanduser("~"), "Documents", "PBCA_Meetings")
        os.makedirs(self.save_dir, exist_ok=True)

    def execute(self, entities: dict) -> dict:
        """
        Execute meeting action.

        Args:
            entities: {
                'action': 'start_recording' | 'stop_recording' | 'summarize_file',
                'file': str (optional, path to existing audio file),
                'duration': int (optional, max recording duration in seconds)
            }
        """
        action = entities.get("action", "start_recording").lower()

        if action in ("start_recording", "record_meeting"):
            return self._start_recording(entities)
        elif action in ("stop_recording", "stop_recording_and_summarize"):
            return self._stop_and_summarize(entities)
        elif action == "summarize_file":
            return self._summarize_file(entities)
        else:
            return {"success": False, "error": f"Unknown meeting action: {action}"}

    def _start_recording(self, entities: dict) -> dict:
        """Start recording audio from the microphone."""
        if self._recording:
            return {"success": False, "error": "Already recording! Say 'stop recording' to finish."}

        try:
            import sounddevice as sd
        except ImportError:
            return {"success": False, "error": "sounddevice not installed. Run: pip install sounddevice"}

        max_duration = int(entities.get("duration", 3600))  # Default 1 hour max
        max_duration = min(max_duration, 7200)  # Cap at 2 hours

        self._recording = True
        self._audio_data = []

        def record_callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"[MEETING] Audio status: {status}")
            if self._recording:
                self._audio_data.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="float32",
                callback=record_callback
            )
            self._stream.start()
            self._record_start = datetime.now()

            # Auto-stop timer
            def auto_stop():
                time.sleep(max_duration)
                if self._recording:
                    logger.info("[MEETING] Auto-stopping recording (max duration reached).")
                    self._recording = False

            self._record_thread = threading.Thread(target=auto_stop, daemon=True)
            self._record_thread.start()

            logger.info(f"[MEETING] Recording started (max {max_duration}s).")
            return {
                "success": True,
                "message": f"🎙️ Recording started! Say 'stop recording' to finish and get a summary.\nMax duration: {max_duration // 60} minutes."
            }

        except Exception as e:
            self._recording = False
            return {"success": False, "error": f"Failed to start recording: {e}"}

    def _stop_and_summarize(self, entities: dict) -> dict:
        """Stop recording, transcribe, and summarize."""
        if not self._recording and not self._audio_data:
            return {"success": False, "error": "No active recording to stop."}

        self._recording = False

        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass

        if not self._audio_data:
            return {"success": False, "error": "No audio data captured."}

        try:
            import numpy as np

            # Concatenate audio chunks
            audio = np.concatenate(self._audio_data, axis=0).flatten()
            duration_secs = len(audio) / self._sample_rate
            logger.info(f"[MEETING] Recorded {duration_secs:.1f} seconds of audio.")

            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = os.path.join(self.save_dir, f"meeting_{timestamp}.wav")

            import scipy.io.wavfile as wavfile
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(audio_path, self._sample_rate, audio_int16)
            logger.info(f"[MEETING] Audio saved: {audio_path}")

            # Transcribe with Whisper using direct numpy array (no ffmpeg needed)
            from voice.stt_engine import transcribe_audio_array
            transcript = transcribe_audio_array(audio.astype(np.float32), self._sample_rate, model_name="base")

            if not transcript or len(transcript.strip()) < 10:
                return {
                    "success": True,
                    "audio_path": audio_path,
                    "duration": f"{duration_secs:.1f}s",
                    "message": f"🎙️ Recording saved ({duration_secs:.0f}s) but no speech detected.\nFile: {audio_path}"
                }

            # Summarize with Mistral
            summary = self._generate_summary(transcript)

            # Save transcript and summary
            transcript_path = audio_path.replace(".wav", "_transcript.txt")
            summary_path = audio_path.replace(".wav", "_summary.txt")

            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(f"Meeting Transcript - {timestamp}\n")
                f.write(f"Duration: {duration_secs:.1f} seconds\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(transcript)

            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"Meeting Summary - {timestamp}\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(summary)

            self._audio_data = None

            return {
                "success": True,
                "audio_path": audio_path,
                "transcript_path": transcript_path,
                "summary_path": summary_path,
                "duration": f"{duration_secs:.1f}s",
                "transcript": transcript,
                "summary": summary,
                "message": f"📝 Meeting Summary ({duration_secs:.0f}s recording):\n\n{summary}\n\n📂 Files saved in: {self.save_dir}"
            }

        except Exception as e:
            logger.error(f"[MEETING] Error: {e}")
            return {"success": False, "error": f"Meeting processing failed: {e}"}

    def _summarize_file(self, entities: dict) -> dict:
        """Summarize an existing audio file."""
        filepath = entities.get("file", "")
        if not filepath:
            return {"success": False, "error": "No audio file specified."}

        filepath = os.path.abspath(os.path.expanduser(filepath))
        if not os.path.exists(filepath):
            return {"success": False, "error": f"File not found: {filepath}"}

        try:
            from voice.stt_engine import transcribe_audio_file
            transcript = transcribe_audio_file(filepath, model_name="base")

            if not transcript:
                return {"success": False, "error": "No speech detected in audio."}

            summary = self._generate_summary(transcript)

            return {
                "success": True,
                "transcript": transcript,
                "summary": summary,
                "message": f"📝 Meeting Summary:\n\n{summary}"
            }

        except Exception as e:
            return {"success": False, "error": f"Summarization failed: {e}"}

    def _generate_summary(self, transcript: str) -> str:
        """Use Mistral to extract structured meeting notes."""
        try:
            from agent.mistral_llm import query_mistral

            prompt = f"""Analyze this meeting transcript and provide a structured summary:

Transcript:
{transcript[:4000]}

Provide in this format:
## Key Points
- [bullet points of main discussion topics]

## Decisions Made
- [any decisions that were agreed upon]

## Action Items
- [specific tasks assigned, with names if mentioned]

## Follow-ups Needed
- [pending items that need follow-up]"""

            system = "You are a professional meeting note-taker. Extract key information clearly and concisely."
            return query_mistral(prompt, system)

        except Exception as e:
            logger.error(f"[MEETING] Summary generation failed: {e}")
            return f"(Summary generation failed: {e})\n\nRaw transcript:\n{transcript[:2000]}"

    def get_capabilities(self) -> list:
        return ["record_meeting", "stop_recording_and_summarize", "summarize_meeting"]


_tool = MeetingTool()


def record_meeting(entities: dict = None) -> dict:
    return _tool.execute({"action": "start_recording", **(entities or {})})


def stop_and_summarize(entities: dict = None) -> dict:
    return _tool.execute({"action": "stop_recording", **(entities or {})})


def summarize_meeting_file(entities: dict = None) -> dict:
    return _tool.execute({"action": "summarize_file", **(entities or {})})
