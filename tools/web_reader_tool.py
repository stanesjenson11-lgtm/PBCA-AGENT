"""
Web Reader Tool
Fetch and extract readable text from a URL (read-only, no interaction).
Uses requests + BeautifulSoup for clean text extraction.
"""

import logging

logger = logging.getLogger(__name__)


class WebReaderTool:
    """Read and extract text content from web pages."""

    def execute(self, entities: dict) -> dict:
        """
        Read content from a URL.

        Args:
            entities: {
                'url': str (the URL to read),
                'summarize': bool (optional, use LLM to summarize)
            }
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return {"success": False, "error": "requests or beautifulsoup4 not installed. Run: pip install requests beautifulsoup4"}

        url = entities.get("url", "")
        if not url:
            return {"success": False, "error": "No URL specified."}

        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            # Fetch page
            headers = {
                "User-Agent": "PBCA-Agent/1.0 (Local Privacy-Preserving Assistant)"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Extract title
            title = soup.title.string if soup.title else "No title"

            # Extract main text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up multiple newlines
            import re
            text = re.sub(r"\n{3,}", "\n\n", text)

            # Truncate for display
            display_text = text[:3000]
            if len(text) > 3000:
                display_text += f"\n\n... (truncated, {len(text)} chars total)"

            result = {
                "success": True,
                "url": url,
                "title": title,
                "text": text,
                "message": f"🌐 {title}\n{url}\n\n{display_text}"
            }

            # Optional LLM summary
            if entities.get("summarize"):
                try:
                    from agent.mistral_llm import query_mistral
                    summary = query_mistral(
                        f"Summarize this web page concisely:\n\nTitle: {title}\n\n{text[:3000]}",
                        "You are a content summarizer. Provide a clear, concise summary of the web page."
                    )
                    result["summary"] = summary
                    result["message"] = f"🌐 {title}\n{url}\n\n📝 Summary:\n{summary}"
                except Exception as e:
                    logger.error(f"[WEB] Summary failed: {e}")

            return result

        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Request timed out for: {url}"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {e}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Cannot connect to: {url}"}
        except Exception as e:
            logger.error(f"[WEB] Error: {e}")
            return {"success": False, "error": f"Failed to read URL: {e}"}

    def get_capabilities(self) -> list:
        return ["read_url"]


_tool = WebReaderTool()


def read_url(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
