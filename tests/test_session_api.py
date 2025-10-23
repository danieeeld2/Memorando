import pytest
import os
import sys
import sqlite3
import shutil
import json
from fastapi.testclient import TestClient
from fastapi import status

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
# Import the module that holds the global paths/instance
from backend.core import db_manager as db_module
# Import the class for type hinting and patching
from backend.core.db_manager import DBManager 

# --- Test Data ---

# This mimics the structure of EXAMPLE_DOCUMENT_JSON
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
# Total 6 segments


# --- Fixtures for Isolated DB and Doc Storage ---

# RENAMED: from TestDBManager to IsolatedDBManager to avoid PytestCollectionWarning
class IsolatedDBManager(db_module.DBManager):
    """A specific DBManager instance for testing, using temporary paths."""
    def __init__(self, test_db_path, test_doc_path):
        self.DB_PATH = test_db_path
        self.DOC_STORAGE_PATH = test_doc_path
        super().__init__()
        # Initialize the temporary DB and tables
        self.initialize_db()

@pytest.fixture(scope="function")
def isolated_db_manager(tmp_path_factory):
    """
    Creates a completely isolated DBManager with its own temp DB and doc storage.
    Yields the manager instance. Cleans up on exit.
    """
    temp_dir = tmp_path_factory.mktemp("test_session_api")
    test_db_path = os.path.join(temp_dir, "test_sessions.db")
    test_doc_path = os.path.join(temp_dir, "test_session_docs")
    
    # UPDATED: Use the renamed class
    temp_db_manager = IsolatedDBManager(test_db_path, test_doc_path)
    
    yield temp_db_manager
    
    # Teardown
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_client(isolated_db_manager, monkeypatch):
    """
    Provides a TestClient with the global db_manager patched to use
    the isolated_db_manager instance.
    """
    
    # Patch the global db_manager instance in the modules where it's imported
    monkeypatch.setattr('backend.api.study_routes.db_manager', isolated_db_manager)
    monkeypatch.setattr('backend.core.session_manager.db_manager', isolated_db_manager)
    
    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def setup_document(isolated_db_manager):
    """
    Sets up a dummy user and a dummy document (with its JSON file)
    in the isolated database. Yields the document_id and user_id.
    """
    user_id = 1
    document_id = 1
    
    # 1. Create dummy main JSON file
    doc_filename = f"doc{document_id}_user{user_id}_main.json"
    doc_filepath = os.path.join(isolated_db_manager.DOC_STORAGE_PATH, doc_filename)
    
    with open(doc_filepath, 'w', encoding='utf-8') as f:
        json.dump(MOCK_DOCUMENT_CONTENT, f)
        
    # 2. Insert user and document records into isolated DB
    conn = isolated_db_manager.get_connection()
    cursor = conn.cursor()
    
    # Insert dummy user (simplified, skips hashing for this test)
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, name) VALUES (?, ?, ?, ?)",
        (user_id, 'test@user.com', 'hash', 'Test User')
    )
    
    # Insert dummy document
    cursor.execute(
        "INSERT INTO documents (id, user_id, title, json_file_path) VALUES (?, ?, ?, ?)",
        (document_id, user_id, 'Test Document', doc_filepath)
    )
    conn.commit()
    conn.close()
    
    yield document_id, user_id


# --- API Endpoint Tests ---

def test_create_sessions_success(test_client, setup_document, isolated_db_manager):
    """
    Tests the POST /documents/{document_id}/create-sessions endpoint.
    """
    document_id, user_id = setup_document
    segments_per_session = 2
    
    # Act
    response = test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": segments_per_session}
    )
    
    # Assert API Response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 3 # 6 total segments / 2 per session = 3 sessions
    assert response_data[0]["title"] == f"Document {document_id} - Part 1"
    assert response_data[0]["segment_count"] == segments_per_session
    
    # Assert DB State
    conn = isolated_db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM study_sessions WHERE document_id = ?", (document_id,))
    count = cursor.fetchone()[0]
    assert count == 3
    
    # Assert File System State
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
    """
    Tests the GET /documents/{document_id}/sessions endpoint.
    """
    document_id, _ = setup_document
    
    # First, create sessions to list
    test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": 3}
    )
    
    # Act: Get the list of sessions
    response = test_client.get(f"/study/documents/{document_id}/sessions")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 2 # 6 segments / 3 per session = 2 sessions
    assert response_data[0]["title"] == f"Document {document_id} - Part 1"
    assert "created_at" in response_data[0]


def test_get_document_sessions_no_sessions_found(test_client, setup_document):
    """
    Tests 404 response when a document exists but has no sessions generated.
    """
    document_id, _ = setup_document
    
    # Act: Get sessions *without* creating any
    response = test_client.get(f"/study/documents/{document_id}/sessions")
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No study sessions found for this document."


def test_get_session_content_success(test_client, setup_document):
    """
    Tests the GET /sessions/{session_id} endpoint.
    """
    document_id, _ = setup_document
    
    # 1. Create sessions
    create_response = test_client.post(
        f"/study/documents/{document_id}/create-sessions",
        json={"segments_per_session": 4} # Create 2 sessions (4, 2)
    )
    created_sessions = create_response.json()
    session_id_1 = created_sessions[0]["session_id"] # e.g., s1, s2, s3, s4
    session_id_2 = created_sessions[1]["session_id"] # e.g., s5, s6
    
    # 2. Act: Get content for session 1
    response_1 = test_client.get(f"/study/sessions/{session_id_1}")
    
    # Assert session 1
    assert response_1.status_code == status.HTTP_200_OK
    assert response_1.json() == ["s1", "s2", "s3", "s4"]
    
    # 3. Act: Get content for session 2
    response_2 = test_client.get(f"/study/sessions/{session_id_2}")
    
    # Assert session 2
    assert response_2.status_code == status.HTTP_200_OK
    assert response_2.json() == ["s5", "s6"]


def test_get_session_content_not_found(test_client):
    """Tests 404 when session_id does not exist."""
    response = test_client.get("/study/sessions/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session ID '999' not found" in response.json()["detail"]

