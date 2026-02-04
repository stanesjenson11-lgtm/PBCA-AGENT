"""
Web Search Tool
Uses DuckDuckGo for privacy-preserving web searches
"""

from typing import Dict, List
from duckduckgo_search import DDGS

def search(query: str, max_results: int = 5) -> Dict:
    """
    Perform a web search using DuckDuckGo
    
    Args:
        query: Search query
        max_results: Number of results to return (default 5)
    
    Returns:
        Dict with success status and results list
    """
    try:
        results = []
        with DDGS() as ddgs:
            # text() returns generator of results
            ddgs_gen = ddgs.text(query, max_results=max_results)
            for r in ddgs_gen:
                results.append({
                    "title": r.get("title"),
                    "href": r.get("href"),
                    "body": r.get("body")
                })
                
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test search
    print("Testing web search:")
    res = search("current weather in Tokyo")
    print(res)
