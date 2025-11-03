"""
Voice Handler Module
Handles speech-to-text (STT) and text-to-speech (TTS) functionality.
Uses ONLY FREE resources - no API keys required.
Supports multilingual input with automatic transcription to English.
"""
import os
import tempfile
import base64
from typing import Optional, Tuple
import io

# Try to import required libraries (all FREE, no API keys needed)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: speech_recognition not installed. Install with: pip install SpeechRecognition")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Warning: gTTS not installed. Install with: pip install gtts")

# Try to import translation library (free)
try:
    from googletrans import Translator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: googletrans not installed. Install with: pip install googletrans==4.0.0rc1")

# Note: Removed Whisper as it's heavy and not necessary - using free Google Speech Recognition instead


class VoiceHandler:
    """Handles voice input and output operations using FREE tools only."""
    
    def __init__(self):
        self.recognizer = None
        self.translator = None
        self._init_recognizer()
        self._init_translator()
    
    def _init_recognizer(self):
        """Initialize speech recognition using Google's free service."""
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            # Adjust for better recognition
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
    
    def _init_translator(self):
        """Initialize translator for Hindi to English translation."""
        if TRANSLATION_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception as e:
                print(f"Translator initialization warning: {e}")
                self.translator = None
    
    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Tuple[Optional[str], Optional[str]]:
        """
        Translate text from source language to target language (FREE).
        
        Args:
            text: Text to translate
            source_lang: Source language code (or "auto" for auto-detect)
            target_lang: Target language code (default: "en" for English)
        
        Returns:
            Tuple of (translated_text, detected_source_language)
        """
        if not TRANSLATION_AVAILABLE or not self.translator:
            # If translation not available, return original text
            return text, source_lang if source_lang != "auto" else "en"
        
        try:
            if source_lang == "auto":
                result = self.translator.translate(text, dest=target_lang)
            else:
                result = self.translator.translate(text, src=source_lang, dest=target_lang)
            
            translated_text = result.text
            detected_lang = result.src.lower() if hasattr(result, 'src') else source_lang
            
            return translated_text, detected_lang
        except Exception as e:
            print(f"Translation error: {e}")
            # Return original text if translation fails
            return text, source_lang if source_lang != "auto" else "en"
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "auto") -> Tuple[Optional[str], Optional[str]]:
        """
        Transcribe audio file to text using FREE Google Speech Recognition.
        No API key required - completely free service.
        
        Args:
            audio_file_path: Path to audio file (WAV format)
            language: Source language code (e.g., "hi-IN" for Hindi, "en-US" for English)
                     Use "auto" for auto-detection (may not work, so specify if known)
        
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        if not os.path.exists(audio_file_path):
            print(f"Audio file not found: {audio_file_path}")
            return None, None
        
        # Use Google Speech Recognition (FREE, no API key needed)
        if SPEECH_RECOGNITION_AVAILABLE and self.recognizer:
            try:
                # Load audio file
                with sr.AudioFile(audio_file_path) as source:
                    # Adjust for ambient noise (helps with recognition)
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    # Record the audio
                    audio = self.recognizer.record(source)
                
                # Try Hindi and English specifically (as user requested)
                languages_to_try = []
                
                if language == "auto":
                    # Try Hindi first, then English (as user primarily uses these)
                    languages_to_try = [
                        "hi-IN",  # Hindi (India) - primary
                        "en-IN",  # English (India)
                        "en-US",  # English (US)
                        "hi",     # Hindi (generic)
                        "en",     # English (generic)
                    ]
                else:
                    languages_to_try = [language]
                
                # Try each language
                transcribed_text = None
                detected_lang = None
                
                for lang in languages_to_try:
                    try:
                        text = self.recognizer.recognize_google(audio, language=lang)
                        if text and text.strip():
                            transcribed_text = text.strip()
                            # Detect language based on what worked
                            detected_lang = lang.split("-")[0] if "-" in lang else lang
                            break  # Success, exit loop
                    except sr.UnknownValueError:
                        # Try next language
                        continue
                    except sr.RequestError as e:
                        print(f"Google Speech Recognition error: {e}")
                        # If it's a network error, try the next language
                        continue
                
                if transcribed_text:
                    return transcribed_text, detected_lang
                
                # If all languages failed, try once more with no language specified
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text and text.strip():
                        return text.strip(), "en"  # Assume English if auto-detect works
                except:
                    pass
                
                # If all languages failed
                return None, None
                
            except sr.WaitTimeoutError:
                print("Audio file appears to be empty or too short")
                return None, None
            except Exception as e:
                print(f"Speech recognition error: {e}")
                import traceback
                traceback.print_exc()
                return None, None
        
        print("Speech recognition not available. Install: pip install SpeechRecognition")
        return None, None
    
    def transcribe_audio_bytes(self, audio_bytes: bytes, sample_rate: int = 16000, language: str = "auto") -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Transcribe audio bytes to text using FREE Google Speech Recognition.
        Supports Hindi and English. Translates Hindi to English automatically.
        
        Args:
            audio_bytes: Audio data as bytes (WAV format from audio_recorder_streamlit)
            sample_rate: Sample rate of audio
            language: Language code or "auto" for auto-detection
        
        Returns:
            Tuple of (transcribed_text_in_source_lang, translated_text_in_english, detected_language)
            If translation not needed (already English), both texts will be the same.
        """
        # Convert audio bytes to proper WAV format if needed
        # audio_recorder_streamlit typically returns WAV, but let's ensure it's valid
        if len(audio_bytes) < 44:  # WAV header is at least 44 bytes
            print("Audio data too short, may be invalid")
            return None, None
        
        # Save to temporary file (required by speech_recognition library)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            # Close file before processing (Windows requirement)
            if tmp_path and os.path.exists(tmp_path):
                # Verify file is not empty
                if os.path.getsize(tmp_path) == 0:
                    print("Audio file is empty")
                    return None, None, None
                
                # Transcribe using the file
                transcribed_text, detected_lang = self.transcribe_audio_file(tmp_path, language=language)
                
                if not transcribed_text:
                    return None, None, None
                
                # Translate to English if detected language is Hindi
                english_text = transcribed_text
                if detected_lang and detected_lang.lower() in ["hi", "hindi"]:
                    # Translate Hindi to English
                    english_text, _ = self.translate_text(transcribed_text, source_lang="hi", target_lang="en")
                
                # Return: (original_text, english_text, detected_language)
                return transcribed_text, english_text, detected_lang
            else:
                return None, None, None
        except Exception as e:
            print(f"Error processing audio bytes: {e}")
            import traceback
            traceback.print_exc()
            return None, None
        finally:
            # Clean up temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    print(f"Warning: Could not delete temp file: {e}")
    
    def text_to_speech(self, text: str, language: str = "en", output_file: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech audio. Supports both Hindi and English.
        
        Args:
            text: Text to convert
            language: Language code - "en" for English, "hi" for Hindi (default: "en")
            output_file: Optional path to save audio file
        
        Returns:
            Audio data as bytes (if output_file not provided)
        """
        if not GTTS_AVAILABLE:
            return None
        
        try:
            # Remove markdown formatting for cleaner speech
            clean_text = text.replace("**", "").replace("*", "").replace("#", "").replace("---", "")
            
            # Map language codes for gTTS
            lang_code = "hi" if language.lower() in ["hi", "hindi"] else "en"
            
            tts = gTTS(text=clean_text, lang=lang_code, slow=False)
            
            if output_file:
                tts.save(output_file)
                with open(output_file, "rb") as f:
                    return f.read()
            else:
                # Save to temporary file and return bytes
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tts.save(tmp_file.name)
                    with open(tmp_file.name, "rb") as f:
                        audio_bytes = f.read()
                    os.remove(tmp_file.name)
                    return audio_bytes
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def text_to_speech_base64(self, text: str, language: str = "en") -> Optional[str]:
        """
        Convert text to speech and return as base64 encoded string for web playback.
        
        Args:
            text: Text to convert
            language: Language code
        
        Returns:
            Base64 encoded audio string
        """
        audio_bytes = self.text_to_speech(text, language)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None


# Global instance
voice_handler = VoiceHandler()

