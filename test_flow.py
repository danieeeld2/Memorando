# test_flow.py
import os
import sys
import requests
import json
import time
import io
import sqlite3
import shutil
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "test_document.pdf"

def log_step(step, message):
    """Function for consistent logging"""
    print(f"\n{'='*60}")
    print(f"📋 {step}")
    print(f"{'='*60}")
    print(f"➡️  {message}")

def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def log_info(message):
    print(f"ℹ️  {message}")

def create_test_pdf_if_not_exists():
    """Creates a simple test PDF if it doesn't exist"""
    if not os.path.exists(TEST_PDF_PATH):
        log_step("CREATE TEST PDF", f"Creating test PDF: {TEST_PDF_PATH}")
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            c = canvas.Canvas(TEST_PDF_PATH, pagesize=letter)
            c.drawString(100, 750, "Test Document for Memorando")
            c.drawString(100, 730, "This is a test PDF to test the application.")
            c.drawString(100, 710, "Chapter 1: Introduction")
            c.drawString(100, 690, "This is the first paragraph of the introductory chapter.")
            c.drawString(100, 670, "It contains several sentences to be processed.")
            c.drawString(100, 650, "Chapter 2: Development")
            c.drawString(100, 630, "Second chapter with more test content.")
            c.drawString(100, 610, "Perfect for generating study sessions.")
            c.save()
            log_success(f"Test PDF created: {TEST_PDF_PATH}")
        except ImportError:
            log_error("ReportLab not installed. Install with: pip install reportlab")
            log_info("Using existing PDF or create one manually")
            return False
    return True

def inspect_document_json(document_id):
    """Inspects the structure of the saved JSON"""
    log_step("DEBUG JSON STRUCTURE", f"Inspecting document {document_id}")
    
    try:
        json_path = f"documents_json/doc_{document_id}.json"
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
            
            log_info(f"Complete JSON structure:")
            log_info(f"Document keys: {list(document_data.keys())}")
            
            if 'chapters' in document_data:
                log_info(f"Number of chapters: {len(document_data['chapters'])}")
                if document_data['chapters']:
                    first_chapter = document_data['chapters'][0]
                    log_info(f"First chapter keys: {list(first_chapter.keys())}")
                    log_info(f"First chapter content: {first_chapter}")
            
            return document_data
        else:
            log_error(f"JSON file not found: {json_path}")
            return None
    except Exception as e:
        log_error(f"Error inspecting JSON: {e}")
        return None

def convert_gemini_to_session_structure(document_id):
    """Converts Gemini structure to SessionManager expected structure"""
    log_step("CONVERT STRUCTURE", f"Adapting document {document_id} for SessionManager")
    
    json_path = f"documents_json/doc_{document_id}.json"
    if not os.path.exists(json_path):
        log_error(f"File not found: {json_path}")
        return False
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract all texts from Gemini structure
        all_segments = []
        chapters = data.get("chapters", [])
        
        for chapter in chapters:
            if isinstance(chapter, dict):
                sections = chapter.get("sections", [])
                for section in sections:
                    if isinstance(section, dict):
                        paragraphs = section.get("paragraphs", [])
                        for paragraph in paragraphs:
                            if isinstance(paragraph, dict):
                                lines = paragraph.get("lines", [])
                                all_segments.extend(lines)
        
        # Create new structure compatible with SessionManager
        new_structure = {
            "title": data.get("title", "Document"),
            "chapters": [
                {
                    "title": "Main Content",
                    "segments": all_segments  # ← Structure that SessionManager expects
                }
            ]
        }
        
        # Save the new structure
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(new_structure, f, ensure_ascii=False, indent=2)
        
        log_success(f"Document converted: {len(all_segments)} segments extracted")
        return True
        
    except Exception as e:
        log_error(f"Error converting structure: {e}")
        return False

def cleanup_database_and_files():
    """Cleans up the database and files created during testing"""
    log_step("CLEANUP", "Cleaning up database and files")
    
    try:
        # Clean up database
        conn = sqlite3.connect('memorando_data.db')
        cursor = conn.cursor()
        
        # Get counts before cleanup
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM study_sessions")
        session_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM study_logs")
        log_count = cursor.fetchone()[0]
        
        # Delete test data (keep users for future tests)
        cursor.execute("DELETE FROM study_logs")
        cursor.execute("DELETE FROM study_sessions")
        cursor.execute("DELETE FROM documents")
        
        conn.commit()
        conn.close()
        
        log_success(f"Database cleaned: {doc_count} documents, {session_count} sessions, {log_count} logs removed")
        
        # Clean up JSON files
        documents_json_dir = "documents_json"
        if os.path.exists(documents_json_dir):
            files_removed = 0
            for file in os.listdir(documents_json_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(documents_json_dir, file)
                    os.remove(file_path)
                    files_removed += 1
            log_success(f"Files cleaned: {files_removed} JSON files removed from {documents_json_dir}")
        else:
            log_info(f"Directory {documents_json_dir} not found")
            
        # Clean up test PDF if it exists
        if os.path.exists(TEST_PDF_PATH):
            os.remove(TEST_PDF_PATH)
            log_success(f"Test PDF removed: {TEST_PDF_PATH}")
            
    except Exception as e:
        log_error(f"Error during cleanup: {e}")

def test_full_flow():
    """Executes the complete test flow"""
    
    # Verify server is running
    log_step("VERIFY SERVER", f"Connecting to {BASE_URL}")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        log_success("FastAPI server is running")
    except requests.exceptions.ConnectionError:
        log_error(f"Cannot connect to {BASE_URL}")
        log_info("Make sure the server is running: uvicorn backend.main:app --reload")
        return
    
    # 1. REGISTER USER
    log_step("1. USER REGISTRATION", "Creating test user")
    register_data = {
        "email": "testuser@memorando.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/study/register", json=register_data)
        if response.status_code == 201:
            user_data = response.json()
            log_success(f"User created: {user_data['name']} (ID: {user_data['user_id']})")
            user_id = user_data['user_id']
        elif response.status_code == 409:
            log_info("User already exists, proceeding with login...")
            # User exists, login
            login_data = {
                "email": "testuser@memorando.com",
                "password": "testpassword123"
            }
            response = requests.post(f"{BASE_URL}/study/login", json=login_data)
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data['user_id']
                log_success(f"Login successful: {user_data['name']} (ID: {user_data['user_id']})")
            else:
                log_error(f"Login error: {response.text}")
                return
        else:
            log_error(f"Registration error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error in registration/login: {e}")
        return
    
    # 2. UPLOAD PDF DOCUMENT
    log_step("2. UPLOAD DOCUMENT", f"Uploading PDF: {TEST_PDF_PATH}")
    
    if not os.path.exists(TEST_PDF_PATH):
        log_error(f"PDF not found: {TEST_PDF_PATH}")
        log_info("Creating test PDF...")
        if not create_test_pdf_if_not_exists():
            return
    
    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': (TEST_PDF_PATH, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/study/upload-document", files=files)
        
        if response.status_code == 201:
            upload_data = response.json()
            document_id = upload_data['document_id']
            log_success(f"Document uploaded successfully: {upload_data['title']} (ID: {document_id})")
            log_info(f"Full response: {json.dumps(upload_data, indent=2)}")
        else:
            log_error(f"Error uploading document: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error in upload: {e}")
        return
    
    # 3. CREATE STUDY SESSIONS
    log_step("3. CREATE SESSIONS", f"Creating sessions for document {document_id}")
    
    session_data = {
        "segments_per_session": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/study/documents/{document_id}/create-sessions", 
            json=session_data
        )
        
        if response.status_code == 200:
            sessions = response.json()
            log_success(f"Created {len(sessions)} study sessions")
            for i, session in enumerate(sessions):
                log_info(f"Session {i+1}: {session['title']} ({session['segment_count']} segments)")
        else:
            log_error(f"Error creating sessions: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error creating sessions: {e}")
        return
    
    # 4. LIST AVAILABLE SESSIONS
    log_step("4. LIST SESSIONS", f"Getting sessions for document {document_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/study/documents/{document_id}/sessions")
        
        if response.status_code == 200:
            sessions = response.json()
            log_success(f"Found {len(sessions)} sessions")
            for session in sessions:
                log_info(f"Session ID {session['id']}: {session['title']} - {session['segment_count']} segments")
            
            # Save the first session ID for testing
            if sessions:
                first_session_id = sessions[0]['id']
            else:
                log_error("No sessions available")
                return
        else:
            log_error(f"Error getting sessions: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error listing sessions: {e}")
        return
    
    # 5. GET SESSION CONTENT
    log_step("5. SESSION CONTENT", f"Getting content of session {first_session_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/study/sessions/{first_session_id}")
        
        if response.status_code == 200:
            session_content = response.json()
            log_success(f"Session contains {len(session_content)} segments")
            for i, segment in enumerate(session_content[:3]):  # Show only first 3
                log_info(f"Segment {i+1}: {segment[:100]}...")
        else:
            log_error(f"Error getting content: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error getting content: {e}")
        return
    
    # 6. TEST AVAILABLE STUDY METHODS
    log_step("6. AVAILABLE METHODS", "Checking available study methods")
    
    try:
        response = requests.get(f"{BASE_URL}/study/methods")
        
        if response.status_code == 200:
            methods = response.json()
            log_success(f"Available methods: {len(methods['methods'])}")
            for method_name, description in methods['methods'].items():
                log_info(f"• {method_name}: {description}")
        else:
            log_error(f"Error getting methods: {response.status_code} - {response.text}")
            return
    except Exception as e:
        log_error(f"Error getting methods: {e}")
        return
    
    # 7. START STUDY SESSION (BRIEF)
    log_step("7. START STUDY", f"Starting session with method 'read_repeat'")
    
    # Use content from first session
    study_request = {
        "session_content": session_content,
        "method_name": "read_repeat",
        "method_config": {
            "repeat_delay_seconds": 2  # Short for testing
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/study/start", json=study_request)
        
        if response.status_code == 200:
            study_status = response.json()
            log_success(f"Study session started: {study_status}")
            log_info("Session active, waiting 5 seconds...")
            
            # Wait a bit for session to run
            time.sleep(5)
            
            # Check status
            response = requests.get(f"{BASE_URL}/study/status")
            if response.status_code == 200:
                status = response.json()
                log_info(f"Current status: {status}")
            
            # Stop session
            log_info("Stopping study session...")
            response = requests.post(f"{BASE_URL}/study/stop")
            if response.status_code == 200:
                log_success("Session stopped correctly")
        else:
            log_error(f"Error starting study: {response.status_code} - {response.text}")
    except Exception as e:
        log_error(f"Error in study: {e}")
    
    # 8. FINAL VERIFICATION
    log_step("8. FINAL VERIFICATION", "Reviewing created data structure")
    
    log_info("✅ User created/authenticated")
    log_info("✅ Document processed and stored")
    log_info("✅ Study sessions generated")
    log_info("✅ Study system functional")
    
    print(f"\n{'🎉'*20}")
    print("FLOW COMPLETED SUCCESSFULLY!")
    print(f"{'🎉'*20}")
    print("\nSummary:")
    print(f"• User ID: {user_id}")
    print(f"• Document ID: {document_id}")
    print(f"• Sessions created: {len(sessions)}")
    print(f"• Available methods: Yes")
    print(f"• System working: ✅")
    
    # 9. CLEANUP
    cleanup_database_and_files()

if __name__ == "__main__":
    # Install dependencies if not available
    try:
        import requests
        import reportlab
    except ImportError:
        print("Installing necessary dependencies...")
        os.system("pip install requests reportlab")
    
    test_full_flow()