"""
PDF Reader Tool
Read and extract text from PDF files locally.
Uses pypdf (pure Python, no external deps).
"""

import logging
import os
import glob

logger = logging.getLogger(__name__)

# Project root directory (where files are commonly stored)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Safe directories — include common user dirs + project folder
SAFE_PREFIXES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    PROJECT_DIR,
]


def _is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(os.path.expanduser(path))
    return any(abs_path.startswith(prefix) for prefix in SAFE_PREFIXES)


def _find_file(filename: str) -> str:
    """
    Search for a file by name in safe directories.
    Returns the absolute path if found, or empty string.
    """
    # If already an absolute path and exists, return it
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    # Search in safe prefixes (project dir, downloads, documents, desktop)
    search_dirs = [PROJECT_DIR] + SAFE_PREFIXES
    for search_dir in search_dirs:
        # Direct match
        candidate = os.path.join(search_dir, filename)
        if os.path.exists(candidate):
            return candidate

        # Recursive search (up to 3 levels deep)
        pattern = os.path.join(search_dir, "**", filename)
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]

    return ""


class PdfTool:
    """Read text content from PDF files."""

    def execute(self, entities: dict) -> dict:
        """
        Read a PDF file.

        Args:
            entities: {
                'path': str (path to PDF file),
                'pages': str (optional, e.g. '1-5' or 'all'),
                'summarize': bool (optional, use LLM to summarize)
            }
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            return {"success": False, "error": "pypdf not installed. Run: pip install pypdf"}

        path = entities.get("path", "")
        if not path:
            return {"success": False, "error": "No PDF path specified."}

        # Try to find the file
        resolved = _find_file(path)
        if not resolved:
            # Also try with .pdf extension
            if not path.lower().endswith(".pdf"):
                resolved = _find_file(path + ".pdf")

        if not resolved:
            return {
                "success": False,
                "error": f"File not found: {path}\nSearched in: {', '.join(os.path.basename(d) for d in SAFE_PREFIXES)}"
            }

        path = resolved

        if not path.lower().endswith(".pdf"):
            return {"success": False, "error": "File is not a PDF."}

        if not _is_safe_path(path):
            return {"success": False, "error": f"⛔ File outside safe directories: {path}"}

        try:
            reader = PdfReader(path)
            total_pages = len(reader.pages)

            # Parse page range
            pages_str = str(entities.get("pages", "all")).lower()
            if pages_str == "all":
                page_range = range(total_pages)
            else:
                try:
                    parts = pages_str.split("-")
                    start = max(0, int(parts[0]) - 1)
                    end = min(total_pages, int(parts[-1]))
                    page_range = range(start, end)
                except (ValueError, IndexError):
                    page_range = range(min(5, total_pages))  # Default first 5

            # Extract text
            text_parts = []
            for i in page_range:
                page_text = reader.pages[i].extract_text() or ""
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")

            full_text = "\n\n".join(text_parts)

            # Truncate for display (keep full for LLM)
            display_text = full_text[:2000]
            if len(full_text) > 2000:
                display_text += f"\n\n... (truncated, {len(full_text)} chars total)"

            result = {
                "success": True,
                "path": path,
                "total_pages": total_pages,
                "pages_read": len(list(page_range)),
                "text": full_text,
                "message": f"📄 PDF: {os.path.basename(path)} ({total_pages} pages)\n\n{display_text}"
            }

            # Optional LLM summary
            if entities.get("summarize"):
                try:
                    from agent.mistral_llm import query_mistral
                    summary = query_mistral(
                        f"Summarize this document concisely:\n\n{full_text[:3000]}",
                        "You are a document summarizer. Provide a clear, concise summary."
                    )
                    result["summary"] = summary
                    result["message"] += f"\n\n📝 Summary:\n{summary}"
                except Exception as e:
                    logger.error(f"[PDF] Summary failed: {e}")

            return result

        except Exception as e:
            logger.error(f"[PDF] Error reading {path}: {e}")
            return {"success": False, "error": f"Failed to read PDF: {e}"}

    def get_capabilities(self) -> list:
        return ["read_pdf"]


_tool = PdfTool()


def read_pdf(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
