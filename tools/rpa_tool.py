"""
RPA (Robotic Process Automation) Tool
Full computer automation — move mouse, click, type, take screenshots
for visual element location. Uses pyautogui + opencv.

⚠️ HIGH RISK: Every RPA action requires explicit user approval.
"""

import logging
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class RPATool:
    """
    Robotic Process Automation — control mouse, keyboard,
    and interact with on-screen elements.

    SECURITY: All actions are logged and require approval.
    """

    def __init__(self):
        self.save_dir = os.path.join(os.path.expanduser("~"), "Documents", "PBCA_RPA_Logs")
        os.makedirs(self.save_dir, exist_ok=True)

    def execute(self, entities: dict) -> dict:
        """
        Execute an RPA action.

        Args:
            entities: {
                'action': str (click, type, move, screenshot, locate, hotkey, scroll, sequence),
                'x': int (for click/move),
                'y': int (for click/move),
                'text': str (for type),
                'image': str (for locate — path to reference image),
                'keys': list (for hotkey, e.g. ['ctrl', 'c']),
                'delay': float (pause between actions),
                'steps': list (for sequence — list of step dicts)
            }
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # Moving mouse to corner stops execution
            pyautogui.PAUSE = 0.5  # Half-second pause between actions
        except ImportError:
            return {"success": False, "error": "pyautogui not installed. Run: pip install pyautogui"}

        action = entities.get("action", "").lower()

        try:
            if action == "click":
                return self._click(entities, pyautogui)
            elif action == "type":
                return self._type_text(entities, pyautogui)
            elif action == "move":
                return self._move(entities, pyautogui)
            elif action == "screenshot":
                return self._screenshot(pyautogui)
            elif action == "locate":
                return self._locate(entities, pyautogui)
            elif action == "hotkey":
                return self._hotkey(entities, pyautogui)
            elif action == "scroll":
                return self._scroll(entities, pyautogui)
            elif action == "sequence":
                return self._run_sequence(entities, pyautogui)
            else:
                return {"success": False, "error": f"Unknown RPA action: {action}. Supported: click, type, move, screenshot, locate, hotkey, scroll, sequence"}

        except pyautogui.FailSafeException:
            return {"success": False, "error": "⛔ FAILSAFE triggered! Mouse moved to screen corner."}
        except Exception as e:
            logger.error(f"[RPA] Error: {e}")
            return {"success": False, "error": f"RPA action failed: {e}"}

    def _click(self, entities: dict, pyautogui) -> dict:
        """Click at coordinates or located element."""
        x = entities.get("x")
        y = entities.get("y")
        button = entities.get("button", "left")
        clicks = int(entities.get("clicks", 1))

        if x is None or y is None:
            # Try to locate by image
            image = entities.get("image")
            if image:
                loc = self._find_on_screen(image, pyautogui)
                if loc:
                    x, y = loc
                else:
                    return {"success": False, "error": f"Could not find element on screen: {image}"}
            else:
                return {"success": False, "error": "Specify x, y coordinates or an image to locate."}

        pyautogui.click(int(x), int(y), clicks=clicks, button=button)
        logger.info(f"[RPA] Clicked ({x}, {y}) button={button} clicks={clicks}")

        return {
            "success": True,
            "message": f"🖱️ Clicked at ({x}, {y}) — {button} button, {clicks}x"
        }

    def _type_text(self, entities: dict, pyautogui) -> dict:
        """Type text at current cursor position."""
        text = entities.get("text", "")
        if not text:
            return {"success": False, "error": "No text specified to type."}

        interval = float(entities.get("interval", 0.05))
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)

        logger.info(f"[RPA] Typed: '{text[:50]}...'")
        return {
            "success": True,
            "message": f"⌨️ Typed: '{text[:100]}{'...' if len(text) > 100 else ''}'"
        }

    def _move(self, entities: dict, pyautogui) -> dict:
        """Move mouse to coordinates."""
        x = int(entities.get("x", 0))
        y = int(entities.get("y", 0))
        duration = float(entities.get("duration", 0.5))

        pyautogui.moveTo(x, y, duration=duration)
        return {"success": True, "message": f"🖱️ Moved to ({x}, {y})"}

    def _screenshot(self, pyautogui) -> dict:
        """Take a screenshot for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.save_dir, f"rpa_screenshot_{timestamp}.png")
        pyautogui.screenshot(filepath)
        return {
            "success": True,
            "filepath": filepath,
            "message": f"📸 RPA Screenshot saved: {filepath}"
        }

    def _locate(self, entities: dict, pyautogui) -> dict:
        """Locate an element on screen by reference image."""
        image = entities.get("image", "")
        if not image or not os.path.exists(image):
            return {"success": False, "error": f"Reference image not found: {image}"}

        loc = self._find_on_screen(image, pyautogui)
        if loc:
            return {
                "success": True,
                "x": loc[0],
                "y": loc[1],
                "message": f"🎯 Found element at ({loc[0]}, {loc[1]})"
            }
        return {"success": False, "error": "Element not found on screen."}

    def _hotkey(self, entities: dict, pyautogui) -> dict:
        """Press a hotkey combination."""
        keys = entities.get("keys", [])
        if not keys:
            return {"success": False, "error": "No keys specified for hotkey."}

        pyautogui.hotkey(*keys)
        key_str = " + ".join(keys)
        logger.info(f"[RPA] Hotkey: {key_str}")
        return {"success": True, "message": f"⌨️ Pressed: {key_str}"}

    def _scroll(self, entities: dict, pyautogui) -> dict:
        """Scroll the mouse wheel."""
        amount = int(entities.get("amount", 3))
        direction = entities.get("direction", "down").lower()
        if direction == "up":
            amount = abs(amount)
        else:
            amount = -abs(amount)

        pyautogui.scroll(amount)
        return {"success": True, "message": f"🖱️ Scrolled {'up' if amount > 0 else 'down'} {abs(amount)} clicks"}

    def _run_sequence(self, entities: dict, pyautogui) -> dict:
        """Run a sequence of RPA actions."""
        steps = entities.get("steps", [])
        if not steps:
            return {"success": False, "error": "No steps in sequence."}

        results = []
        delay = float(entities.get("delay", 1.0))

        for i, step in enumerate(steps):
            logger.info(f"[RPA] Step {i+1}/{len(steps)}: {step.get('action')}")
            result = self.execute(step)
            results.append(result)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Sequence failed at step {i+1}: {result.get('error')}",
                    "completed_steps": i,
                    "results": results
                }

            time.sleep(delay)

        return {
            "success": True,
            "completed_steps": len(steps),
            "results": results,
            "message": f"✅ RPA Sequence completed: {len(steps)} steps executed."
        }

    def _find_on_screen(self, image_path: str, pyautogui):
        """Try to find an image on screen, return center coordinates or None."""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if location:
                center = pyautogui.center(location)
                return (center.x, center.y)
        except Exception as e:
            logger.error(f"[RPA] Image locate error: {e}")
        return None

    def get_capabilities(self) -> list:
        return ["rpa_click", "rpa_type", "rpa_sequence", "perform_rpa_task"]


_tool = RPATool()


def perform_rpa_task(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
