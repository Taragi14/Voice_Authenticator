import os
import numpy as np
import librosa
import speech_recognition as sr
import cv2
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import soundfile as sf
from fuzzywuzzy import fuzz
from cryptography.fernet import Fernet
from datetime import datetime
import logging
from PIL import Image, ImageTk
from tkinter import messagebox
from database import save_user_data, get_user_data

# Setup logging
logging.basicConfig(filename="auth.log", level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class AuthHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.intruder_photo = None
        self.status_text = None

    def log_status(self, message, status_text):
        """Update status text area with a new message."""
        if status_text and status_text.winfo_exists():
            status_text.text.configure(state='normal')
            status_text.text.insert("end", f"{datetime.now().strftime('%H:%M:%S')}: {message}\n")
            status_text.text.see("end")
            status_text.text.configure(state='disabled')
            status_text.update()
        logging.info(message)

    def save_encrypted_phrase(self, phrase):
        """Encrypt and return the phrase and key."""
        try:
            key = Fernet.generate_key()
            cipher = Fernet(key)
            encrypted = cipher.encrypt(phrase.encode())
            return encrypted, key
        except Exception as e:
            self.log_status(f"Error encrypting phrase: {e}", self.status_text)
            return None, None

    def load_encrypted_phrase(self, key_data, phrase_data):
        """Decrypt phrase using provided key."""
        try:
            cipher = Fernet(key_data)
            return cipher.decrypt(phrase_data).decode().strip().lower()
        except Exception as e:
            self.log_status(f"Error decrypting phrase: {e}", self.status_text)
            return None

    def extract_features(self, audio_data):
        """Extract and normalize MFCC features from audio data."""
        temp_file = None
        try:
            if isinstance(audio_data, bytes):
                temp_file = 'temp_audio.wav'
                with open(temp_file, 'wb') as f:
                    f.write(audio_data)
                audio_path = temp_file
            else:
                audio_path = audio_data

            y, sr = sf.read(audio_path)
            if len(y) == 0:
                self.log_status("Error: Audio data is empty.", self.status_text)
                return None

            if sr != 22050:
                y = librosa.resample(y, orig_sr=sr, target_sr=22050)
                sr = 22050

            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            if mfccs.size == 0:
                self.log_status("Error: MFCC extraction resulted in empty features.", self.status_text)
                return None

            mfccs = mfccs.T
            mfccs_min = np.min(mfccs, axis=0)
            mfccs_max = np.max(mfccs, axis=0)
            mfccs = (mfccs - mfccs_min) / (mfccs_max - mfccs_min + 1e-8)
            return mfccs
        except Exception as e:
            self.log_status(f"Error extracting features: {str(e)}", self.status_text)
            return None
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    self.log_status(f"Error cleaning up temp file: {e}", self.status_text)

    def save_voice(self, audio_data):
        """Save voice features as binary data."""
        feats = self.extract_features(audio_data)
        if feats is None:
            return None
        temp_file = 'temp.wav'
        try:
            y_inv = librosa.feature.inverse.mfcc_to_audio(feats.T, n_mels=13, sr=22050)
            sf.write(temp_file, y_inv, 22050)
            with open(temp_file, 'rb') as f:
                voice_data = f.read()
            return voice_data
        except Exception as e:
            self.log_status(f"Error saving voice: {e}", self.status_text)
            return None
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    self.log_status(f"Error cleaning up temp file: {e}", self.status_text)

    def save_average_voice(self, audio1, audio2):
        """Average MFCC features from two audio data for signup."""
        feats1 = self.extract_features(audio1)
        feats2 = self.extract_features(audio2)
        if feats1 is None or feats2 is None:
            return None
        max_len = max(len(feats1), len(feats2))
        feats1 = np.pad(feats1, ((0, max_len - len(feats1)), (0, 0)), mode='mean')
        feats2 = np.pad(feats2, ((0, max_len - len(feats2)), (0, 0)), mode='mean')
        avg_feats = (feats1 + feats2) / 2
        temp_file = 'temp.wav'
        try:
            y_inv = librosa.feature.inverse.mfcc_to_audio(avg_feats.T, n_mels=13, sr=22050)
            sf.write(temp_file, y_inv, 22050)
            with open(temp_file, 'rb') as f:
                voice_data = f.read()
            return voice_data
        except Exception as e:
            self.log_status(f"Error saving averaged voice: {e}", self.status_text)
            return None
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    self.log_status(f"Error cleaning up temp file: {e}", self.status_text)

    def record_audio(self, prompt, return_data=True):
        """Record audio and return as binary data or AudioData object."""
        self.log_status(prompt, self.status_text)
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                if return_data:
                    wav_data = audio.get_wav_data(convert_rate=22050)
                    if len(wav_data) == 0:
                        self.log_status("Error: Recorded audio is empty.", self.status_text)
                        return None
                    return wav_data
                return audio
            except sr.WaitTimeoutError:
                self.log_status("No audio detected. Try again.", self.status_text)
                return None
            except Exception as e:
                self.log_status(f"Error recording audio: {e}", self.status_text)
                return None

    def capture_intruder(self, image_label):
        """Capture intruder photo using webcam."""
        self.log_status("Capturing intruder photo...", self.status_text)
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            self.log_status("Camera not available.", self.status_text)
            return
        try:
            for _ in range(10):
                cam.read()
                time.sleep(0.1)
            ret, frame = cam.read()
            if ret:
                os.makedirs("static", exist_ok=True)
                cv2.imwrite("static/intruder.jpg", frame)
                self.log_status("Intruder photo saved.", self.status_text)
                img = Image.open("static/intruder.jpg")
                img = img.resize((200, 150), Image.Resampling.LANCZOS)
                self.intruder_photo = ImageTk.PhotoImage(img)
                if image_label and image_label.winfo_exists():
                    image_label.config(image=self.intruder_photo, text="")
            else:
                self.log_status("Failed to capture image.", self.status_text)
        except Exception as e:
            self.log_status(f"Error capturing intruder photo: {e}", self.status_text)
        finally:
            cam.release()

    def match_voice(self, stored_voice_data):
        """Compare recorded voice with stored sample."""
        if not stored_voice_data:
            self.log_status("No authorized voice sample found for this email.", self.status_text)
            return False

        audio_data = self.record_audio("Recording voice for authentication...", return_data=True)
        if not audio_data:
            return False

        temp_stored = None
        temp_test = None
        try:
            temp_stored = "temp_stored.wav"
            temp_test = "temp_test.wav"
            with open(temp_stored, 'wb') as f:
                f.write(stored_voice_data)
            with open(temp_test, 'wb') as f:
                f.write(audio_data)

            auth_features = self.extract_features(temp_stored)
            test_features = self.extract_features(temp_test)

            if auth_features is None or test_features is None:
                return False

            distance, _ = fastdtw(auth_features, test_features, dist=euclidean)
            self.log_status(f"Voice Match Score: {distance:.2f}", self.status_text)
            if distance >= 500:
                self.log_status("Voice mismatch. Try speaking clearly, closer to the microphone.", self.status_text)
                return False
            return True
        except Exception as e:
            self.log_status(f"Error matching voice: {e}", self.status_text)
            return False
        finally:
            for temp_file in [temp_stored, temp_test]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        self.log_status(f"Error cleaning up temp file: {e}", self.status_text)

    def verify_phrase(self, key_data, phrase_data):
        """Verify spoken phrase against stored phrase."""
        audio = self.record_audio("Speak your unlock phrase...", return_data=False)
        if not audio:
            return False

        try:
            spoken_phrase = self.recognizer.recognize_google(audio).strip().lower()
            stored_phrase = self.load_encrypted_phrase(key_data, phrase_data)
            if stored_phrase is None:
                return False
            similarity = fuzz.ratio(spoken_phrase, stored_phrase)
            self.log_status(f"Phrase Similarity: {similarity}%", self.status_text)
            return similarity > 90
        except Exception as e:
            self.log_status(f"Error recognizing phrase: {e}", self.status_text)
            return False

    def run_signup(self, email, status_text, progress_bar, window, image_label):
        """Perform signup process with two voice samples and a secret phrase."""
        self.status_text = status_text
        self.log_status(f"Starting signup process for {email}...", status_text)
        try:
            progress_bar.pack(pady=10)
            progress_bar["value"] = 0
            window.update()

            audio1 = self.record_audio("Recording first voice sample... Speak any sentence.")
            if not audio1:
                messagebox.showerror("Error", "Voice recording failed. Please try again.", parent=window)
                self.log_status("Signup failed due to voice recording error.", status_text)
                return False
            progress_bar["value"] = 25
            window.update()

            audio2 = self.record_audio("Recording second voice sample... Speak another sentence.")
            if not audio2:
                messagebox.showerror("Error", "Voice recording failed. Please try again.", parent=window)
                self.log_status("Signup failed due to voice recording error.", status_text)
                return False
            progress_bar["value"] = 50
            window.update()

            voice_data = self.save_average_voice(audio1, audio2)
            if not voice_data:
                messagebox.showerror("Error", "Voice processing failed. Please try again.", parent=window)
                self.log_status("Signup failed due to voice processing error.", status_text)
                return False
            progress_bar["value"] = 75
            window.update()

            audio = self.record_audio("Speak your secret unlock phrase (e.g., 'Open my phone')...", return_data=False)
            if not audio:
                messagebox.showerror("Error", "Phrase recording failed. Please try again.", parent=window)
                self.log_status("Signup failed due to phrase recording error.", status_text)
                return False

            try:
                phrase = self.recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                messagebox.showerror("Error", "Could not understand the phrase. Please try again.", parent=window)
                self.log_status("Signup failed due to unrecognizable phrase.", status_text)
                return False
            except sr.RequestError as e:
                messagebox.showerror("Error", "Speech recognition service error. Please check your internet connection.", parent=window)
                self.log_status(f"Signup failed due to speech recognition error: {e}", status_text)
                return False

            phrase_data, key_data = self.save_encrypted_phrase(phrase)
            if not phrase_data or not key_data:
                messagebox.showerror("Error", "Encryption failed. Please try again.", parent=window)
                self.log_status("Signup failed due to encryption error.", status_text)
                return False

            save_user_data(email, voice_data, phrase_data, key_data)
            progress_bar["value"] = 100
            window.update()
            time.sleep(0.5)
            self.log_status("Signup completed successfully!", status_text)
            messagebox.showinfo("Success", "Signup completed successfully!", parent=window)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Signup failed: {str(e)}", parent=window)
            self.log_status(f"Signup failed: {str(e)}", status_text)
            return False
        finally:
            progress_bar.pack_forget()
            window.destroy()
            window.master.deiconify()

    def run_login(self, email, status_text, progress_bar, window, image_label):
        """Perform login with one voice sample and secret phrase."""
        self.status_text = status_text
        self.log_status(f"Starting login for {email}...", status_text)
        try:
            user_data = get_user_data(email)
            if not user_data:
                messagebox.showerror("Error", "No user data found. Please sign up first.", parent=window)
                self.log_status("No user data found for this email.", status_text)
                return False

            voice_data, phrase_data, key_data = user_data
            max_attempts = 3
            for attempt in range(max_attempts):
                self.log_status(f"Attempt {attempt + 1}/{max_attempts}", status_text)
                progress_bar.pack(pady=10)
                progress_bar["value"] = 0
                window.update()

                audio_data = self.record_audio("Recording voice sample for login...")
                if not audio_data:
                    messagebox.showerror("Error", "Voice recording failed. Please try again.", parent=window)
                    self.log_status("Login failed due to voice recording error.", status_text)
                    progress_bar.pack_forget()
                    continue

                progress_bar["value"] = 50
                window.update()

                voice_ok = self.match_voice(voice_data)
                if not voice_ok:
                    self.log_status("Voice authentication failed.", status_text)
                    progress_bar.pack_forget()
                    continue

                progress_bar["value"] = 75
                window.update()

                phrase_ok = self.verify_phrase(key_data, phrase_data)
                if not phrase_ok:
                    self.log_status("Phrase authentication failed.", status_text)
                    progress_bar.pack_forget()
                    continue

                progress_bar["value"] = 100
                window.update()
                time.sleep(0.5)
                self.log_status("Access Granted! Opening success page...", status_text)
                logging.info(f"Authentication successful for {email} at {datetime.now()}")
                try:
                    import webbrowser
                    webbrowser.open("http://127.0.0.1:5000/success")
                except Exception as e:
                    messagebox.showwarning("Warning", "Authentication succeeded, but failed to open success page.", parent=window)
                    self.log_status(f"Error opening success page: {e}", status_text)
                return True
            self.log_status("Max attempts reached. Capturing intruder photo...", status_text)
            self.capture_intruder(image_label)
            logging.info(f"Authentication failed for {email} at {datetime.now()}")
            messagebox.showwarning("Failed", "Login failed. Intruder photo captured.", parent=window)
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}", parent=window)
            self.log_status(f"Login failed: {str(e)}", status_text)
            return False
        finally:
            progress_bar.pack_forget()
            window.destroy()
            window.master.deiconify()