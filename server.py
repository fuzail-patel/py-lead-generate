from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from run_workflow import run_workflow
from dotenv import load_dotenv

# load env
load_dotenv();

app = FastAPI(
    title="Lead Generator API",
    description="AI-powered outreach email/content generator built with FastAPI",
    version="1.0.0"
)

class SenderInfo(BaseModel):
    sender_name: Optional[str] = Field(None, example="John Doe")
    sender_title: Optional[str] = Field(None, example="Sales Lead")
    sender_company: Optional[str] = Field(None, example="Techify CRM")
    sender_phone: Optional[str] = Field(None, example="+1234567890")
    sender_email: Optional[str] = Field(None, example="john@techify.com")
    sender_website: Optional[str] = Field(None, example="https://techify.com")
    sender_address: Optional[str] = Field(None, example="123 Main St, City, State")

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, example="Loop Company", description="Company name or topic to research (required)")
    mode: str = Field("lead", example="lead", description="Workflow mode: 'lead', 'general', or 'research'")
    recipient_name: Optional[str] = Field("", example="John Doe", description="Recipient name for personalized emails")
    sender_company_summary: Optional[str] = Field("", example="We are a payment integration consultancy that helps businesses optimize their payment workflows", description="Description of YOUR company (the sender) - helps AI write personalized outreach emails mentioning your services. This is NOT about the target company.")
    sender_info: Optional[SenderInfo] = Field(default_factory=SenderInfo, description="Sender information for email signature")
    max_results: Optional[int] = Field(5, ge=1, le=20, example=5, description="Maximum number of search results (1-20)")

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v):
        """Ensure topic is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError("Topic is required and cannot be empty or whitespace")
        return v.strip()

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Ensure mode is one of the valid options"""
        valid_modes = ['lead', 'general', 'research']
        if v.lower() not in valid_modes:
            raise ValueError(f"Mode must be one of: {', '.join(valid_modes)}")
        return v.lower()

class GenerateResponse(BaseModel):
    success: bool
    mode: str
    summary: Optional[str] = None
    email: Optional[Dict[str, Any]] = None
    content: Optional[str] = None

@app.post(
    "/api/generate",
    response_model=GenerateResponse,
    summary="Generate outreach email or content",
    description="Calls internal workflow to create AI-powered outreach material based on topic and mode. Requires 'topic' field."
)
async def generate(payload: GenerateRequest):
    """
    Generate outreach email or research content.
    
    **Required fields:**
    - `topic`: Company name or topic to research (cannot be empty)
    
    **Optional fields:**
    - `mode`: Workflow mode ('lead', 'general', 'research') - defaults to 'lead'
    - `recipient_name`: Name for personalized emails
    - `sender_company_summary`: Description of YOUR company (the sender) - helps AI personalize the email by mentioning your services
    - `sender_info`: Sender information for email signature
    - `max_results`: Number of search results (1-20, default: 5)
    
    **Returns:**
    - For 'lead' mode: summary + email (subject + body)
    - For other modes: summary + content
    """
    try:
        # Convert sender_info to dict, removing None values
        sender_info_dict = {}
        if payload.sender_info:
            sender_info_dict = {k: v for k, v in payload.sender_info.model_dump().items() if v is not None}
        
        result = run_workflow(
            topic=payload.topic,
            mode=payload.mode,
            recipient_name=payload.recipient_name or "",
            sender_company_summary=payload.sender_company_summary or "",
            sender_info=sender_info_dict,
            max_results=payload.max_results
        )

        if not result.get("success", True):
            raise HTTPException(status_code=400, detail=result)

        if payload.mode == "lead":
            return {
                "success": True,
                "mode": payload.mode,
                "summary": result.get("summary", ""),
                "email": result.get("email", {})
            }
        else:
            return {
                "success": True,
                "mode": payload.mode,
                "summary": result.get("summary", ""),
                "content": result.get("content", "")
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate endpoint: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error_type": "InternalError", "message": str(e)})
