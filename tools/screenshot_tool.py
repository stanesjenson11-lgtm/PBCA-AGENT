"""
Screenshot Tool
Capture the screen and save to a safe directory.
Requires explicit approval every time (privacy-sensitive).
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ScreenshotTool:
    """Take screenshots and save them locally."""

    def __init__(self):
        # Save screenshots in user's Pictures folder
        self.save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "PBCA_Screenshots")
        os.makedirs(self.save_dir, exist_ok=True)

    def execute(self, entities: dict) -> dict:
        """
        Take a screenshot.

        Args:
            entities: {
                'filename': str (optional),
                'region': tuple (optional, x, y, w, h)
            }
        """
        try:
            import pyautogui
        except ImportError:
            return {"success": False, "error": "pyautogui not installed. Run: pip install pyautogui"}

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = entities.get("filename", f"screenshot_{timestamp}.png")
            if not filename.endswith(".png"):
                filename += ".png"

            filepath = os.path.join(self.save_dir, filename)

            # Capture
            region = entities.get("region")
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            screenshot.save(filepath)
            logger.info(f"[SCREENSHOT] Saved: {filepath}")

            return {
                "success": True,
                "filepath": filepath,
                "message": f"📸 Screenshot saved: {filepath}"
            }

        except Exception as e:
            logger.error(f"[SCREENSHOT] Error: {e}")
            return {"success": False, "error": f"Screenshot failed: {e}"}

    def get_capabilities(self) -> list:
        return ["take_screenshot"]


_tool = ScreenshotTool()


def take_screenshot(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
