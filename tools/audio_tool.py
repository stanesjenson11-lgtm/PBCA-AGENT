"""
Audio Control Tool
Control system volume on Windows using pycaw.
"""

import logging
import sys

logger = logging.getLogger(__name__)


class AudioTool:
    """Control system audio volume (Windows only)."""

    def execute(self, entities: dict) -> dict:
        """
        Execute audio action.

        Args:
            entities: {
                'action': 'set_volume' | 'mute' | 'unmute' | 'get_volume',
                'level': int (0-100, for set_volume)
            }
        """
        if sys.platform != "win32":
            return {"success": False, "error": "Audio control is only supported on Windows."}

        action = entities.get("action", "get_volume").lower()

        try:
            if action == "set_volume":
                return self._set_volume(entities.get("level", 50))
            elif action == "mute":
                return self._set_mute(True)
            elif action == "unmute":
                return self._set_mute(False)
            elif action == "get_volume":
                return self._get_volume()
            else:
                return {"success": False, "error": f"Unknown audio action: {action}"}

        except ImportError:
            return {"success": False, "error": "pycaw not installed. Run: pip install pycaw comtypes"}
        except Exception as e:
            logger.error(f"[AUDIO] Error: {e}")
            return {"success": False, "error": f"Audio control failed: {e}"}

    def _get_audio_interface(self):
        """Get the Windows audio endpoint volume interface."""
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL, CoInitialize
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        # Initialize COM for this thread
        try:
            CoInitialize()
        except Exception:
            pass

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def _get_volume(self) -> dict:
        """Get current volume level."""
        volume = self._get_audio_interface()
        current = volume.GetMasterVolumeLevelScalar()
        muted = volume.GetMute()
        level = int(current * 100)

        return {
            "success": True,
            "volume": level,
            "muted": bool(muted),
            "message": f"🔊 Volume: {level}%{' (Muted)' if muted else ''}"
        }

    def _set_volume(self, level: int) -> dict:
        """Set volume to a specific level (0-100)."""
        level = max(0, min(100, int(level)))
        volume = self._get_audio_interface()
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)

        logger.info(f"[AUDIO] Volume set to {level}%")
        return {
            "success": True,
            "volume": level,
            "message": f"🔊 Volume set to {level}%"
        }

    def _set_mute(self, mute: bool) -> dict:
        """Mute or unmute system audio."""
        volume = self._get_audio_interface()
        volume.SetMute(int(mute), None)

        status = "muted" if mute else "unmuted"
        logger.info(f"[AUDIO] System {status}")
        return {
            "success": True,
            "muted": mute,
            "message": f"🔇 System {status}" if mute else f"🔊 System {status}"
        }

    def get_capabilities(self) -> list:
        return ["set_volume", "mute_volume", "get_volume"]


_tool = AudioTool()


def set_volume(level: int) -> dict:
    return _tool.execute({"action": "set_volume", "level": level})


def mute_volume() -> dict:
    return _tool.execute({"action": "mute"})


def unmute_volume() -> dict:
    return _tool.execute({"action": "unmute"})


def get_volume() -> dict:
    return _tool.execute({"action": "get_volume"})
