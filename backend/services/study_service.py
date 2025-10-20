import threading
from typing import Dict, Any, Type, List
from backend.core.tts_engine import TtsEngine
from backend.core.study_methods.base_method import StudyMethod
from backend.core.study_methods.method_read_repeat import ReadRepeatMethod

# A dictionary to map string names to their respective StudyMethod classes
AVAILABLE_METHODS: Dict[str, Type[StudyMethod]] = {
    "read_repeat": ReadRepeatMethod,
}


class StudyService:
    """
    Orchestrates the study process, now exclusively working with pre-processed
    session content (a list of strings).

    1. Manages core component instances (TTS).
    2. Selects, configures, and runs the chosen StudyMethod.
    3. Manages the session lifecycle (start/stop).
    """

    def __init__(self):
        # Initialize core dependencies
        self.tts_engine = TtsEngine()
        self.current_method: StudyMethod | None = None
        self.session_thread: threading.Thread | None = None
        self.is_session_active = False

    def start_study_session(
        self,
        session_content: List[str],
        method_name: str,
        method_config: Dict[str, Any]
    ) -> bool:
        """
        Takes the content of a single session and starts the study method
        in a separate thread.

        :param session_content: List of text fragments that make up the session.
        :param method_name: The key name of the study method (e.g., 'read_repeat').
        :param method_config: Specific configuration for the chosen method.
        :return: True if the session started successfully, False otherwise.
        """
        if self.is_session_active:
            print("❌ Error: A study session is already active. Stop it first.")
            return False

        # Get the chosen method class
        MethodClass = AVAILABLE_METHODS.get(method_name)
        if not MethodClass:
            print(f"❌ Error: Study method '{method_name}' is not recognized.")
            return False

        if not session_content:
            print("❌ Error: No valid session content provided.")
            return False
            
        try:
            study_data = session_content

            # Instantiate the study method
            self.current_method = MethodClass(
                tts_engine=self.tts_engine,
                study_data=study_data,
                config=method_config
            )

            # Start the method in a separate thread
            self.session_thread = threading.Thread(target=self._run_method_safely)
            self.session_thread.daemon = True
            self.session_thread.start()
            self.is_session_active = True
            print(f"✅ Session started with '{self.current_method.name}' in a new thread.")
            return True

        except Exception as e:
            print(f"❌ Failed to start the session due to an error: {e}")
            self.current_method = None
            return False

    def _run_method_safely(self):
        """Internal function to execute the study method and handle session cleanup."""
        if self.current_method:
            try:
                self.current_method.run()
            except Exception as e:
                print(f"❌ Error in study session thread: {e}")
            finally:
                # Cleanup and state reset when the run() method exits
                self.is_session_active = False
                self.current_method = None
                print("✅ Study session thread terminated.")

    def stop_study_session(self) -> bool:
        """
        Signals the running study method to stop and cleans up the session state.

        :return: True if a session was stopped, False if none was running.
        """
        if self.is_session_active and self.current_method:
            print("🛑 Requesting active session to stop...")
            # Delegate the stop signal to the method instance
            self.current_method.stop() 
            
            # Wait briefly for the thread to recognize the stop signal and finish
            if self.session_thread and self.session_thread.is_alive():
                 self.session_thread.join(timeout=2) 
            
            self.is_session_active = False
            self.current_method = None
            self.session_thread = None

            print("✅ Study session successfully stopped.")
            return True
        
        print("⚠️ No active study session to stop.")
        return False
