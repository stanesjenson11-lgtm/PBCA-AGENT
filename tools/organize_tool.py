"""
File Organizer Tool
Automatically organize files in a directory by type/extension.
Moves files into categorized subfolders (Images, Documents, etc.).
Requires explicit approval (moves files).
"""

import logging
import os
import shutil

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Safe directories
SAFE_PREFIXES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    PROJECT_DIR,
]

# Category mappings
FILE_CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".csv", ".pptx", ".ppt"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Code": {".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".xml", ".yaml", ".yml"},
    "Executables": {".exe", ".msi", ".bat", ".cmd", ".sh"},
}


def _get_category(ext: str) -> str:
    """Get the category for a file extension."""
    for category, extensions in FILE_CATEGORIES.items():
        if ext.lower() in extensions:
            return category
    return "Other"


def _is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(os.path.expanduser(path))
    return any(abs_path.startswith(prefix) for prefix in SAFE_PREFIXES)


class OrganizeTool:
    """Organize files in a directory by type."""

    def execute(self, entities: dict) -> dict:
        """
        Organize a directory.

        Args:
            entities: {
                'directory': str (path to organize),
                'dry_run': bool (optional, preview only)
            }
        """
        directory = entities.get("directory", entities.get("path", ""))
        if not directory:
            return {"success": False, "error": "No directory specified."}

        directory = os.path.abspath(os.path.expanduser(directory))

        if not os.path.isdir(directory):
            return {"success": False, "error": f"Not a directory: {directory}"}

        if not _is_safe_path(directory):
            return {"success": False, "error": f"⛔ Directory outside safe paths: {directory}"}

        dry_run = entities.get("dry_run", False)

        try:
            moved = {}
            errors = []

            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)

                # Skip directories and hidden files
                if os.path.isdir(filepath) or filename.startswith("."):
                    continue

                ext = os.path.splitext(filename)[1]
                if not ext:
                    continue

                category = _get_category(ext)
                target_dir = os.path.join(directory, category)

                if not dry_run:
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, filename)

                    # Handle duplicates
                    if os.path.exists(target_path):
                        base, extension = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(target_path):
                            target_path = os.path.join(target_dir, f"{base}_{counter}{extension}")
                            counter += 1

                    try:
                        shutil.move(filepath, target_path)
                    except Exception as e:
                        errors.append(f"{filename}: {e}")
                        continue

                moved.setdefault(category, []).append(filename)

            # Format result
            total = sum(len(files) for files in moved.values())
            lines = [f"📂 {'[DRY RUN] ' if dry_run else ''}Organized {total} files in {os.path.basename(directory)}:"]
            for category, files in sorted(moved.items()):
                lines.append(f"  📁 {category}: {len(files)} files")
                for f in files[:5]:
                    lines.append(f"    • {f}")
                if len(files) > 5:
                    lines.append(f"    ... and {len(files) - 5} more")

            if errors:
                lines.append(f"\n⚠️ {len(errors)} errors:")
                for err in errors[:3]:
                    lines.append(f"  • {err}")

            return {
                "success": True,
                "moved": moved,
                "total": total,
                "errors": errors,
                "message": "\n".join(lines)
            }

        except Exception as e:
            logger.error(f"[ORGANIZE] Error: {e}")
            return {"success": False, "error": f"Organization failed: {e}"}

    def get_capabilities(self) -> list:
        return ["organize_directory"]


_tool = OrganizeTool()


def organize_directory(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
