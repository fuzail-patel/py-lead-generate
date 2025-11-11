import urllib3
from modules.main import WorkflowFacade
from modules.exceptions.exceptions import (
    InsufficientContentError,
    SearchFailedError,
    LLMProcessingError,
    SearchBlockedError,
    ProxyFailureError
)

# disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_workflow(
    topic: str,
    mode: str = "lead",
    recipient_name: str = "Dr. Smith",
    sender_company_summary: str = "",
    sender_info: dict = {},
    max_results: int = 5
):
    """
    Executes the workflow and returns results as a structured dictionary.
    Handles common workflow errors gracefully.
    """
    
    wf = WorkflowFacade()
    wf.email.set_email_config(**sender_info)

    # Validate mode
    mode = mode.lower()
    if mode not in ["lead", "general", "research"]:
        mode = "lead"

    try:
        # Run the workflow pipeline
        result = wf.process_topic(
            topic=topic,
            mode=mode,
            max_results=max_results,
            receipient_name=recipient_name,
            sender_company_summary=sender_company_summary
        )

        # return structured result
        return {
            "success": True,
            "topic": topic,
            "mode": mode,
            "summary": result["summary"],
            "email": result.get("email"),
            "content": result["content"],
        }

    except ProxyFailureError as e:
        return {
            "success": False,
            "error_type": "ProxyFailureError",
            "message": str(e),
            "topic": topic,
            "is_infrastructure_error": True  # Flag to indicate this is not a lead issue
        }

    except InsufficientContentError as e:
        return {
            "success": False,
            "error_type": "InsufficientContentError",
            "message": str(e),
            "topic": topic,
            "is_infrastructure_error": False  # This is a lead/content issue
        }

    except SearchFailedError as e:
        return {
            "success": False,
            "error_type": "SearchFailedError",
            "message": str(e),
            "topic": topic
        }
        
    except SearchBlockedError as e:
        return {
            "success": False,
            "error_type": "SearchBlockedError",
            "message": str(e),
            "topic": topic
        }

    except LLMProcessingError as e:
        return {
            "success": False,
            "error_type": "LLMProcessingError",
            "message": str(e),
            "topic": topic
        }

    except Exception as e:
        # fallback for unexpected errors
        return {
            "success": False,
            "error_type": "UnknownError",
            "message": str(e),
            "topic": topic
        }