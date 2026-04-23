import random
import asyncio
import edge_tts
import os
import threading
import tempfile
from dotenv import dotenv_values
# IMPORTANT: Do NOT do `from AssistantState import is_speaking` — that copies
# the bool at import time and will never reflect updates from other modules.
import AssistantState

# ── Load env variables ────────────────────────────────────────────────────────
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")

# ── pygame mixer — initialized ONCE at module level, never re-init'd ──────────
# This eliminates the ~2-3s pygame.mixer.init() cost that was happening every
# single TTS call in the original code.
import pygame
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.mixer.init()
print("[TTS] pygame mixer initialized.")

# ── Temp file — reused across calls (no repeated create/delete overhead) ───────
# We write to a fixed temp path and reload it each call.
_SPEECH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data", "speech.mp3")
os.makedirs(os.path.dirname(_SPEECH_FILE), exist_ok=True)

# ── Event loop — one persistent loop for all async TTS calls ─────────────────
# asyncio.run() creates AND destroys a full event loop every call — expensive.
# Instead we keep one loop alive on a background thread.
_loop = asyncio.new_event_loop()

def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

_loop_thread = threading.Thread(target=_start_loop, args=(_loop,), daemon=True)
_loop_thread.start()


# ── Audio generation ──────────────────────────────────────────────────────────
async def _generate_audio(text: str, file_path: str) -> None:
    """Generate speech audio file using edge_tts (runs on the async loop thread)."""
    # NOTE: pygame.mixer.music.unload() is called BEFORE this function
    # from the calling thread (TTS). pygame is NOT thread-safe, so all
    # pygame calls must happen on the same thread that initialized it.
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch="+1Hz", rate="+5%")
    await communicate.save(file_path)


def _run_async(coro):
    """Submit a coroutine to the persistent event loop and block until done."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()  # Blocks current thread until coroutine completes


def _ensure_mixer():
    """Re-initialize pygame mixer if it was somehow de-initialized."""
    try:
        pygame.mixer.get_init()
    except pygame.error:
        pass

    if not pygame.mixer.get_init():
        print("[TTS] Re-initializing pygame mixer...")
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.mixer.init()


# ── Core TTS function ─────────────────────────────────────────────────────────
_MAX_RETRIES = 3

def TTS(Text, func=lambda r=None: True):
    """
    Convert text to speech and play it.

    func : optional external callable used to signal early stop.
            Return False from func() to interrupt playback mid-sentence.

    Anti-feedback-loop:
      - Calls AssistantState.pause_listening() BEFORE playing → physically
        stops the microphone stream so zero audio is captured during playback.
      - Calls AssistantState.resume_listening() AFTER playback → restarts
        the mic with a clean slate and a small delay.
    """
    # Replace all-caps ORA with Ora so TTS pronounces it as a word, not an acronym
    Text = Text.replace("ORA", "Ora")

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            # ── 1. PAUSE MIC — physically stop the microphone stream ─────
            AssistantState.pause_listening()

            # ── 2. Ensure mixer is alive (recovery from previous crash) ──
            _ensure_mixer()

            # ── 3. Unload previous audio ON THIS THREAD (pygame not thread-safe)
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass  # No file was loaded yet — that's fine

            # ── 4. Generate audio via the persistent event loop ──────────
            _run_async(_generate_audio(Text, _SPEECH_FILE))

            # ── 5. Load and play ─────────────────────────────────────────
            pygame.mixer.music.load(_SPEECH_FILE)
            pygame.mixer.music.play()

            # ── 6. Wait for playback to finish ───────────────────────────
            clock = pygame.time.Clock()
            while pygame.mixer.music.get_busy():
                if func() is False:
                    break
                clock.tick(10)  # 10 ticks/s — avoids busy-waiting

            return True

        except Exception as e:
            print(f"[TTS] Error (attempt {attempt}/{_MAX_RETRIES}): {e}")
            if attempt < _MAX_RETRIES:
                # Try to recover the mixer for next attempt
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
                try:
                    pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
                    pygame.mixer.init()
                    print("[TTS] Mixer recovered.")
                except Exception as re:
                    print(f"[TTS] Mixer recovery failed: {re}")

        finally:
            try:
                func(False)                      # Signal end of TTS to caller
            except Exception:
                pass
            try:
                pygame.mixer.music.stop()        # Stop playback cleanly
            except Exception:
                pass

            # ── RESUME MIC — restart the microphone stream ───────────────
            AssistantState.resume_listening()

    print(f"[TTS] Failed after {_MAX_RETRIES} attempts. Skipping.")
    return False


# ── Long-text handler ─────────────────────────────────────────────────────────

# Pre-defined responses for when the text is too long to read aloud fully
_OVERFLOW_RESPONSES = [
    "The rest of the result has been printed to the chat screen, kindly check it out sir.",
    "The rest of the text is now on the chat screen, sir, please check it.",
    "You can see the rest of the text on the chat screen, sir.",
    "The remaining part of the text is now on the chat screen, sir.",
    "Sir, you'll find more text on the chat screen for you to see.",
    "The rest of the answer is now on the chat screen, sir.",
    "Sir, please look at the chat screen, the rest of the answer is there.",
    "You'll find the complete answer on the chat screen, sir.",
    "The next part of the text is on the chat screen, sir.",
    "Sir, please check the chat screen for more information.",
    "There's more text on the chat screen for you, sir.",
    "Sir, take a look at the chat screen for additional text.",
    "You'll find more to read on the chat screen, sir.",
    "Sir, check the chat screen for the rest of the text.",
    "The chat screen has the rest of the text, sir.",
    "There's more to see on the chat screen, sir, please look.",
    "Sir, the chat screen holds the continuation of the text.",
    "You'll find the complete answer on the chat screen, kindly check it out sir.",
    "Please review the chat screen for the rest of the text, sir.",
    "Sir, look at the chat screen for the complete answer.",
]


def TextToSpeech(Text, func=lambda r=None: True):
    """
    Public-facing TTS entry point.

    Handles long text by reading only the first 2 sentences aloud and
    appending a message directing the user to the chat screen for the rest.
    Short text is read in full.
    """
    sentences = str(Text).split(".")

    if len(sentences) > 4 and len(Text) >= 250:
        # Read first 2 sentences + an overflow notice
        short_text = ". ".join(s.strip() for s in sentences[:2] if s.strip())
        TTS(short_text + ". " + random.choice(_OVERFLOW_RESPONSES), func)
    else:
        TTS(Text, func)


# ── Cleanup ───────────────────────────────────────────────────────────────────
def shutdown():
    """Call this on application exit to cleanly stop the event loop and mixer."""
    pygame.mixer.quit()
    _loop.call_soon_threadsafe(_loop.stop)


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        while True:
            TextToSpeech(input("Enter the text: "))
    except KeyboardInterrupt:
        shutdown()