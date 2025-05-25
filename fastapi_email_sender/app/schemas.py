from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailSchema(BaseModel):
    to_recipients: List[EmailStr] # Use EmailStr for validation
    subject: str
    html_body: str
    from_email: Optional[EmailStr] = None # Optional, will use default if not provided

class EmailResponseDetail(BaseModel):
    recipient: EmailStr
    status: str # e.g., "sent", "failed"
    error_message: Optional[str] = None

class EmailResponse(BaseModel):
    message: str
    details: Optional[List[EmailResponseDetail]] = None
