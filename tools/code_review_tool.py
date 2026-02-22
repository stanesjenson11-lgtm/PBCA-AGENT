"""
Local Code Reviewer Tool
Reads a source code file and provides a detailed review
using Mistral LLM — bugs, security issues, and suggestions.
100% local, no code leaves your machine.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Supported extensions
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs",
    ".go", ".rs", ".rb", ".php", ".html", ".css", ".sql",
    ".sh", ".bat", ".ps1", ".yaml", ".yml", ".json", ".xml",
    ".kt", ".swift", ".r", ".m", ".lua"
}

# Project root directory
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Safe directories for code review
SAFE_PREFIXES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Projects"),
    PROJECT_DIR,
]


def _is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(os.path.expanduser(path))
    return any(abs_path.startswith(prefix) for prefix in SAFE_PREFIXES)


class CodeReviewTool:
    """
    Automated code review using local Mistral LLM.
    Analyzes: bugs, security issues, style, performance, suggestions.
    """

    def execute(self, entities: dict) -> dict:
        """
        Review a code file.

        Args:
            entities: {
                'path': str (file path to review),
                'focus': str (optional: 'bugs', 'security', 'performance', 'all')
            }
        """
        path = entities.get("path", entities.get("file", ""))
        if not path:
            return {"success": False, "error": "No file path specified for review."}

        path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        if not os.path.isfile(path):
            return {"success": False, "error": f"Not a file: {path}"}

        ext = os.path.splitext(path)[1].lower()
        if ext not in CODE_EXTENSIONS:
            return {"success": False, "error": f"Unsupported file type: {ext}. Supported: {', '.join(sorted(CODE_EXTENSIONS))}"}

        if not _is_safe_path(path):
            return {"success": False, "error": f"⛔ File outside safe directories: {path}"}

        # Read file
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except Exception as e:
            return {"success": False, "error": f"Cannot read file: {e}"}

        if not code.strip():
            return {"success": False, "error": "File is empty."}

        # Truncate very large files
        max_chars = 6000
        truncated = False
        if len(code) > max_chars:
            code = code[:max_chars]
            truncated = True

        focus = entities.get("focus", "all").lower()
        filename = os.path.basename(path)

        # Generate review with Mistral
        try:
            from agent.mistral_llm import query_mistral

            focus_instruction = ""
            if focus == "bugs":
                focus_instruction = "Focus primarily on bugs and logic errors."
            elif focus == "security":
                focus_instruction = "Focus primarily on security vulnerabilities."
            elif focus == "performance":
                focus_instruction = "Focus primarily on performance optimizations."

            prompt = f"""Review this code file and provide a detailed analysis.
{focus_instruction}

File: {filename} ({ext})
{'(First ' + str(max_chars) + ' chars shown)' if truncated else ''}

```
{code}
```

Provide your review in this format:

## 🐛 Bugs & Issues
- [List any bugs, logic errors, or potential crashes]

## 🔒 Security Concerns
- [List any security vulnerabilities, injection risks, etc.]

## 💡 Suggestions & Improvements
- [Code quality, readability, best practices]

## ⚡ Performance Notes
- [Any performance concerns or optimizations]

## 📊 Overall Rating
[Give a rating out of 10 and a one-line verdict]"""

            system = "You are an expert code reviewer. Be thorough, specific, and actionable. Reference line numbers when possible."
            review = query_mistral(prompt, system)

            return {
                "success": True,
                "file": path,
                "filename": filename,
                "lines": code.count("\n") + 1,
                "review": review,
                "message": f"📝 Code Review: {filename}\n{'=' * 40}\n\n{review}"
            }

        except Exception as e:
            logger.error(f"[CODE_REVIEW] LLM error: {e}")
            return {"success": False, "error": f"Code review failed: {e}"}

    def get_capabilities(self) -> list:
        return ["review_code"]


_tool = CodeReviewTool()


def review_code(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
