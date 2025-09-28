import threading
from typing import Dict, Any, Literal, Type
from backend.core.tts_engine import TtsEngine
from backend.core.document_processor import DocumentProcessor, TextSplitOption
from backend.core.study_methods.base_method import StudyMethod
from backend.core.study_methods.method_read_repeat import ReadRepeatMethod

# A dictionary to map string names to their respective StudyMethod classes
# This is the "Method Factory" used for scalability.
AVAILABLE_METHODS: Dict[str, Type[StudyMethod]] = {
    "read_repeat": ReadRepeatMethod,
    # Future methods will be added here: "flashcards": FlashcardMethod, etc.
}


class StudyService:
    """
    Orchestrates the entire study process:
    1. Manages core component instances (TTS, Processor).
    2. Coordinates text preparation.
    3. Selects, configures, and runs the chosen StudyMethod.
    4. Manages the lifecycle (start/stop) of the study session, typically in a separate thread.
    """

    def __init__(self):
        # 1. Initialize core dependencies
        self.tts_engine = TtsEngine()
        self.current_method: StudyMethod | None = None
        self.session_thread: threading.Thread | None = None
        self.is_session_active = False

    def start_study_session(
        self,
        pdf_path: str,
        method_name: str,
        split_by: TextSplitOption,
        method_config: Dict[str, Any]
    ) -> bool:
        """
        Loads the document, prepares the text, and starts the study method
        in a separate thread to keep the main application responsive.

        :param pdf_path: Path to the PDF document.
        :param method_name: The key name of the study method (e.g., 'read_repeat').
        :param split_by: How to fragment the text ('paragraph' or 'line').
        :param method_config: Specific settings for the chosen method (e.g., repetition delay).
        :return: True if the session started successfully, False otherwise.
        """
        if self.is_session_active:
            print("❌ Error: A study session is already active. Stop it first.")
            return False

        # 2. Get the chosen method class
        MethodClass = AVAILABLE_METHODS.get(method_name)
        if not MethodClass:
            print(f"❌ Error: Study method '{method_name}' is not recognized.")
            return False

        try:
            # 3. Process the document
            processor = DocumentProcessor(pdf_path)
            study_data = processor.fragment_text(split_by)

            if not study_data:
                print("❌ Error: Could not generate study data from the PDF.")
                return False

            # 4. Instantiate the study method
            self.current_method = MethodClass(
                tts_engine=self.tts_engine,
                study_data=study_data,
                config=method_config
            )

            # 5. Start the method in a separate thread
            # This is crucial because pyttsx3's runAndWait() is blocking.
            self.session_thread = threading.Thread(target=self._run_method_safely)
            self.session_thread.daemon = True # Allow program to exit even if thread is running
            self.session_thread.start()
            self.is_session_active = True
            print(f"✅ Session started with '{self.current_method.name}' in a new thread.")
            return True

        except (FileNotFoundError, ValueError, Exception) as e:
            print(f"❌ Failed to start session due to error: {e}")
            self.current_method = None
            return False

    def _run_method_safely(self):
        """Internal helper to run the study method and handle session cleanup."""
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
            # Note: In a production API, we would use async/await instead of sleep/join.
            if self.session_thread and self.session_thread.is_alive():
                 self.session_thread.join(timeout=2) 
            
            self.is_session_active = False
            self.current_method = None
            self.session_thread = None

            print("✅ Study session successfully stopped.")
            return True
        
        print("⚠️ No active study session to stop.")
        return False
