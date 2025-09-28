import pyttsx3
import time
from typing import Any

class TtsEngine:
    """
    Implementation of the Text-to-Speech engine using pyttsx3 for local,
    free, and offline demonstration purposes.

    NOTE: pyttsx3 is a BLOCKING library (uses runAndWait()), which is acceptable
    for this demo but would typically be replaced by a non-blocking cloud API
    (like Gemini TTS) in a production web environment.
    """
    def __init__(self):
        try:
            # Initialize the TTS engine client
            self.engine: Any = pyttsx3.init()
            
            # Optional: Set a faster rate for a better study flow
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', rate + 50) # Increase rate slightly
            
            # Attempt to set a Spanish voice
            self.set_spanish_voice()
            
            self.is_speaking = False
            print("✅ TTS Engine (pyttsx3) initialized successfully.")
        except Exception as e:
            self.engine = None
            print(f"❌ Could not initialize pyttsx3 engine. Running in Silent Mode. Error: {e}")

    def set_spanish_voice(self):
        """Attempts to find and set a Spanish voice."""
        if not self.engine:
            return
            
        voices = self.engine.getProperty('voices')
        # Simple search for a voice supporting Spanish ('es')
        spanish_voices = [
            voice for voice in voices 
            if voice.languages and 'es' in [lang.lower() for lang in voice.languages]
        ]
        
        if spanish_voices:
            # Set the first Spanish voice found
            self.engine.setProperty('voice', spanish_voices[0].id)
            print(f"🔊 Using Spanish voice: {spanish_voices[0].name}")
        else:
            print("⚠️ No Spanish voice found. Using default system voice.")


    def speak(self, text: str):
        """
        Speaks the provided text. This function is BLOCKING 
        due to the nature of pyttsx3's runAndWait().
        """
        if not self.engine:
            # Fallback for silent mode (if pyttsx3 failed to initialize)
            print(f"[Silent Mode] 🗣️ Simulating speech: '{text}'")
            time.sleep(1) # Simulate the time it would take to speak
            return

        self.is_speaking = True
        print(f"[pyttsx3] 🗣️ Speaking: '{text}'")
        
        # Non-blocking call to queue the text
        self.engine.say(text)
        
        # Blocking call to process and play the audio (waits here)
        self.engine.runAndWait() 
        
        self.is_speaking = False

    def stop_speaking(self):
        """
        Stops the current speech process immediately.
        """
        if self.engine:
            # pyttsx3's stop() interrupts the runAndWait() loop
            self.engine.stop()
            self.is_speaking = False
            print("[TTS] 🛑 Speaking stopped manually.")
        else:
            print("[TTS] 🛑 Nothing to stop in Silent Mode.")

    def wait_for_completion(self):
        """
        Since pyttsx3 uses runAndWait() inside speak(), this method is 
        mostly a placeholder for API compatibility.
        """
        # We rely on 'speak' being blocking, so no action is typically needed here.
        pass 
