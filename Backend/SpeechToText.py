
# import speech_recognition as sr
# import mtranslate as mt
# import os
# import time
# from dotenv import dotenv_values

# # ── Load env variables ────────────────────────────────────────────────────────
# env_vars = dotenv_values(".env")
# InputLanguage = (env_vars.get("InputLanguage") or "en-US").strip()

# # ── Path setup ────────────────────────────────────────────────────────────────
# current_dir = os.getcwd()
# TempDirPath = os.path.join(current_dir, "Frontend", "Files")
# os.makedirs(TempDirPath, exist_ok=True)

# STATUS_FILE = os.path.join(TempDirPath, "Status.data")

# def SetAssistantStatus(Status: str):
#     """Write assistant status to a file for the frontend to read."""
#     try:
#         with open(STATUS_FILE, "w", encoding="utf-8") as file:
#             file.write(Status)
#     except Exception:
#         # If frontend file path isn't available for some reason, don't crash STT.
#         pass


# def QueryModifier(Query: str) -> str:
#     """Ensure proper punctuation and formatting on the recognized query."""
#     new_query = (Query or "").lower().strip()
#     if not new_query:
#         return ""

#     question_words = [
#         "how", "what", "who", "where", "why", "which", "whose", "whom",
#         "can you", "what's", "where's", "how's", "do you", "if"
#     ]

#     is_question = any(qw in new_query for qw in question_words)

#     last_char = new_query[-1]
#     if is_question:
#         if last_char not in ".?!":
#             new_query += "?"
#         else:
#             new_query = new_query[:-1] + "?"
#     else:
#         if last_char not in ".?!":
#             new_query += "."
#         else:
#             new_query = new_query[:-1] + "."

#     return new_query.capitalize()


# def UniversalTranslator(Text: str) -> str:
#     """Translate recognized text into English."""
#     if not Text:
#         return ""
#     return mt.translate(Text, "en", "auto").capitalize()


# # ── Recognizer (INIT ONCE) ────────────────────────────────────────────────────
# recognizer = sr.Recognizer()

# # These help reduce false triggers and missed speech
# recognizer.pause_threshold = 0.7           # silence before phrase ends
# recognizer.non_speaking_duration = 0.35    # amount of silence stored around phrase
# recognizer.phrase_threshold = 0.25         # minimum "speechy" audio to count as a phrase

# # Start with dynamic threshold to calibrate, then freeze (important fix)
# recognizer.dynamic_energy_threshold = True

# # ── Microphone (OPEN ONCE + CALIBRATE ONCE) ──────────────────────────────────
# _microphone = sr.Microphone()

# print("[STT] Calibrating microphone for ambient noise...")
# with _microphone as source:
#     # You can raise duration to 1.5–2.0 if your room noise fluctuates
#     recognizer.adjust_for_ambient_noise(source, duration=1.0)

# # Freeze threshold to prevent it drifting too low and causing false triggers
# recognizer.dynamic_energy_threshold = False

# # Add a margin so random noise doesn't trigger "speech started"
# ENERGY_MARGIN = 200
# recognizer.energy_threshold = float(recognizer.energy_threshold) + ENERGY_MARGIN

# print(f"[STT] Microphone ready. language={InputLanguage} energy_threshold={recognizer.energy_threshold:.0f}")

# # ── Helper to estimate audio duration (used to ignore noise blips) ────────────
# def _audio_duration_seconds(audio: sr.AudioData) -> float:
#     try:
#         # frame_data length = sample_rate * sample_width * seconds
#         return len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
#     except Exception:
#         return 0.0


# # ── Core STT function ─────────────────────────────────────────────────────────
# def SpeechRecognition() -> str:
#     """
#     Captures audio from the microphone and returns the recognized + formatted text.

#     Fixes included:
#       - Prevent false "Recognizing..." when user didn't speak (noise blips)
#       - Freeze energy threshold after calibration to avoid drift
#       - Reject very short audio captures before calling Google
#       - Reset status back to Listening on non-results/errors
#     """
#     # 1) LISTEN
#     with _microphone as source:
#         SetAssistantStatus("Listening...")
#         try:
#             # timeout: seconds to wait for speech to START
#             # phrase_time_limit: max duration of an utterance
#             audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
#         except sr.WaitTimeoutError:
#             # No speech started within timeout; keep listening in caller loop
#             SetAssistantStatus("Listening...")
#             return ""

#     # 2) FILTER OUT NOISE BLIPS (CRITICAL FIX)
#     dur = _audio_duration_seconds(audio)
#     # If you still see false triggers, raise this to 0.5
#     MIN_UTTERANCE_SEC = 0.35
#     if dur < MIN_UTTERANCE_SEC:
#         SetAssistantStatus("Listening...")
#         return ""

#     # 3) RECOGNIZE
#     try:
#         SetAssistantStatus("Recognizing...")
#         text = recognizer.recognize_google(audio, language=InputLanguage)

#         if not text or not text.strip():
#             SetAssistantStatus("Listening...")
#             return ""

#         # 4) TRANSLATE IF NEEDED + FORMAT
#         if "en" in InputLanguage.lower():
#             return QueryModifier(text)
#         else:
#             SetAssistantStatus("Translating...")
#             translated = UniversalTranslator(text)
#             SetAssistantStatus("Listening...")
#             return QueryModifier(translated)

#     except sr.UnknownValueError:
#         # Google couldn't understand (often silence/noise)
#         SetAssistantStatus("Listening...")
#         return ""
#     except sr.RequestError as e:
#         # Network/API failure
#         print(f"[STT] Google Speech API error: {e}")
#         SetAssistantStatus("Speech API Error")
#         # short cooldown so you don't spam requests if network is down
#         time.sleep(0.3)
#         SetAssistantStatus("Listening...")
#         return ""
#     except Exception as e:
#         print(f"[STT] Unexpected error: {e}")
#         SetAssistantStatus("Listening...")
#         return ""


# # ── Entrypoint ────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     print("[STT] Ready. Speak now...")
#     while True:
#         out = SpeechRecognition()
#         if out:
#             print(out)

import queue
import sounddevice as sd
import json
import os
import time
from vosk import Model, KaldiRecognizer
import mtranslate as mt
from dotenv import dotenv_values

# ── IMPORTANT: import only the MODULE, never do `from AssistantState import is_speaking`
import AssistantState


# ── Load env variables ────────────────────────────────────────────────────────
env_vars = dotenv_values(".env")
InputLanguage = (env_vars.get("InputLanguage") or "en-US").strip()

# ── Path setup ────────────────────────────────────────────────────────────────
current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

STATUS_FILE = os.path.join(TempDirPath, "Status.data")

def SetAssistantStatus(Status: str):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as file:
            file.write(Status)
    except Exception:
        pass

# ── Query Modifier ────────────────────────────────────────────────────────────
def QueryModifier(Query: str) -> str:
    new_query = (Query or "").lower().strip()
    if not new_query:
        return ""

    question_words = [
        "how", "what", "who", "where", "why", "which", "whose", "whom",
        "can you", "what's", "where's", "how's", "do you", "if"
    ]

    is_question = any(qw in new_query for qw in question_words)

    last_char = new_query[-1]
    if is_question:
        if last_char not in ".?!":
            new_query += "?"
        else:
            new_query = new_query[:-1] + "?"
    else:
        if last_char not in ".?!":
            new_query += "."
        else:
            new_query = new_query[:-1] + "."

    return new_query.capitalize()

# ── Translator ────────────────────────────────────────────────────────────────
def UniversalTranslator(Text: str) -> str:
    if not Text:
        return ""
    return mt.translate(Text, "en", "auto").capitalize()

# ── Load Vosk Model ───────────────────────────────────────────────────────────
MODEL_PATH = "model/vosk-model-en-in-0.5"
model = Model(MODEL_PATH)

samplerate = 16000
recognizer = KaldiRecognizer(model, samplerate)

# Queue for audio data
q = queue.Queue()

# ── Minimum utterance duration to reject noise blips ──────────────────────────
MIN_UTTERANCE_SEC = 0.35

# ── Audio Callback ────────────────────────────────────────────────────────────
def callback(indata, frames, time_info, status):
    """Called by sounddevice for every audio block. Pushes raw bytes into the queue."""
    if status:
        print(f"[STT] sounddevice status: {status}")
    q.put(bytes(indata))

# ── Mic stream — created once, stopped/started by TTS via AssistantState ──────
stream = sd.RawInputStream(
    samplerate=samplerate,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
)
stream.start()
print("[STT] Vosk model loaded. Listening...")


# ── Mic stream control — registered with AssistantState so TTS can call them ──
def _pause_mic():
    """Stop the mic stream entirely. Called by TTS before speaking."""
    try:
        if stream.active:
            stream.stop()
            # Drain the queue so stale audio is never processed
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
            # Reset Vosk recognizer state so partial results don't leak
            recognizer.Reset()
            # print("[STT] 🔇 Mic STOPPED (TTS speaking)")
    except Exception as e:
        print(f"[STT] Error stopping mic: {e}")


def _resume_mic():
    """Restart the mic stream. Called by TTS after speaking finishes."""
    try:
        if not stream.active:
            # Drain any residual data in the queue (shouldn't be any, but safety)
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
            recognizer.Reset()
            stream.start()
            # print("[STT] 🔊 Mic STARTED (TTS finished)")
    except Exception as e:
        print(f"[STT] Error starting mic: {e}")


# Register with AssistantState so TTS can control the mic without importing STT
AssistantState.register_stream_controls(_pause_mic, _resume_mic)


def _estimate_audio_duration_sec(data: bytes) -> float:
    """Estimate duration of raw PCM audio in seconds.
    Format: 16-bit mono (2 bytes per sample) at `samplerate` Hz."""
    sample_width = 2  # int16 = 2 bytes
    channels = 1
    return len(data) / (samplerate * sample_width * channels)


# ── Core STT Function ─────────────────────────────────────────────────────────
def SpeechRecognition() -> str:
    """
    Continuous listening using Vosk.
    Returns processed text when a valid phrase is detected.

    Anti-feedback-loop: The mic stream is physically STOPPED by TTS via
    AssistantState.pause_listening() before any audio plays, and RESTARTED
    via AssistantState.resume_listening() after playback ends. This is the
    same approach real voice assistants use — no audio reaches the recognizer
    while the assistant is speaking.
    """

    SetAssistantStatus("Listening...")

    # Accumulate raw bytes to estimate utterance duration
    accumulated_bytes = bytearray()

    while True:
        # ── Extra safety: if is_speaking is True, don't process ──────────
        # (The mic stream should already be stopped, but this is a fallback)
        if AssistantState.is_speaking:
            time.sleep(0.1)
            continue

        # ── Grab next audio block (with timeout so we can re-check state) ─
        try:
            data = q.get(timeout=0.4)
        except queue.Empty:
            continue

        # ── Double-check state (may have changed while we waited) ─────────
        if AssistantState.is_speaking:
            accumulated_bytes.clear()
            continue

        # ── Feed audio to Vosk recognizer ─────────────────────────────────
        accumulated_bytes.extend(data)

        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()

            # Reset accumulator for next utterance
            utterance_bytes = bytes(accumulated_bytes)
            accumulated_bytes.clear()

            # 🔴 Ignore empty / noise
            if not text:
                continue

            # 🔴 Reject very short utterances (noise blips)
            duration = _estimate_audio_duration_sec(utterance_bytes)
            if duration < MIN_UTTERANCE_SEC:
                print(f"[STT] Rejected short audio ({duration:.2f}s < {MIN_UTTERANCE_SEC}s)")
                continue

            # 🔴 Reject single-character garbage
            if len(text) < 2:
                continue

            print(f"[STT] Heard: {text}  ({duration:.2f}s)")

            try:
                SetAssistantStatus("Recognizing...")

                # ── Translation + Formatting ───────────────────────────
                if "en" in InputLanguage.lower():
                    final_text = QueryModifier(text)
                else:
                    SetAssistantStatus("Translating...")
                    translated = UniversalTranslator(text)
                    final_text = QueryModifier(translated)

                SetAssistantStatus("Listening...")
                return final_text

            except Exception as e:
                print(f"[STT] Processing error: {e}")
                SetAssistantStatus("Listening...")
                return ""

# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[STT] Ready. Speak now...")

    while True:
        result = SpeechRecognition()
        if result:
            print(result)