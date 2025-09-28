import pytest
import os
import sys
import time
from unittest.mock import patch, MagicMock, PropertyMock
import threading

# Add the 'backend' directory to the path for correct imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Classes imports
from backend.services.study_service import StudyService, AVAILABLE_METHODS
from backend.core.study_methods.base_method import StudyMethod
from backend.core.document_processor import DocumentProcessor

# --- Mocks for Session Lifecycle ---

# 1. Mock Study Method
class MockStudyMethod(StudyMethod):
    """A mocked study method that exposes its internal state for testing."""
    def __init__(self, tts_engine, study_data, config=None):
        super().__init__(tts_engine, study_data)
        self.name = "Mock Method"
        self._stop_requested = False
        self.run_started = threading.Event()
        self.run_finished = threading.Event()
        self.is_running = False

    def run(self):
        """Simulates the main study logic running in the dedicated thread."""
        self.is_running = True
        self.run_started.set()
        
        # Simulate a long-running task with stop check points
        for i in range(10):
            if self._stop_requested:
                break
            time.sleep(0.01)
        
        self.is_running = False
        self.run_finished.set()

    def stop(self):
        """Sets the stop flag to terminate the run loop."""
        self._stop_requested = True
        if self.tts_engine:
            self.tts_engine.stop_speaking()

# 2. Mock AVAILABLE_METHODS factory
@pytest.fixture(autouse=True)
def mock_available_methods():
    """Temporarily replaces the real 'read_repeat' method with the MockStudyMethod for testing."""
    original_methods = AVAILABLE_METHODS.copy()
    AVAILABLE_METHODS["read_repeat"] = MockStudyMethod
    yield
    AVAILABLE_METHODS.clear()
    AVAILABLE_METHODS.update(original_methods)

# 3. Proper mock setup for StudyService
@pytest.fixture
def study_service():
    """Provides a fresh StudyService instance with properly mocked dependencies."""
    
    # Create a mock TTS engine
    mock_tts_engine = MagicMock()
    mock_tts_engine.stop_speaking = MagicMock()
    
    # Mock DocumentProcessor to avoid file system dependencies
    with patch('backend.services.study_service.DocumentProcessor') as MockProcessor:
        # Configure the mock processor
        mock_processor_instance = MockProcessor.return_value
        mock_processor_instance.extract_text.return_value = "Dummy text."
        mock_processor_instance.fragment_text.return_value = ["Chunk 1", "Chunk 2", "Chunk 3"]
        
        # Create service instance
        service = StudyService()
        service.tts_engine = mock_tts_engine
        
        yield service

# --- StudyService Tests ---

def test_initial_state(study_service):
    """Verifies that the service starts in a clean, inactive state."""
    assert not study_service.is_session_active
    assert study_service.current_method is None
    assert study_service.session_thread is None

def test_start_session_success(study_service):
    """Verifies that a session successfully starts in a separate thread."""
    pdf_path = "dummy/path.pdf"
    method_name = "read_repeat"
    
    success = study_service.start_study_session(pdf_path, method_name, "line", {})
    
    assert success is True
    assert study_service.is_session_active
    assert study_service.session_thread.is_alive()
    assert isinstance(study_service.current_method, MockStudyMethod)
    
    # Cleanup
    study_service.stop_study_session()
    if study_service.session_thread:
        study_service.session_thread.join(timeout=1)

def test_stop_session_running(study_service):
    """Verifies that an active session can be stopped gracefully."""
    # Start the session
    study_service.start_study_session("dummy.pdf", "read_repeat", "line", {})
    
    # Ensure the thread has started running before stopping
    study_service.current_method.run_started.wait(timeout=1)
    
    active_thread = study_service.session_thread
    
    # Stop the session
    success = study_service.stop_study_session()

    assert success is True
    assert not study_service.is_session_active
    
    # Wait for the thread to terminate after the stop signal
    if active_thread:
        active_thread.join(timeout=1)
        assert not active_thread.is_alive()
    
    # Verify that the TTS engine was explicitly stopped
    study_service.tts_engine.stop_speaking.assert_called_once()

def test_start_session_while_active_is_blocked(study_service):
    """Verifies that a new session cannot start while one is already active."""
    # Start the first session
    study_service.start_study_session("dummy1.pdf", "read_repeat", "line", {})
    
    # Attempt to start the second session (should fail)
    success = study_service.start_study_session("dummy2.pdf", "read_repeat", "line", {})
    
    assert success is False
    
    # Cleanup
    study_service.stop_study_session()

def test_stop_session_when_not_active(study_service):
    """Verifies that calling stop when no session is running returns False."""
    # The session is not active by default
    success = study_service.stop_study_session()
    
    assert success is False
    assert not study_service.is_session_active
    # The TTS engine should not have been called
    study_service.tts_engine.stop_speaking.assert_not_called()