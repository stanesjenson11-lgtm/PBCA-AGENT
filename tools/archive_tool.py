"""
File Compression / Archive Tool
Compress and extract ZIP archives.
Uses only stdlib (zipfile, shutil) — no external deps.
"""

import logging
import os
import zipfile
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

# Safe directories for archive operations
SAFE_PREFIXES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]


def _is_safe_path(path: str) -> bool:
    """Check if path is within safe directories."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    return any(abs_path.startswith(prefix) for prefix in SAFE_PREFIXES)


class ArchiveTool:
    """Compress and extract ZIP files."""

    def execute(self, entities: dict) -> dict:
        """
        Execute archive action.

        Args:
            entities: {
                'action': 'compress' or 'extract',
                'path': str (file/folder to compress, or ZIP to extract),
                'output': str (optional output path)
            }
        """
        action = entities.get("action", "compress").lower()

        if action == "compress":
            return self._compress(entities)
        elif action == "extract":
            return self._extract(entities)
        else:
            return {"success": False, "error": f"Unknown archive action: {action}"}

    def _compress(self, entities: dict) -> dict:
        """Compress a file or directory into a ZIP."""
        path = entities.get("path", "")
        if not path:
            return {"success": False, "error": "No path specified to compress."}

        path = os.path.expanduser(path)
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return {"success": False, "error": f"Path not found: {abs_path}"}

        if not _is_safe_path(abs_path):
            return {"success": False, "error": f"⛔ Path outside safe directories: {abs_path}"}

        # Output ZIP path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"{abs_path}_{timestamp}.zip"
        output = entities.get("output", default_output)
        output = os.path.abspath(os.path.expanduser(output))

        try:
            if os.path.isfile(abs_path):
                # Compress single file
                with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(abs_path, os.path.basename(abs_path))
            elif os.path.isdir(abs_path):
                # Compress directory
                shutil.make_archive(output.replace(".zip", ""), "zip", abs_path)
                output = output if output.endswith(".zip") else output + ".zip"
            else:
                return {"success": False, "error": f"Invalid path: {abs_path}"}

            size_mb = os.path.getsize(output) / (1024 * 1024)
            logger.info(f"[ARCHIVE] Compressed: {output} ({size_mb:.1f} MB)")

            return {
                "success": True,
                "output": output,
                "size_mb": f"{size_mb:.1f}",
                "message": f"📦 Compressed to: {output} ({size_mb:.1f} MB)"
            }

        except Exception as e:
            logger.error(f"[ARCHIVE] Compress error: {e}")
            return {"success": False, "error": f"Compression failed: {e}"}

    def _extract(self, entities: dict) -> dict:
        """Extract a ZIP archive."""
        path = entities.get("path", "")
        if not path:
            return {"success": False, "error": "No ZIP file specified."}

        path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        if not path.endswith(".zip"):
            return {"success": False, "error": "Only .zip files are supported."}

        if not _is_safe_path(path):
            return {"success": False, "error": f"⛔ Path outside safe directories: {path}"}

        # Output directory
        output_dir = entities.get("output", path.replace(".zip", ""))
        output_dir = os.path.abspath(os.path.expanduser(output_dir))

        try:
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(output_dir)
                file_count = len(zf.namelist())

            logger.info(f"[ARCHIVE] Extracted {file_count} files to: {output_dir}")

            return {
                "success": True,
                "output": output_dir,
                "file_count": file_count,
                "message": f"📂 Extracted {file_count} files to: {output_dir}"
            }

        except zipfile.BadZipFile:
            return {"success": False, "error": "Invalid or corrupted ZIP file."}
        except Exception as e:
            logger.error(f"[ARCHIVE] Extract error: {e}")
            return {"success": False, "error": f"Extraction failed: {e}"}

    def get_capabilities(self) -> list:
        return ["compress_files", "extract_files"]


_tool = ArchiveTool()


def compress_files(entities: dict = None) -> dict:
    return _tool.execute({"action": "compress", **(entities or {})})


def extract_files(entities: dict = None) -> dict:
    return _tool.execute({"action": "extract", **(entities or {})})
