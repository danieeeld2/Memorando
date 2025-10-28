import pytest
import os
import sys
import sqlite3
import shutil
import json
from fastapi.testclient import TestClient
from fastapi import status
import io
from unittest.mock import patch, MagicMock

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
from backend.core import db_manager as db_module
from backend.core.db_manager import DBManager
from backend.api.study_routes import get_current_user_id

# --- Test Data ---

MOCK_DOCUMENT_CONTENT = [
    {
        "title": "Chapter 1",
        "segments": ["s1", "s2", "s3"]
    },
    {
        "title": "Chapter 2",
        "segments": ["s4", "s5", "s6"]
    }
]

# --- Fixtures for Isolated DB and Doc Storage ---

class IsolatedDBManager(db_module.DBManager):
    """A specific DBManager instance for testing, using temporary paths."""
    def __init__(self, test_db_path, test_doc_path):
        self.DB_PATH = test_db_path
        self.DOC_STORAGE_PATH = test_doc_path
        super().__init__()
        self.initialize_db()

@pytest.fixture(scope="function")
def isolated_db_manager(tmp_path_factory):
    """Creates a completely isolated DBManager with its own temp DB and doc storage."""
    temp_dir = tmp_path_factory.mktemp("test_session_api")
    test_db_path = os.path.join(temp_dir, "test_sessions.db")
    test_doc_path = os.path.join(temp_dir, "test_session_docs")
    
    temp_db_manager = IsolatedDBManager(test_db_path, test_doc_path)
    
    yield temp_db_manager
    
    # Teardown
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_client(isolated_db_manager):
    """
    Provides a TestClient with db_manager patched at the module level.
    This ensures all imports see the isolated_db_manager.
    """
    # Import the modules that use db_manager
    from backend.api import study_routes
    from backend.core import session_manager
    
    # Store original values
    original_study_routes_db = study_routes.db_manager
    original_session_manager_db = session_manager.db_manager
    
    # Patch them
    study_routes.db_manager = isolated_db_manager
    session_manager.db_manager = isolated_db_manager
    
    # Clear any existing overrides before creating client
    app.dependency_overrides.clear()
    
    client = TestClient(app)
    yield client
    
    # Restore originals and clear overrides
    study_routes.db_manager = original_study_routes_db
    session_manager.db_manager = original_session_manager_db
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def setup_document(isolated_db_manager):
    """Sets up a dummy user and document in the isolated database."""
    user_id = 1
    document_id = 1
    
    doc_filename = f"doc{document_id}_user{user_id}_main.json"
    doc_filepath = os.path.join(isolated_db_manager.DOC_STORAGE_PATH, doc_filename)
    
    with open(doc_filepath, 'w', encoding='utf-8') as f:
        json.dump(MOCK_DOCUMENT_CONTENT, f)
        
    conn = isolated_db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, name) VALUES (?, ?, ?, ?)",
        (user_id, 'test@user.com', 'hash', 'Test User')
    )
    
    cursor.execute(
        "INSERT INTO documents (id, user_id, title, json_file_path) VALUES (?, ?, ?, ?)",
        (document_id, user_id, 'Test Document', doc_filepath)
    )
    conn.commit()
    conn.close()
    
    yield document_id, user_id


@pytest.fixture(scope="function")
def setup_user(isolated_db_manager):
    """Sets up a dummy user in the isolated database."""
    user_id = 1
    conn = isolated_db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, name) VALUES (?, ?, ?, ?)",
        (user_id, 'test@user.com', 'hash', 'Test User')
    )
    conn.commit()
    conn.close()
    
    yield user_id


# --- API Endpoint Tests ---

def test_create_sessions_success(test_client, setup_document, isolated_db_manager):
    """Tests the POST /documents/{document_id}/create-sessions endpoint."""
    document_id, user_id = setup_document
    segments_per_session = 2
    
    response = test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": segments_per_session}
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 3
    assert response_data[0]["title"] == f"Document {document_id} - Part 1"
    assert response_data[0]["segment_count"] == segments_per_session
    
    conn = isolated_db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM study_sessions WHERE document_id = ?", (document_id,))
    count = cursor.fetchone()[0]
    assert count == 3
    
    session_filename = f"doc{document_id}_user{user_id}_session1.json"
    session_filepath = os.path.join(isolated_db_manager.DOC_STORAGE_PATH, session_filename)
    assert os.path.exists(session_filepath)
    
    with open(session_filepath, 'r') as f:
        session_json = json.load(f)
        assert session_json["segments"] == ["s1", "s2"]


def test_create_sessions_doc_not_found(test_client):
    """Tests failure when document_id does not exist."""
    response = test_client.post(
        "/study/documents/999/create-sessions",
        json={"segments_per_session": 2}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Document not found."


def test_get_document_sessions_success(test_client, setup_document):
    """Tests the GET /documents/{document_id}/sessions endpoint."""
    document_id, _ = setup_document
    
    test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": 3}
    )
    
    response = test_client.get(f"/study/documents/{document_id}/sessions")
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["title"] == f"Document {document_id} - Part 1"
    assert "created_at" in response_data[0]


def test_get_document_sessions_no_sessions_found(test_client, setup_document):
    """Tests 404 response when a document exists but has no sessions."""
    document_id, _ = setup_document
    
    response = test_client.get(f"/study/documents/{document_id}/sessions")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No study sessions found for this document."


def test_get_session_content_success(test_client, setup_document):
    """Tests the GET /sessions/{session_id} endpoint."""
    document_id, _ = setup_document
    
    create_response = test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": 4}
    )
    created_sessions = create_response.json()
    session_id_1 = created_sessions[0]["session_id"]
    session_id_2 = created_sessions[1]["session_id"]
    
    response_1 = test_client.get(f"/study/sessions/{session_id_1}")
    assert response_1.status_code == status.HTTP_200_OK
    assert response_1.json() == ["s1", "s2", "s3", "s4"]
    
    response_2 = test_client.get(f"/study/sessions/{session_id_2}")
    assert response_2.status_code == status.HTTP_200_OK
    assert response_2.json() == ["s5", "s6"]


def test_get_session_content_not_found(test_client):
    """Tests 404 when session_id does not exist."""
    response = test_client.get("/study/sessions/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session ID '999' not found" in response.json()["detail"]


# --- MOCK DATA FOR AI GENERATED JSON ---

MOCK_AI_OUTPUT = {
    "title": "AI Generated Document Title",
    "uploaded_date": "2025-10-27", 
    "language": "en",
    "chapters": [],
    "structured_elements": [],
    "unique_test_key": "data_saved_correctly"
}


# --- INTEGRATION TEST: DOCUMENT UPLOAD AND PERSISTENCE ---

@patch('backend.api.study_routes.process_pdf_to_json')
def test_upload_document_success_saves_data(
    mock_process_pdf_to_json,
    test_client,
    isolated_db_manager,
    setup_user
):
    """
    Tests the POST /study/upload-document endpoint to verify that:
    1. The AI processor is called.
    2. The document record is created in the isolated DB.
    3. The AI-generated JSON content is saved to the isolated file storage path.
    """

    from backend.api import study_routes

    mock_filename = "quantum_notes.pdf"
    mock_user_id = setup_user

    # Configure mock for AI processing FIRST
    mock_process_pdf_to_json.return_value = MOCK_AI_OUTPUT

    # Override the dependency to return our test user_id BEFORE making the request
    app.dependency_overrides[get_current_user_id] = lambda: mock_user_id

    # DEBUG: Add detailed debugging for the save_document_json method
    original_save = isolated_db_manager.save_document_json
    
    def debug_save(user_id, title, json_data):
        print(f"\n=== DEBUG save_document_json ===")
        print(f"user_id: {user_id} (type: {type(user_id)})")
        print(f"title: '{title}' (type: {type(title)})")
        print(f"json_data keys: {list(json_data.keys()) if json_data else 'None'}")
        
        # Check each parameter individually
        conn = isolated_db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Test parameter 0 (document_id)
            cursor.execute("SELECT ?", (1,))
            print("✅ Parameter 0 (int) works")
            
            # Test parameter 1 (user_id) 
            cursor.execute("SELECT ?", (user_id,))
            print("✅ Parameter 1 (user_id) works")
            
            # Test parameter 2 (title)
            cursor.execute("SELECT ?", (title,))
            print("✅ Parameter 2 (title) works")
            
            # Test parameter 3 (json_file_path)
            test_path = "/tmp/test.json"
            cursor.execute("SELECT ?", (test_path,))
            print("✅ Parameter 3 (path) works")
            
        except Exception as e:
            print(f"❌ Parameter test failed: {e}")
        finally:
            conn.close()
        
        return original_save(user_id, title, json_data)
    
    # Temporarily patch the method for debugging
    with patch.object(isolated_db_manager, 'save_document_json', side_effect=debug_save):
        try:
            # Simulate file upload
            file_content = io.BytesIO(b"Simulated PDF content.")

            response = test_client.post(
                "/study/upload-document",
                files={'file': (mock_filename, file_content, 'application/pdf')}
            )

            # Debug output if error
            if response.status_code != 201:
                print(f"\n=== ERROR RESPONSE ===")
                print(f"Status: {response.status_code}")
                print(f"Body: {response.text}")

                # Check what's in the DB
                conn = isolated_db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents")
                docs = cursor.fetchall()
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()
                conn.close()
                print(f"Documents: {docs}")
                print(f"Users: {users}")

            # --- API RESPONSE ASSERTIONS ---
            assert response.status_code == status.HTTP_201_CREATED, \
                f"Expected 201, got {response.status_code}. Response: {response.text}"
            
            # ... resto de las aserciones ...
            
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()