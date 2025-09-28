import time
from typing import List, Dict, Any
from backend.core.study_methods.base_method import StudyMethod

class ReadRepeatMethod(StudyMethod):
    """
    Implements the 'Read and Repeat' study method.
    The TTS engine reads a chunk of text, pauses for a set duration (for the user to repeat it aloud),
    and then moves to the next chunk.
    """
    
    def __init__(self, tts_engine, study_data: List[str], config: Dict[str, Any]):
        """
        Initializes the method.
        
        :param tts_engine: The TTS engine instance.
        :param study_data: List of text chunks (e.g., sentences).
        :param config: Dictionary containing specific configuration, 
                       e.g., 'repeat_delay_seconds'.
        """
        super().__init__(tts_engine, study_data)
        self.name = "Leer y Repetir"
        self.config = config
        self.repeat_delay = config.get("repeat_delay_seconds", 5)
        self.is_running = False
        self.stop_requested = False

    def run(self):
        """
        Runs the study logic: reads, waits, and repeats until the data is exhausted or stopped.
        """
        if not self.study_data:
            print("❌ No data available to start the Read & Repeat session.")
            return

        self.is_running = True
        self.stop_requested = False
        print(f"✨ Starting '{self.name}' session. Delay: {self.repeat_delay} seconds.")

        for i, chunk in enumerate(self.study_data):
            if self.stop_requested:
                print("Session stopped by user request.")
                break

            print(f"--- Chunk {i+1}/{len(self.study_data)} ---")
            
            # 1. Read the text chunk
            self.tts_engine.speak(chunk)
            
            # Check stop request immediately after speaking
            if self.stop_requested:
                print("Session stopped by user request.")
                break

            # 2. Wait for the user to repeat the chunk
            print(f"👂 Waiting {self.repeat_delay} seconds for user repetition...")
            time.sleep(self.repeat_delay)
            
        self.is_running = False
        if not self.stop_requested:
             print(f"✅ '{self.name}' session completed.")

    def stop(self):
        """
        Signals the session to stop and stops the TTS engine.
        """
        self.stop_requested = True
        # Ensure the TTS engine stops immediately if it's currently speaking
        self.tts_engine.stop_speaking()
        
        # Wait for the blocking run() loop to check the flag and exit
        # In a real async environment, we'd use threading/asyncio primitives here.
        # For this pyttsx3 demo, the loop check in run() handles the graceful exit.
        print("🛑 Stop signal sent to Read & Repeat method.")

