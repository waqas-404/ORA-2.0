"""
Shared assistant state — used by STT and TTS to coordinate mic/speaker.

This module acts as a mediator between STT and TTS so they don't need to
import each other (which would cause circular imports).

The KEY mechanism: TTS calls pause_listening() / resume_listening() to
physically stop/start the microphone stream. This is what real voice
assistants (Alexa, Siri, Google Home) do — they don't just "ignore" audio,
they turn off the mic entirely while the speaker is active.

IMPORTANT: Always access via `AssistantState.is_speaking`, NEVER do
`from AssistantState import is_speaking` — that copies the bool value
at import time and won't reflect later changes (Python gotcha).
"""

import threading
import time

# ── Global flag ──────────────────────────────────────────────────────────────
# True while TTS audio is playing. STT checks this as an extra safety net.
is_speaking: bool = False

# ── Mic stream control callbacks ─────────────────────────────────────────────
# STT registers its stream stop/start functions here at module load time.
# TTS calls pause_listening() / resume_listening() through this module,
# avoiding any circular import between STT and TTS.

_pause_callback = None
_resume_callback = None
_lock = threading.Lock()


def register_stream_controls(pause_fn, resume_fn):
    """Called by STT at import time to register mic stream stop/start."""
    global _pause_callback, _resume_callback
    with _lock:
        _pause_callback = pause_fn
        _resume_callback = resume_fn
    print("[AssistantState] Mic stream controls registered.")


def pause_listening():
    """Stop the microphone stream. Called by TTS before playing audio."""
    global is_speaking
    with _lock:
        is_speaking = True
        if _pause_callback:
            try:
                _pause_callback()
            except Exception as e:
                print(f"[AssistantState] Error pausing mic: {e}")


def resume_listening():
    """Restart the microphone stream. Called by TTS after audio finishes."""
    global is_speaking
    # Small delay to ensure speaker output has fully stopped before
    # re-opening the mic (prevents capturing the tail-end of TTS audio)
    time.sleep(0.3)
    with _lock:
        is_speaking = False
        if _resume_callback:
            try:
                _resume_callback()
            except Exception as e:
                print(f"[AssistantState] Error resuming mic: {e}")