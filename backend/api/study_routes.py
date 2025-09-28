from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
import os
import sys

from backend.services.study_service import StudyService, AVAILABLE_METHODS
from backend.core.document_processor import TextSplitOption


# --- Pydantic Models for Request and Response Validation ---

class StartStudyRequest(BaseModel):
    """Defines the required payload to start a study session."""
    pdf_path: str = Field(..., description="Absolute or relative path to the PDF document.")
    method_name: Literal["read_repeat"] = Field(..., description="The name of the study method to use.")
    split_by: TextSplitOption = Field("paragraph", description="How to fragment the text ('paragraph' or 'line').")
    method_config: Dict[str, Any] = Field(
        {"repeat_delay_seconds": 5}, 
        description="Configuration specific to the chosen method."
    )

class StudyStatusResponse(BaseModel):
    """Defines the response structure for the status endpoint."""
    is_active: bool = Field(..., description="True if a study session is currently running.")
    current_method: str | None = Field(None, description="The name of the currently active method, if any.")

class MethodListResponse(BaseModel):
    """Defines the response structure for listing available methods."""
    methods: Dict[str, str] = Field(..., description="A map of method names to their descriptions.")


# --- API Router Initialization ---

# Initialize the FastAPI router for study-related routes
router = APIRouter(prefix="/study", tags=["Study Session"])

# Instantiate the service that holds the core logic
# NOTE: In a production setting, this would typically be managed by dependency injection.
study_service = StudyService()

# --- Endpoint Definitions ---

@router.post("/start", response_model=StudyStatusResponse)
def start_study(request: StartStudyRequest):
    """
    Starts a new study session based on the provided PDF, method, and configuration.
    """
    
    # Check if the PDF path exists immediately
    if not os.path.exists(request.pdf_path):
         raise HTTPException(
            status_code=400, 
            detail=f"PDF file not found at: {request.pdf_path}"
        )
        
    # Delegate the complex task to the service layer
    success = study_service.start_study_session(
        pdf_path=request.pdf_path,
        method_name=request.method_name,
        split_by=request.split_by,
        method_config=request.method_config
    )

    if success:
        current_method_name = study_service.current_method.name if study_service.current_method else request.method_name
        return StudyStatusResponse(
            is_active=True,
            current_method=current_method_name
        )
    else:
        # If the service failed to start (e.g., PDF error, method not found)
        raise HTTPException(
            status_code=500, 
            detail="Failed to start study session. Check console for details."
        )


@router.post("/stop", response_model=StudyStatusResponse)
def stop_study():
    """
    Requests the active study session to stop gracefully.
    """
    success = study_service.stop_study_session()
    
    if success:
        return StudyStatusResponse(is_active=False, current_method=None)
    else:
        # Return 200 even if no session was running, indicating the desired state (stopped) is met
        return StudyStatusResponse(is_active=False, current_method=None)


@router.get("/status", response_model=StudyStatusResponse)
def get_study_status():
    """
    Retrieves the current status of the study application.
    """
    current_method_name = study_service.current_method.name if study_service.current_method else None
    
    return StudyStatusResponse(
        is_active=study_service.is_session_active,
        current_method=current_method_name
    )


@router.get("/methods", response_model=MethodListResponse)
def list_available_methods():
    """
    Lists all implemented study methods available for use.
    """
    method_descriptions = {
        name: method_cls().name 
        for name, method_cls in AVAILABLE_METHODS.items()
    }
    return MethodListResponse(methods=method_descriptions)
