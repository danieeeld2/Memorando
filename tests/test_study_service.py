import pytest
import os
import sys
import time
from unittest.mock import patch, MagicMock, PropertyMock
import threading
from typing import List, Dict, Any

# Adjust the path to allow imports from the 'backend' structure
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Classes imports
from backend.services.study_service import StudyService, AVAILABLE_METHODS
from backend.core.study_methods.base_method import StudyMethod
# NOTE: DocumentProcessor import is removed as it's no longer used by StudyService

# --- Mocks for Session Lifecycle ---

# 1. Mock Study Method for testing execution flow
class MockStudyMethod(StudyMethod):
    """A mocked study method that exposes its internal state for testing."""
    def __init__(self, tts_engine, study_data: List[str], config: Dict[str, Any] = None):
        super().__init__(tts_engine, study_data)
        self.name = "Mock Method"
        self._stop_requested = False
        self.run_started = threading.Event()
        self.run_finished = threading.Event()
        self.is_running = False
        self.config = config or {}

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
        # Call the base stop to ensure TTS mock is called
        super().stop()
        print("Mock stop requested.")

# 2. Update AVAILABLE_METHODS to use the Mock for testing
@pytest.fixture(autouse=True)
def mock_available_methods():
    """Temporarily replace the actual method with the mock for all tests."""
    original_methods = AVAILABLE_METHODS.copy()
    AVAILABLE_METHODS["read_repeat"] = MockStudyMethod
    yield
    # Restore the original methods after the test
    AVAILABLE_METHODS.clear()
    AVAILABLE_METHODS.update(original_methods)


# 3. Fixture for the StudyService and its dependencies
@pytest.fixture
def study_service():
    """Initializes StudyService with a mocked TTS Engine."""
    # 🔑 FIX: Patch the TtsEngine where StudyService imports it, not where it's defined.
    # Additionally, ensure the return_value is a full MagicMock instance.
    with patch('backend.services.study_service.TtsEngine', autospec=True) as MockTtsEngine:
        # Create a mock instance with a full specification (autospec=True)
        # to ensure it has all the real TtsEngine methods (like stop_speaking)
        mock_tts_instance = MagicMock()
        MockTtsEngine.return_value = mock_tts_instance
        
        # Temporarily create the service instance
        service = StudyService()
        
        # We assert that the service received the correctly mocked instance
        assert service.tts_engine is mock_tts_instance
        
        yield service
        
        # Clean up any running sessions after the test
        if service.is_session_active:
            service.stop_study_session()

# --- Test Cases ---

# Dummy session content to use in all relevant tests
DUMMY_SESSION_CONTENT = ["Segment 1.", "Segment 2.", "Segment 3."]
DUMMY_CONFIG = {"delay": 2}


def test_successful_session_start(study_service):
    """Verifies that a session starts successfully, flags are set, and the thread is running."""
    
    # Start the session with the new signature
    success = study_service.start_study_session(
        DUMMY_SESSION_CONTENT, 
        "read_repeat", 
        DUMMY_CONFIG
    )

    assert success is True
    assert study_service.is_session_active is True
    assert study_service.current_method is not None
    assert isinstance(study_service.current_method, MockStudyMethod)
    assert study_service.session_thread.is_alive()
    
    # Verify the method received the correct data and config
    assert study_service.current_method.study_data == DUMMY_SESSION_CONTENT
    assert study_service.current_method.config == DUMMY_CONFIG
    
    # Wait for the thread to finish its internal loop
    study_service.current_method.run_finished.wait(timeout=1)


def test_start_session_with_unknown_method(study_service):
    """Verifies that attempting to start an unknown method fails gracefully."""
    
    success = study_service.start_study_session(
        DUMMY_SESSION_CONTENT, 
        "unknown_method", 
        {}
    )
    
    assert success is False
    assert study_service.is_session_active is False
    assert study_service.current_method is None


def test_start_session_with_empty_content(study_service):
    """Verifies that a session fails if the session content list is empty."""
    
    success = study_service.start_study_session(
        [], # Empty content list
        "read_repeat", 
        {}
    )
    
    assert success is False
    assert study_service.is_session_active is False
    assert study_service.current_method is None


def test_session_stops_gracefully(study_service):
    """Verifies that a running session can be stopped cleanly."""
    
    # Start the session
    study_service.start_study_session(DUMMY_SESSION_CONTENT, "read_repeat", {})
    
    # Wait until the mock method has started running before stopping
    study_service.current_method.run_started.wait(timeout=1)
    
    active_thread = study_service.session_thread
    mock_tts_engine = study_service.tts_engine
    
    # Stop the session
    success = study_service.stop_study_session()

    assert success is True
    assert not study_service.is_session_active
    
    # Wait for the thread to terminate after the stop signal
    if active_thread:
        active_thread.join(timeout=1)
        assert not active_thread.is_alive()
    
    # Verify that the TTS engine was explicitly stopped by the MockStudyMethod's stop()
    mock_tts_engine.stop_speaking.assert_called_once()


def test_start_session_while_active_is_blocked(study_service):
    """Verifies that a new session cannot start while one is already active."""
    # Start the first session
    study_service.start_study_session(DUMMY_SESSION_CONTENT, "read_repeat", {})
    
    # Attempt to start the second session (should fail)
    success = study_service.start_study_session(DUMMY_SESSION_CONTENT, "read_repeat", {})
    
    assert success is False
    
    # Cleanup
    study_service.stop_study_session()


def test_stop_session_when_not_active(study_service):
    """Verifies that calling stop when no session is running returns False."""
    
    # The session is not active by default
    success = study_service.stop_study_session()
    
    assert success is False
    assert not study_service.is_session_active
    
    # The TTS engine should not have been called to stop
    study_service.tts_engine.stop_speaking.assert_not_called()
