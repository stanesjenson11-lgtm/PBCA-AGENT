"""
Universal File & Folder Search Tool
Search the entire local disk for files and folders by name.
Supports exact, partial, and fuzzy matching across all drives.
Returns a ranked list of results with size and modification date.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from fnmatch import fnmatch

logger = logging.getLogger(__name__)

# Directories to skip during search (system/hidden/large dirs)
SKIP_DIRS = {
    "$Recycle.Bin", "$WinREAgent", "System Volume Information",
    "Windows", "ProgramData", "Recovery", "PerfLogs",
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "AppData", "MicrosoftEdgeBackups", ".cache", ".local",
}

# Max results to return
MAX_RESULTS = 25

# Max search time (seconds) before returning partial results
MAX_SEARCH_TIME = 30


def _get_search_roots() -> list:
    """Get all available drive letters on Windows, or home on Linux/Mac."""
    roots = []
    if os.name == "nt":
        # Windows: check all drive letters
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                roots.append(drive)
    else:
        roots.append(os.path.expanduser("~"))
    return roots


def _format_size(size_bytes: int) -> str:
    """Format file size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_time(timestamp: float) -> str:
    """Format a timestamp to a readable date string."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def _similarity(name: str, query: str) -> float:
    """
    Simple similarity score between 0.0 and 1.0.
    Higher = better match.
    """
    name_lower = name.lower()
    query_lower = query.lower()

    # Exact match
    if name_lower == query_lower:
        return 1.0

    # Exact match without extension
    name_stem = os.path.splitext(name_lower)[0]
    query_stem = os.path.splitext(query_lower)[0]
    if name_stem == query_stem:
        return 0.95

    # Name starts with query
    if name_lower.startswith(query_lower):
        return 0.9

    # Query is contained in name
    if query_lower in name_lower:
        return 0.8

    # All query words found in name
    query_words = query_lower.replace("_", " ").replace("-", " ").split()
    if all(w in name_lower for w in query_words):
        return 0.7

    # Fuzzy: count matching characters in order (subsequence match)
    qi = 0
    for ch in name_lower:
        if qi < len(query_lower) and ch == query_lower[qi]:
            qi += 1
    if qi == len(query_lower):
        return 0.5 + (0.2 * len(query_lower) / len(name_lower))

    # Partial word overlap
    name_words = set(name_lower.replace("_", " ").replace("-", " ").split())
    overlap = len(name_words & set(query_words))
    if overlap > 0:
        return 0.3 + (0.2 * overlap / max(len(query_words), 1))

    return 0.0


class SearchTool:
    """Universal file and folder search across all drives."""

    def execute(self, entities: dict) -> dict:
        """
        Search for files or folders.

        Args:
            entities: {
                'query': str (file/folder name to search for),
                'type': str (optional: 'file', 'folder', 'all'),
                'extension': str (optional: '.pdf', '.py', etc.),
                'drive': str (optional: 'C', 'D', etc.)
            }
        """
        query = entities.get("query", entities.get("name", entities.get("filename", "")))
        if not query:
            return {"success": False, "error": "No search query specified."}

        search_type = entities.get("type", "all").lower()
        extension = entities.get("extension", "")
        target_drive = entities.get("drive", "")

        # Determine search roots
        if target_drive:
            roots = [f"{target_drive.upper()}:\\"]
        else:
            roots = _get_search_roots()

        # Prioritized search dirs (search these first for speed)
        home = os.path.expanduser("~")
        priority_dirs = [
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Music"),
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Project dir
        ]

        logger.info(f"[SEARCH] Searching for '{query}' (type={search_type}) across {len(roots)} drive(s)")

        results = []
        searched_paths = set()
        start_time = time.time()
        timed_out = False

        # Phase 1: Search priority directories first
        for pdir in priority_dirs:
            if os.path.isdir(pdir) and pdir not in searched_paths:
                searched_paths.add(pdir)
                self._search_directory(pdir, query, search_type, extension, results, start_time, max_depth=10)

        # Phase 2: Search remaining drives (broader, shallower)
        if len(results) < MAX_RESULTS and (time.time() - start_time) < MAX_SEARCH_TIME:
            for root in roots:
                if (time.time() - start_time) >= MAX_SEARCH_TIME:
                    timed_out = True
                    break
                self._search_directory(
                    root, query, search_type, extension, results, start_time,
                    max_depth=8, skip_searched=searched_paths
                )

        if not results:
            return {
                "success": True,
                "count": 0,
                "message": f"🔍 No matches found for \"{query}\".\n\nTry:\n• A different name or partial name\n• Adding the extension (e.g. \"{query}.pdf\")\n• Checking a specific drive"
            }

        # Score and rank results
        for r in results:
            r["score"] = _similarity(r["name"], query)

        results.sort(key=lambda r: (-r["score"], r["path"]))

        # Deduplicate by path
        seen = set()
        unique = []
        for r in results:
            if r["path"] not in seen:
                seen.add(r["path"])
                unique.append(r)
        results = unique[:MAX_RESULTS]

        # Format output
        message = self._format_results(query, results, timed_out)

        return {
            "success": True,
            "count": len(results),
            "results": results,
            "message": message
        }

    def _search_directory(self, root_dir: str, query: str, search_type: str,
                          extension: str, results: list, start_time: float,
                          max_depth: int = 8, skip_searched: set = None):
        """Recursively search a directory for matching files/folders."""
        query_lower = query.lower()
        query_stem = os.path.splitext(query_lower)[0]

        # Extract extension from query if present
        _, query_ext = os.path.splitext(query_lower)

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Time check
            if (time.time() - start_time) >= MAX_SEARCH_TIME:
                return

            # Result limit
            if len(results) >= MAX_RESULTS * 3:  # Collect extra for ranking
                return

            # Depth check
            depth = dirpath.replace(root_dir, "").count(os.sep)
            if depth >= max_depth:
                dirnames.clear()
                continue

            # Skip system/hidden dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS
                and not d.startswith(".")
                and not d.startswith("$")
            ]

            # Skip already-searched dirs
            if skip_searched:
                dirnames[:] = [
                    d for d in dirnames
                    if os.path.join(dirpath, d) not in skip_searched
                ]

            # Search folder names
            if search_type in ("folder", "all", "directory"):
                for dirname in dirnames:
                    score = _similarity(dirname, query_lower)
                    if score >= 0.3:
                        full_path = os.path.join(dirpath, dirname)
                        try:
                            results.append({
                                "name": dirname,
                                "path": full_path,
                                "type": "folder",
                                "size": "",
                                "modified": "",
                                "score": score
                            })
                        except Exception:
                            pass

            # Search file names
            if search_type in ("file", "all"):
                for filename in filenames:
                    # Extension filter
                    if extension and not filename.lower().endswith(extension.lower()):
                        continue

                    score = _similarity(filename, query)
                    if score >= 0.3:
                        full_path = os.path.join(dirpath, filename)
                        try:
                            stat = os.stat(full_path)
                            results.append({
                                "name": filename,
                                "path": full_path,
                                "type": "file",
                                "size": _format_size(stat.st_size),
                                "size_bytes": stat.st_size,
                                "modified": _format_time(stat.st_mtime),
                                "score": score
                            })
                        except (OSError, PermissionError):
                            pass

    def _format_results(self, query: str, results: list, timed_out: bool) -> str:
        """Format search results for Telegram display."""
        lines = [f"🔍 Search results for \"{query}\":"]
        lines.append(f"Found {len(results)} match(es):\n")

        for i, r in enumerate(results, 1):
            icon = "📁" if r["type"] == "folder" else "📄"
            lines.append(f"{icon} {r['path']}")

            details = []
            if r.get("size"):
                details.append(f"Size: {r['size']}")
            if r.get("modified"):
                details.append(f"Modified: {r['modified']}")
            if details:
                lines.append(f"   {' | '.join(details)}")
            lines.append("")

        if timed_out:
            lines.append("⚠️ Search timed out — partial results shown.")
            lines.append("Tip: Specify a drive like \"find resume.pdf on D:\"")

        return "\n".join(lines)

    def get_capabilities(self) -> list:
        return ["search_files"]


_tool = SearchTool()


def search_files(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
