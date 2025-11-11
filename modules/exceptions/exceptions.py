# modules/exceptions/exceptions.py
class InsufficientContentError(Exception):
    """
    Raised when the combined search content is too short,
    irrelevant, or otherwise not sufficient for AI processing.
    """

    def __init__(self, topic: str, message: str = None):
        default_message = f"No sufficient content found for topic: '{topic}'."
        super().__init__(message or default_message)
        self.topic = topic

class SearchFailedError(Exception):
    """Raised when the search module fails to retrieve data."""
    
class SearchBlockedError(Exception):
    """Raised when the search module is blocked or challenged."""
    def __init__(self, topic: str, message: str = None):
        default_message = f"Search was blocked or challenged for topic: '{topic}'."
        super().__init__(message or default_message)
        self.topic = topic

class ProxyFailureError(Exception):
    """Raised when all proxy attempts fail to fetch content."""
    def __init__(self, topic: str, message: str = None):
        default_message = f"All proxy attempts failed for topic: '{topic}'. This is a network/proxy infrastructure issue, not a problem with the lead."
        super().__init__(message or default_message)
        self.topic = topic

class LLMProcessingError(Exception):
    """Raised when LLM summarization or email generation fails."""
