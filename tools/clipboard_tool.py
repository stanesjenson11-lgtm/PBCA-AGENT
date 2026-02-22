"""
Clipboard Manager Tool
Read from and write to the system clipboard.
"""

import logging

logger = logging.getLogger(__name__)


class ClipboardTool:
    """Manage the system clipboard — get and set content."""

    def execute(self, entities: dict) -> dict:
        """
        Execute clipboard action.

        Args:
            entities: {
                'action': 'get' or 'set',
                'content': str (for set)
            }
        """
        try:
            import pyperclip
        except ImportError:
            return {"success": False, "error": "pyperclip not installed. Run: pip install pyperclip"}

        action = entities.get("action", "get").lower()

        try:
            if action == "set":
                content = entities.get("content", "")
                if not content:
                    return {"success": False, "error": "No content provided to copy."}
                pyperclip.copy(content)
                logger.info(f"[CLIPBOARD] Set clipboard: '{content[:50]}...'")
                return {
                    "success": True,
                    "message": f"📋 Copied to clipboard: '{content[:100]}{'...' if len(content) > 100 else ''}'"
                }

            elif action == "get":
                content = pyperclip.paste()
                if not content:
                    return {"success": True, "content": "", "message": "📋 Clipboard is empty."}
                logger.info(f"[CLIPBOARD] Got clipboard: '{content[:50]}...'")
                return {
                    "success": True,
                    "content": content,
                    "message": f"📋 Clipboard content:\n{content[:500]}{'...' if len(content) > 500 else ''}"
                }

            else:
                return {"success": False, "error": f"Unknown clipboard action: {action}"}

        except Exception as e:
            logger.error(f"[CLIPBOARD] Error: {e}")
            return {"success": False, "error": f"Clipboard error: {e}"}

    def get_capabilities(self) -> list:
        return ["get_clipboard", "set_clipboard"]


_tool = ClipboardTool()


def get_clipboard() -> dict:
    return _tool.execute({"action": "get"})


def set_clipboard(content: str) -> dict:
    return _tool.execute({"action": "set", "content": content})
