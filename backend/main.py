"""
Clew Directive - Local Development API Server

This FastAPI server wraps the Lambda handlers for local development.
In production, these handlers run as AWS Lambda functions behind API Gateway.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict

# Import Lambda handlers
from backend.lambda_vibe_check import lambda_handler as vibe_check_handler
from backend.lambda_refine_profile import lambda_handler as refine_profile_handler
from backend.lambda_generate_briefing import lambda_handler as generate_briefing_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("clew.api")

# Create FastAPI app
app = FastAPI(
    title="Clew Directive API",
    description="AI Learning Navigator - Local Development Server",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class VibeCheckRequest(BaseModel):
    vibe_check_responses: Dict[str, str] = Field(
        ...,
        description="Vibe Check responses with keys: skepticism, goal, learning_style, context"
    )


class ProfileResponse(BaseModel):
    profile: str = Field(..., description="Generated profile summary")


class RefineProfileRequest(BaseModel):
    original_profile: str = Field(..., description="Original profile to refine")
    user_correction: str = Field(..., description="User's correction feedback")


class GenerateBriefingRequest(BaseModel):
    approved_profile: str = Field(..., description="User-approved profile")


class BriefingResponse(BaseModel):
    learning_path: list
    total_hours: int
    next_steps: str
    pdf_url: str | None


# Helper function to convert Lambda response to FastAPI response
def lambda_to_fastapi(lambda_response: dict):
    """Convert Lambda handler response to FastAPI response"""
    import json
    
    status_code = lambda_response.get("statusCode", 500)
    body = json.loads(lambda_response.get("body", "{}"))
    
    if status_code != 200:
        error_message = body.get("error", "Unknown error")
        raise HTTPException(status_code=status_code, detail=error_message)
    
    return body


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Clew Directive API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/vibe-check", response_model=ProfileResponse)
async def vibe_check(request: VibeCheckRequest):
    """
    Process Vibe Check responses and generate profile summary.
    
    This endpoint analyzes the user's answers to 4 questions and generates
    a personalized profile summary using the Navigator agent.
    """
    logger.info("[api:vibe-check] Request received")
    
    # Create Lambda event format
    event = {
        "body": request.model_dump_json()
    }
    
    # Call Lambda handler
    lambda_response = vibe_check_handler(event, None)
    
    # Convert to FastAPI response
    return lambda_to_fastapi(lambda_response)


@app.post("/refine-profile", response_model=ProfileResponse)
async def refine_profile(request: RefineProfileRequest):
    """
    Refine profile based on user correction.
    
    This endpoint takes the original profile and user's correction feedback,
    then generates a revised profile using the Navigator agent.
    """
    logger.info("[api:refine-profile] Request received")
    
    # Create Lambda event format
    event = {
        "body": request.model_dump_json()
    }
    
    # Call Lambda handler
    lambda_response = refine_profile_handler(event, None)
    
    # Convert to FastAPI response
    return lambda_to_fastapi(lambda_response)


@app.post("/generate-briefing", response_model=BriefingResponse)
async def generate_briefing(request: GenerateBriefingRequest):
    """
    Generate learning path and Command Briefing PDF.
    
    This endpoint:
    1. Uses Scout agent to gather and verify resources
    2. Uses Navigator agent to generate personalized learning path
    3. Generates Command Briefing PDF
    4. Returns learning path with PDF download URL
    """
    logger.info("[api:generate-briefing] Request received")
    
    # Create Lambda event format
    event = {
        "body": request.model_dump_json()
    }
    
    # Call Lambda handler
    lambda_response = generate_briefing_handler(event, None)
    
    # Convert to FastAPI response
    return lambda_to_fastapi(lambda_response)


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Clew Directive API server...")
    logger.info("API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
