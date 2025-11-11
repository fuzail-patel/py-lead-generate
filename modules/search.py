from typing import List, Optional
from urllib.parse import quote_plus
import time, random
from modules.proxy import proxy
from constants.searchTemplates import SEARCH_TEMPLATES
from modules.exceptions.exceptions import ProxyFailureError

DUCK_SEARCH_BASE = "https://duckduckgo.com/html/"

class Search:
    def __init__(self, per_page: int = 10, page_delay: float = 0.8):
        self.per_page = per_page
        self.page_delay = page_delay

    def _build_queries(self, topic: str, mode: Optional[str]) -> str:
        templates = SEARCH_TEMPLATES.get(mode, SEARCH_TEMPLATES.get("general", []))
        queries = [t.replace("{topic}", topic) for t in templates]
        return " + ".join(queries)

    def _format_search_url(self, q: str, offset: int = 0) -> str:
        return f"{DUCK_SEARCH_BASE}?q={quote_plus(q)}&s={offset}"

    def _fetch(self, url: str) -> Optional[str]:
        return proxy.fetch(url)

    def search(self, topic: str, mode: Optional[str] = None) -> str:
        query = self._build_queries(topic, mode)
        url = self._format_search_url(query)
        
        # Start timing
        start_time = time.time()
        print(f"[SEARCH] Searching DuckDuckGo for: '{topic}'...")
        
        try:
            content, resp = self._fetch(url)
            
            # Calculate and log elapsed time
            elapsed_time = time.time() - start_time
            print(f"[SEARCH] DuckDuckGo search completed in {elapsed_time:.2f} seconds for: '{topic}'")
            
            return content
        except ProxyFailureError as e:
            # Log time even on failure
            elapsed_time = time.time() - start_time
            print(f"[SEARCH] DuckDuckGo search failed after {elapsed_time:.2f} seconds for: '{topic}'")
            
            # Re-raise with topic context for better error messages
            raise ProxyFailureError(
                topic,
                f"All proxy attempts failed while searching for '{topic}'. This indicates a network/proxy infrastructure issue, not that the lead is invalid. {str(e)}"
            )