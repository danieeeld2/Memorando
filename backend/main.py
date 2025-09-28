from fastapi import FastAPI
from .api.study_routes import router as study_router 
import os

# --- FastAPI Initialization ---
# This is the main entry point for the API application.

app = FastAPI(
    title="Memorando App API",
    description="API for document processing, text-to-speech, and study session management.",
    version="0.1.0",
)

# 1. Include the API router
# All endpoints defined in study_routes.py will now be accessible under the /study prefix.
app.include_router(study_router)


@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to Memorando API! Check /docs for available endpoints."}


# To run this API locally (in your terminal):
# 1. Ensure requirements (fastapi, uvicorn, pypdf2, pyttsx3) are installed.
# 2. Run the command: uvicorn main:app --reload
# 3. Access the API documentation at http://127.0.0.1:8000/docs
