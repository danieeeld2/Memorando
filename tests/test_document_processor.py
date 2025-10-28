import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from datetime import date

# Add the 'backend' directory to the path for correct imports from your project structure
# This is crucial for pytest to find your core modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Import the function to be tested
from core.document_processor import process_pdf_to_json 

# --- Setup Fixtures and Mock Data ---

# Define the expected JSON output (what Gemini would return)
MOCK_GEMINI_JSON_OUTPUT = {
    "title": "A Study of Quantum AI",
    "language": "en",
    "chapters": [
        {"chapter_title": "Introduction", "sections": []}
    ],
    "structured_elements": []
}

# The Gemini API returns a response object with a 'text' property containing the JSON string.
MOCK_RESPONSE_TEXT = json.dumps(MOCK_GEMINI_JSON_OUTPUT)

@pytest.fixture
def mock_pdf_file(tmp_path):
    """Creates a temporary, existing file path for testing."""
    dummy_pdf_path = tmp_path / "test_doc.pdf"
    dummy_pdf_path.write_text("dummy content")
    return str(dummy_pdf_path)

# --- Test Case for Successful API Call ---

# The test uses three patches:
# 1. 'client': Mocks the genai.Client() instance.
# 2. 'date.today': Ensures the 'uploaded_date' is consistent for assertion.
@patch("core.document_processor.date")
@patch("core.document_processor.client") 
def test_process_pdf_to_json_success(mock_client, mock_date, mock_pdf_file):
    """
    Tests the successful end-to-end process: 
    1. Uploads file.
    2. Calls generate_content.
    3. Deletes file.
    4. Returns correct structured JSON.
    """
    # 1. Setup Mock Date
    fixed_date_str = "2025-10-27"
    
    # Create a mock object that mimics the return value of date.today()
    mock_today_date = MagicMock()
    # Ensure that when .isoformat() is called on the mock, it returns a fixed string
    mock_today_date.isoformat.return_value = fixed_date_str

    # Tell the patched 'date' module that its 'today()' method should return our mock date object
    mock_date.today.return_value = mock_today_date

    # 2. Setup Mock Client Behavior
    # --- Mock File Upload ---
    mock_file_handle = MagicMock()
    mock_file_handle.name = "files/mock-pdf-12345" 
    mock_client.files.upload.return_value = mock_file_handle
    
    # --- Mock Gemini Response ---
    mock_response = MagicMock()
    mock_response.text = MOCK_RESPONSE_TEXT 
    mock_client.models.generate_content.return_value = mock_response

    # 3. Execute the function
    result = process_pdf_to_json(mock_pdf_file)

    # 4. Assertions

    # A. Verify API interactions
    # Check that the file was uploaded
    mock_client.files.upload.assert_called_once() 
    # Check that the content generation was called with the uploaded file
    mock_client.models.generate_content.assert_called_once()
    # Check that the temporary file was cleaned up (deleted)
    mock_client.files.delete.assert_called_once_with(name=mock_file_handle.name)

    # B. Verify Output structure and content
    assert isinstance(result, dict)
    assert result["title"] == MOCK_GEMINI_JSON_OUTPUT["title"]
    # CRITICAL: Verify the date was correctly injected/updated by the function
    assert result["uploaded_date"] == fixed_date_str
    assert result["language"] == MOCK_GEMINI_JSON_OUTPUT["language"]

# --- Test Case for Error Handling ---

@patch("core.document_processor.client")
def test_process_pdf_to_json_api_error(mock_client, mock_pdf_file):
    """
    Tests that the function handles exceptions (like a failed API call or network error) 
    and still attempts file cleanup.
    """
    # 1. Setup Mock Client Behavior
    mock_file_handle = MagicMock()
    mock_file_handle.name = "files/mock-pdf-error-54321" 
    mock_client.files.upload.return_value = mock_file_handle
    
    # Force the API call (generate_content) to raise an exception
    mock_client.models.generate_content.side_effect = Exception("Simulated API Error")

    # 2. Execute the function
    result = process_pdf_to_json(mock_pdf_file)

    # 3. Assertions
    
    # Check that the function returned None on failure
    assert result is None 
    
    # CRITICAL: Check that file cleanup (delete) was *still* called, even after the error
    mock_client.files.delete.assert_called_once_with(name=mock_file_handle.name)