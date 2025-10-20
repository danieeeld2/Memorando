import pytest
import os
import sys
import sqlite3
from fastapi.testclient import TestClient
from fastapi import status # Import HTTP status codes for clarity

# Adjust the path to allow imports from the 'backend' structure
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import classes to be tested
from backend.main import app
# Import the module that holds the global paths/instance
from backend.core import db_manager as db_module
from backend.services.user_service import UserService, hash_password, check_password
# Import the dependency function we need to override
from backend.api.study_routes import get_user_service 


# --- Fixtures for Isolated Testing (Crucial for database isolation) ---

class TestDBManager(db_module.DBManager):
    """A specific DBManager instance for testing, using temporary paths."""
    def __init__(self, test_db_path, test_doc_path):
        self.DB_PATH = test_db_path
        self.DOC_STORAGE_PATH = test_doc_path
        super().__init__()
        # Initialize the temporary DB and tables
        self.initialize_db()

@pytest.fixture(scope="module")
def isolated_user_service(tmp_path_factory):
    """
    Creates a completely isolated UserService instance with its own
    temporary DBManager and database file.
    """
    # 1. Setup temporary paths
    temp_dir = tmp_path_factory.mktemp("test_db_auth")
    test_db_path = os.path.join(temp_dir, "test_auth_" + db_module.DB_NAME)
    test_doc_path = os.path.join(temp_dir, "test_auth_" + db_module.DOC_STORAGE_DIR)
    
    # 2. Instantiate a test DB manager and test service
    temp_db_manager = TestDBManager(test_db_path, test_doc_path)
    # Inject the temporary manager into the UserService
    test_service = UserService(db_manager=temp_db_manager) 
    
    yield test_service
    
    # 3. Teardown: Clean up the temporary database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    if os.path.exists(test_doc_path):
        try:
             os.rmdir(test_doc_path)
        except OSError:
             pass

@pytest.fixture(scope="module")
def test_client_with_override(isolated_user_service):
    """
    Provides a TestClient that overrides the global get_user_service 
    dependency with our isolated test service.
    """
    # Function that returns the isolated service
    def override_get_user_service():
        return isolated_user_service
        
    # Override the dependency for the duration of the module tests
    app.dependency_overrides[get_user_service] = override_get_user_service
    
    client = TestClient(app)
    yield client
    
    # Clean up the override after the module tests finish
    app.dependency_overrides = {}


# --- Service Layer Tests (UserService) ---

def test_hash_and_check_password():
    """Tests the integrity of the bcrypt hash and check utilities."""
    password = "secure_password_123"
    hashed = hash_password(password)
    
    assert check_password(password, hashed) is True
    assert check_password("wrong_password", hashed) is False


def test_register_successful(isolated_user_service):
    """Tests successful user registration."""
    # The service returns a dict with 'user_id'
    user_data = isolated_user_service.register_user("test1@isolated.com", "password", "Test User 1")
    user_id = user_data["user_id"] if user_data else None

    assert user_id is not None
    assert isinstance(user_id, int)
    
    # Verify data exists in the isolated test DB
    conn = isolated_user_service.db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, name FROM users WHERE id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    
    assert data is not None
    assert data[0] == "test1@isolated.com"


def test_register_duplicate_email(isolated_user_service):
    """Tests that registering with a duplicate email fails."""
    # Register first user (ensure it's done from the same isolated session)
    isolated_user_service.register_user("duplicate@isolated.com", "password", "Original")
    
    # Attempt to register second user with same email
    user_data = isolated_user_service.register_user("duplicate@isolated.com", "password2", "Duplicated")
    
    assert user_data is None # Should return None on failure


# --- API Routes Tests (/register and /login) ---

def test_api_register_and_login_flow(test_client_with_override):
    """Tests the complete API flow: Register -> Login."""
    email = "api_user@isolated_flow.com"
    password = "api_password"
    name = "API Test User"

    # 1. API Register Test (POST /study/register)
    register_response = test_client_with_override.post(
        "/study/register",
        json={"email": email, "password": password, "name": name}
    )
    
    # Expect 201 Created
    assert register_response.status_code == status.HTTP_201_CREATED
    register_data = register_response.json()
    assert register_data["email"] == email
    user_id = register_data["user_id"]
    
    # 2. API Login Test (POST /study/login)
    login_response = test_client_with_override.post(
        "/study/login",
        json={"email": email, "password": password}
    )
    
    # Expect 200 OK
    assert login_response.status_code == status.HTTP_200_OK
    login_data = login_response.json()
    assert login_data["user_id"] == user_id


def test_api_register_duplicate_fails(test_client_with_override):
    """Tests that the API returns 409 when registering a duplicate user."""
    email = "duplicate_api@isolated_flow.com"
    
    # First successful registration
    test_client_with_override.post(
        "/study/register",
        json={"email": email, "password": "pass", "name": "First"}
    )
    
    # Second registration attempt (should fail)
    second_response = test_client_with_override.post(
        "/study/register",
        json={"email": email, "password": "pass2", "name": "Second"}
    )
    
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert "User already exists" in second_response.json()["detail"]


def test_api_login_invalid_credentials(test_client_with_override):
    """Tests API login failure with wrong password."""
    # Register a control user for this test scope
    email = "control_user@login_fail.com"
    test_client_with_override.post(
        "/study/register",
        json={"email": email, "password": "correct_password", "name": "Control User"}
    )
    
    # Attempt login with wrong password
    response = test_client_with_override.post(
        "/study/login",
        json={"email": email, "password": "wrong_password"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in response.json()["detail"]


def test_api_login_non_existent_user(test_client_with_override):
    """Tests API login failure with non-existent email."""
    response = test_client_with_override.post(
        "/study/login",
        json={"email": "no_one_here@isolated_run.com", "password": "any_password"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in response.json()["detail"]
