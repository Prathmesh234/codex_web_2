from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WebAgentResponse(BaseModel):
    """Structured response format for web agent tasks"""
    response: str = Field(..., description="The response/result from the web agent task")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when the response was generated")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for easy serialization"""
        return {
            "response": self.response,
            "timestamp": self.timestamp.isoformat()
        }