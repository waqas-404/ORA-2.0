from groq import Groq
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "close", "play", "generate image",
    "system", "content", "google search", "youtube search", "reminder"
]

# ── No history cap — full history sent every call as requested ────────────────
_dynamic_history = []

_SYSTEM_PROMPT = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation.

*** Do not answer any query, just decide what kind of query is given to you. ***
*** Do NOT add explanations, questions, or extra text. Only output the classification label(s). ***

-> Respond with 'general (query)' if a query can be answered by a llm model and doesn't require real-time information.
   Examples: 'how are you?' -> 'general how are you?', 'what is python?' -> 'general what is python?'
   Also use 'general' for time/date queries: 'what's the time?' -> 'general what's the time?'
   Also use 'general' for incomplete/pronoun queries: 'who is he?' -> 'general who is he?'

-> Respond with 'realtime (query)' if a query requires up-to-date information.
   Examples: 'who is indian prime minister' -> 'realtime who is indian prime minister'
   'latest news about AI' -> 'realtime latest news about AI'
   'what is the networth of elon musk?' -> 'what is the networth of elon musk?'

-> Respond with 'open (application or website name)' if a query is asking to open ANYTHING — 
   any app, website, system setting, file manager, camera, browser, or any named software.
   *** CRITICAL: ANY query starting with "open" must ALWAYS be classified as 'open ...' — NEVER as 'general'. ***
   *** Do NOT ask for clarification. Do NOT output 'general'. Just output 'open (name)'. ***
   Examples:
   'open settings' -> 'open settings'
   'open camera' -> 'open camera'
   'open files' -> 'open files'
   'open notepad' -> 'open notepad'
   'open instagram' -> 'open instagram'
   'open canva' -> 'open canva'
   'open chrome' -> 'open chrome'
   'open facebook' -> 'open facebook'
   'open file manager' -> 'open file manager'
   'open control panel' -> 'open control panel'
   Multiple apps: 'open chrome and firefox' -> 'open chrome, open firefox'

-> Respond with 'close (application name)' if a query is asking to close any application.
   Multiple: 'close chrome and notepad' -> 'close chrome, close notepad'

-> Respond with 'play (song name)' if a query is asking to play a song.
   Multiple: 'play song1 and song2' -> 'play song1, play song2'

-> Respond with 'generate image (image prompt)' if a query requests image generation.
   Examples: 'generate image of a lion' -> 'generate image of a lion'

-> Respond with 'reminder (datetime with message)' for reminders.
   Example: 'set a reminder at 9pm on 25th june for meeting' -> 'reminder 9:00pm 25th june meeting'

-> Respond with 'system (task)' for system tasks like mute, unmute, volume up, volume down.
   Multiple: 'mute and then volume up' -> 'system mute, system volume up'

-> Respond with 'content (topic)' if asked to write content, code, emails, applications, etc.

-> Respond with 'google search (topic)' to search on Google.

-> Respond with 'youtube search (topic)' to search on YouTube.

-> Respond with 'exit' if the user says goodbye or wants to end the conversation.

*** For multiple tasks: 'open facebook, telegram and close whatsapp' -> 'open facebook, open telegram, close whatsapp' ***
*** If you can't decide, use 'general (query)'. ***
*** If query has "can you / do you / are you able to" with a tool action, classify as general. ***
*** NEVER add extra explanation. ONLY output the label(s). ***
"""

# Seed examples — strong few-shot signals especially for 'open' edge cases
_SEED_MESSAGES = [
    {"role": "user",      "content": "how are you?"},
    {"role": "assistant", "content": "general how are you?"},
    {"role": "user",      "content": "open settings"},
    {"role": "assistant", "content": "open settings"},
    {"role": "user",      "content": "open camera"},
    {"role": "assistant", "content": "open camera"},
    {"role": "user",      "content": "open file manager"},
    {"role": "assistant", "content": "open file manager"},
    {"role": "user",      "content": "open control panel"},
    {"role": "assistant", "content": "open control panel"},
    {"role": "user",      "content": "open notepad"},
    {"role": "assistant", "content": "open notepad"},
    {"role": "user",      "content": "open chrome and firefox"},
    {"role": "assistant", "content": "open chrome, open firefox"},
    {"role": "user",      "content": "open chrome and tell me about Elon Musk."},
    {"role": "assistant", "content": "open chrome, realtime tell me about Elon Musk."},
    {"role": "user",      "content": "can you open chrome?"},
    {"role": "assistant", "content": "general can you open chrome?"},
    {"role": "user",      "content": "can you generate images?"},
    {"role": "assistant", "content": "general can you generate images?"},
    {"role": "user",      "content": "generate image of tony stark"},
    {"role": "assistant", "content": "generate image of tony stark"},
    {"role": "user",      "content": "what is today's date and remind me about my presentation on 5th august 11:00am"},
    {"role": "assistant", "content": "general what is today's date, reminder 11:00am 5th august presentation"},
    {"role": "user",      "content": "mute the volume"},
    {"role": "assistant", "content": "system mute"},
    {"role": "user",      "content": "volume up"},
    {"role": "assistant", "content": "system volume up"},
    {"role": "user",      "content": "close notepad"},
    {"role": "assistant", "content": "close notepad"},
    {"role": "user",      "content": "who is the current CEO of Tesla?"},
    {"role": "assistant", "content": "realtime who is the current CEO of Tesla?"},
    {"role": "user",      "content": "chat with me."},
    {"role": "assistant", "content": "general chat with me."},
]


def FirstLayerDMM(prompt: str = "test"):
    global _dynamic_history

    # Guard: never send empty prompt
    if not prompt or not prompt.strip():
        return []

    # Build full message array — complete history, no cap
    messages = (
        [{"role": "system", "content": _SYSTEM_PROMPT}]
        + _SEED_MESSAGES
        + _dynamic_history
        + [{"role": "user", "content": prompt}]
    )

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=100,
        temperature=0.3,
        stream=False
    )

    response = chat_completion.choices[0].message.content.strip()

    # Append to full history — no rolling cap as requested
    _dynamic_history.append({"role": "user",      "content": prompt})
    _dynamic_history.append({"role": "assistant", "content": response})

    # Post-process into list of tasks
    response = response.replace("\n", "")
    response = response.split(",")
    response = [i.strip() for i in response]

    temp = []
    for task in response:
        for func in funcs:
            if task.startswith(func):
                temp.append(task)

    response = temp

    if "(query)" in response:
        return FirstLayerDMM(prompt=prompt)
    else:
        return response


if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>> ")))