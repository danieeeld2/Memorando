import time
from abc import ABC, abstractmethod 

class StudyMethod(ABC):
    """
    Abstract Base Class for all memorization methods.

    Defines the contract: any method must be initializable with a TTS engine
     and study data, and must have a 'run' method that implements the study logic.
    """
    def __init__(self, tts_engine, study_data):
        self.tts_engine = tts_engine
        self.study_data = study_data
        # For now, we are going to implement it in Spanish
        self.name = "Método Base" 

    @abstractmethod
    def run(self):
        """
        Main method containing the study logic.
        Must be implemented by all classes inheriting from StudyMethod.
        """
        pass

    def stop(self):
        """
        Allows the study session to be stopped if necessary.
        Currently only stops the TTS engine.
        """
        if self.tts_engine:
            self.tts_engine.stop_speaking()
