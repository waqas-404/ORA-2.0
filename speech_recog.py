import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

# -------------------------------
# Load Model
# -------------------------------
model = Model("model/vosk-model-en-in-0.5")

# Sample rate (important)
samplerate = 16000

# Recognizer
recognizer = KaldiRecognizer(model, samplerate)

# Queue to store audio
q = queue.Queue()

# -------------------------------
# Audio Callback
# -------------------------------
def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# -------------------------------
# Start Microphone Stream
# -------------------------------
with sd.RawInputStream(
    samplerate=samplerate,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
):
    print("🎤 Listening... (say 'hey ora' to activate)")

    activated = False

    while True:
        data = q.get()

        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()

            if text:
                print("Heard:", text)

                # -------------------------------
                # Wake Word Logic (Simulated)
                # -------------------------------
                if "hey ora" in text and not activated:
                    activated = True
                    print("✅ Assistant Activated! Listening for command...")

                elif activated:
                    print("🧠 Command:", text)
                    
                    # Example commands
                    if "time" in text:
                        print("⏰ It's assistant time 😄")
                    elif "hello" in text:
                        print("👋 Hello! How can I help?")
                    
                    # Reset after command
                    activated = False
                    print("🔄 Back to passive listening...")