from utils.helpers import is_sufficient_content, is_search_blocked
from modules.exceptions.exceptions import InsufficientContentError, SearchBlockedError

class FilterModule:
    def __init__(self):
        pass

    def filter_insufficient_and_blocked_content(self, content: str, topic: str):
        if is_search_blocked(content):
            raise SearchBlockedError(topic)
        if not is_sufficient_content(content):
            raise InsufficientContentError(topic)
        return True
    
    def filter_page_contents(self, pages: tuple, topic: str):
        # Optimize string concatenation: use list and join instead of +=
        content_parts = []
        
        for page in pages:
            cleaned = self.clean(page.get("content", " "))
            if cleaned:
                content_parts.append(cleaned)
        
        content = " ".join(content_parts)
            
        if not is_sufficient_content(content):
            raise InsufficientContentError(topic)

        return content

    def clean(self, text: str):
        """
        Additional filtering:
        - Deduplicate whitespace
        - Remove very short or empty content
        """
        if not text:
            return None
        text = " ".join(text.split())  # normalize whitespace
        if len(text) < 200:
            return None
        return text
