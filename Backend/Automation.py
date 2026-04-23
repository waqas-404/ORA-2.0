from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
import urllib.parse
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import json
import threading
import os
from datetime import datetime

#load the env variables from .env file
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

#define CSS CLASSES for parsing specific elements to HTML content
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table__webanswers-table", "dDoNO ikb48b gsrt", "sXLaOe", 
           "LWkfke", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

#define a user-agent for making web requests
useragent = 'Mozilla/5.0 (Windows NT 10.0: Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

#Initailize the Groq client with the API Key
client = Groq(api_key = GroqAPIKey)

#predefined professional responses for user interaction
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at you service for any additional questions or support you may need-don't hesitate to ask.",
]

#List to store messages
messages = []

# system messages to provide context to the chatbot
SystemChatBot = [
    {"role": "system", "content": f"Hello, I am {os.environ['username']}, You're a content writer. You have to write content like letters, applications, stories and create music symphonies "}
]

#function to perform search
def GoogleSearch(Topic):
    search(Topic) #use pywhatkit's search function to perform a Google Search
    return True #indicate success

#function to generate content using AI  and save it as a file
def Content(Topic):
    
    #nested function to open a file in notepad.
    def OpenNotepad(File):
        default_text_editor = "notepad.exe" #default text editor
        subprocess.Popen([default_text_editor, File]) #open the file in notepad
    
    #nested function to generate content using AI chatbot
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", #specify the AI model
            messages = SystemChatBot + messages, 
            max_tokens = 2048,
            temperature= 0.7, #adjust the response randomness
            top_p = 1, #use nucleus sampling for response diversity
            stream = True, #enable streaming response
            stop = None #allow the model to determine stopping conditions
        )
        
        Answer = "" #initialize and empty string for the response
        
        #proceed streamed response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content: #check for content in the current chunk
                Answer += chunk.choices[0].delta.content #append the content to the answer
        
        Answer = Answer.replace("</s>", "") #remove unwanted tokens from the response
        messages.append({"role": "assistant", "content": Answer}) # add the AI response to the messages
        return Answer
    
    Topic: str = Topic.replace("Content ", "") #remove the "Content" from the topic
    ContentByAI = ContentWriterAI(Topic) #generate content using AI
    
    #Save the generate content to a text file
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI) #write the content to the file
        file.close()
    
    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt") #open the file in Notepad
    return True #indicate success

#Function to search for a topic on youtube
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}" #construct the YouTube search URL
    webbrowser.open(Url4Search) #open the search URL  in the web browser
    return True #Indicate success

#define function to play a video on YouTube
def PlayYoutube(query):
    playonyt(query) # Use pywhatkit's playonyt function to play the video
    return True

#Function to oopen a application or a relevent webpage
def OpenApp(app, sess=requests.session()):
    app = (app or "").strip().lower()

    web_apps = {
        "youtube": "https://www.youtube.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "gmail": "https://mail.google.com",
        "whatsapp": "https://web.whatsapp.com",
        "chatgpt": "https://chat.openai.com",
        "openai": "https://openai.com",
        "notion": "https://www.notion.so",
        "canva": "https://www.canva.com",
        "figma": "https://www.figma.com",
        "etsy": "https://www.etsy.com",
        "google": "https://www.google.com",
        "maps": "https://maps.google.com",
        "google maps": "https://maps.google.com",      
                                 
    }
    
    # 1) Try to open installed app first
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        pass
    
    # 2) If not installed, open website if known
    if app in web_apps:
        webbrowser.open(web_apps[app])
        return True

    # 3) Final fallback: open a Google search page (no scraping)
    q = urllib.parse.quote_plus(app)
    webbrowser.open(f"https://www.google.com/search?q={q}")
    return True
    # try:
    #     appopen(app, match_closest=True, output=True, throw_error=True) #attempt to opent the app
    #     return True 
    # except:
    #     #nested function to extract links from HTML content
    #     def extract_links(html):
    #         if html is None:
    #             return []
    #         soup = BeautifulSoup(html, 'html.parser') #parse the HTML content
    #         links = soup.find_all('a', {'jsname': 'UWckNb'}) #Find the relevant links
    #         return [link.get('href') for link in links] #return the links
    #     # Nested function to perform google search and retrieve HTML
    #     def search_google(query):
    #         url = f"https://www.google.com/search?q={query}" # Construct the Google search URL
    #         headers = {"User-Agent":useragent}  # Use the predefned user-agent
    #         response = sess.get(url, headers=headers)  #perform the GET request.
            
    #         if response.status_code == 200:
    #             return response.text #return the HTML content
    #         else:
    #             print("Failed to retrieve search results.") #print error message
    #         return None
        
    #     html = search_google(app) #perform the google search
        
    #     if html:
    #         link = extract_links(html)[0] # Extract the first link from the search results
    #         webopen(link) # Open the link in the web browser
            
    #     return True

# Function to close an application
def CloseApp(app):
    if "chrome" in app:
        pass  # Skip if the app is chrome
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True) # Attempt to close the app
            return True # Indicate success
        except:
            return False # Indicate failure
        
# Function to execute system level commands.
def System(command):
    
    #nested function to mute the system volume
    def mute():
        keyboard.press_and_release("volume mute") #simulate the mute key press
        
    #nested function to unmute the system volume
    def unmute():
        keyboard.press_and_release("volume mute") #simulate the unmute key press
        
    #nested function to increase the system volume
    def volume_up():
        keyboard.press_and_release("volume up") #simulate the volume up key press
    
    #nested function to decrease the system volume
    def volume_down():
        keyboard.press_and_release("volume down") #simulate the volume down key press
        
    #Execute the appropriate command
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    
    return True

# Helper function to save user and assistant messages to ChatLog.json
def SaveToChatLog(user_msg=None, assistant_msg=None):
    try:
        chatlog_path = r"Data\ChatLog.json"
        with open(chatlog_path, "r", encoding="utf-8") as f:
            chatlog = json.load(f)
        if user_msg:
            chatlog.append({"role": "user", "content": user_msg})
        if assistant_msg:
            chatlog.append({"role": "assistant", "content": assistant_msg})
        with open(chatlog_path, "w", encoding="utf-8") as f:
            json.dump(chatlog, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to chatlog: {e}")

# Helper function to speak a confirmation and show it on the GUI
def SpeakConfirmation(message):
    try:
        from Backend.TextToSpeech import TextToSpeech
        from Frontend.GUI import ShowTextToScreen, SetAssistantStatus
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        assistant_name = env.get("Assistantname", "ORA")
        
        ShowTextToScreen(f"{assistant_name} : {message}")
        SetAssistantStatus("Answering...")
        TextToSpeech(message)
        SetAssistantStatus("Available...")
    except Exception as e:
        print(f"Error speaking confirmation: {e}")

# Function to set a reminder using Groq LLM for natural language datetime parsing
def SetReminder(reminder_text):
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
    
    parse_prompt = f"""Extract the reminder datetime and message from the following text.
Current date and time is: {current_time}

Reminder text: "{reminder_text}"

Respond ONLY in this exact format (no extra text):
DATETIME: YYYY-MM-DD HH:MM
MESSAGE: <the reminder message>

Examples:
- Input: "9:00pm 25th june business meeting" → DATETIME: 2026-06-25 21:00\nMESSAGE: business meeting
- Input: "3pm tomorrow meeting" → DATETIME: {datetime.now().strftime('%Y-%m-%d')} 15:00\nMESSAGE: meeting
- Input: "in 30 minutes take medicine" → calculate from current time\nMESSAGE: take medicine
"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": parse_prompt}],
            max_tokens=100,
            temperature=0.1,
        )
        
        response = completion.choices[0].message.content.strip()
        print(f"[bold green]Groq parsed reminder:[/bold green] {response}")
        
        # Parse the response
        lines = response.strip().split("\n")
        reminder_datetime = ""
        reminder_message = ""
        
        for line in lines:
            if line.startswith("DATETIME:"):
                reminder_datetime = line.replace("DATETIME:", "").strip()
            elif line.startswith("MESSAGE:"):
                reminder_message = line.replace("MESSAGE:", "").strip()
        
        if not reminder_datetime or not reminder_message:
            print("[bold red]Failed to parse reminder from LLM response.[/bold red]")
            return False
        
        # Validate the datetime format
        parsed_dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M")
        
        # Load existing reminders
        reminders_path = r"Data\Reminders.json"
        try:
            with open(reminders_path, "r", encoding="utf-8") as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reminders = []
        
        # Add new reminder
        new_reminder = {
            "datetime": reminder_datetime,
            "message": reminder_message,
            "original": reminder_text
        }
        reminders.append(new_reminder)
        
        # Save reminders
        with open(reminders_path, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
        
        # Format confirmation message and speak it aloud
        formatted_time = parsed_dt.strftime("%I:%M %p on %B %d, %Y")
        confirmation = f"Ok sir, your reminder set for {formatted_time}. I will remind you about the {reminder_message}."
        print(f"[bold green]{confirmation}[/bold green]")
        
        SaveToChatLog(f"Set a reminder: {reminder_text}", confirmation)
        SpeakConfirmation(confirmation)
        
        return confirmation
        
    except Exception as e:
        print(f"[bold red]Error setting reminder: {e}[/bold red]")
        return False

# Function to check and fire due reminders (runs in background daemon thread)
def CheckReminders():
    from Backend.TextToSpeech import TextToSpeech
    from Frontend.GUI import ShowTextToScreen, SetAssistantStatus
    from dotenv import dotenv_values
    
    env = dotenv_values(".env")
    assistant_name = env.get("Assistantname", "ORA")
    
    import time
    reminders_path = r"Data\Reminders.json"
    
    while True:
        try:
            time.sleep(30)  # Check every 30 seconds
            
            if not os.path.exists(reminders_path):
                continue
            
            with open(reminders_path, "r", encoding="utf-8") as f:
                reminders = json.load(f)
            
            if not reminders:
                continue
            
            now = datetime.now()
            fired = []
            remaining = []
            
            for reminder in reminders:
                try:
                    reminder_dt = datetime.strptime(reminder["datetime"], "%Y-%m-%d %H:%M")
                    if now >= reminder_dt:
                        fired.append(reminder)
                    else:
                        remaining.append(reminder)
                except ValueError:
                    remaining.append(reminder)  # Keep malformed entries
            
            if fired:
                # Save remaining reminders
                with open(reminders_path, "w", encoding="utf-8") as f:
                    json.dump(remaining, f, indent=2, ensure_ascii=False)
                
                # Fire each due reminder
                for reminder in fired:
                    message = f"Sir, you have a reminder for your {reminder['message']} now"
                    print(f"[bold yellow] REMINDER: {reminder['message']}[/bold yellow]")
                    
                    try:
                        ShowTextToScreen(f"{assistant_name} :  {message}")
                        SetAssistantStatus("Reminding...")
                        TextToSpeech(message)
                        SetAssistantStatus("Available...")
                        SaveToChatLog(assistant_msg=message)
                    except Exception as e:
                        print(f"Error firing reminder: {e}")
                    
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        except Exception as e:
            print(f"Reminder checker error: {e}")

# Function to start the reminder daemon thread
def StartReminderDaemon():
    daemon = threading.Thread(target=CheckReminders, daemon=True)
    daemon.start()
    print("[bold cyan]Reminder daemon started.[/bold cyan]")

# Asynchronous function to translate and execute user commands
async def TranslateAndExecute(commands: list[str]):
    
    funcs = [] #list to store asynchronous tasks
    dispatched_tasks = [] #list to track dispatched command descriptions
    
    for command in commands:
        if command.startswith("open "): #handle 'open' commands
            
            if "open it" in command: #ignore "open it" commands
                pass
            
            elif "open file" == command: # ignore 'open file' commands
                pass
            
            else:
                app_name = command.removeprefix("open").strip()
                fun = asyncio.to_thread(OpenApp, app_name)  #schedule app opening
                funcs.append(fun)
                dispatched_tasks.append(("open", app_name))
                
            
        elif command.startswith("general "):  #placeholder for general commands
            pass
        
        elif command.startswith("realtime "): # placeholder for real-time commands
            pass
        
        elif command.startswith("close "):  #handle "close" commands
            app_name = command.removeprefix("close ").strip()
            fun = asyncio.to_thread(CloseApp, app_name)  #schedule app closing
            funcs.append(fun)
            dispatched_tasks.append(("close", app_name))
        
        elif command.startswith("play "): # handle "play " commands
            song_name = command.removeprefix("play ").strip()
            fun = asyncio.to_thread(PlayYoutube, song_name)  #schedule YouTube video playback
            funcs.append(fun)
            dispatched_tasks.append(("play", song_name))
            
        elif command.startswith("content "): #handle "content" commands
            topic = command.removeprefix("content ").strip()
            fun = asyncio.to_thread(Content, topic)  #schedule content generation
            funcs.append(fun)
            dispatched_tasks.append(("content", topic))
            
        elif command.startswith("google search "): #handle google search commands
            topic = command.removeprefix("google search ").strip()
            fun = asyncio.to_thread(GoogleSearch, topic)  #schedule google search
            funcs.append(fun)
            dispatched_tasks.append(("google search", topic))
        
        elif command.startswith("youtube search "): #handle youtube search commands
            topic = command.removeprefix("youtube search ").strip()
            fun = asyncio.to_thread(YouTubeSearch, topic)  #schedule youtube search
            funcs.append(fun)
            dispatched_tasks.append(("youtube search", topic))
            
        elif command.startswith("system "): #handle system commands
            action = command.removeprefix("system ").strip()
            fun = asyncio.to_thread(System, action)  #schedule system command execution
            funcs.append(fun)
            dispatched_tasks.append(("system", action))
        
        elif command.startswith("reminder "): #handle reminder commands
            fun = asyncio.to_thread(SetReminder, command.removeprefix("reminder ").strip())  #schedule reminder setting
            funcs.append(fun)
            # Reminder handles its own confirmation, don't add to dispatched_tasks
            
        else:
            print(f"No Function Found For {command}") #print error for unrecognized commands
            
    results = await asyncio.gather(*funcs, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            print("Automation task error:", repr(r))
    
    # Build and speak confirmation for non-reminder tasks
    if dispatched_tasks:
        # Build user-friendly summary of what was done
        descriptions = []
        for task_type, detail in dispatched_tasks:
            if task_type == "open":
                descriptions.append(f"opened {detail}")
            elif task_type == "close":
                descriptions.append(f"closed {detail}")
            elif task_type == "play":
                descriptions.append(f"playing {detail}")
            elif task_type == "content":
                descriptions.append(f"written the content about {detail} and opened it in Notepad")
            elif task_type == "google search":
                descriptions.append(f"searched for {detail} on Google")
            elif task_type == "youtube search":
                descriptions.append(f"searched for {detail} on YouTube")
            elif task_type == "system":
                descriptions.append(f"{detail}")
        
        if descriptions:
            if len(descriptions) == 1:
                confirmation = f"Sure sir, I've {descriptions[0]}."
            else:
                confirmation = f"Sure sir, I've {', '.join(descriptions[:-1])} and {descriptions[-1]}."
            
            # Build user command summary for chatlog
            user_summary = ", ".join([f"{t} {d}" for t, d in dispatched_tasks])
            
            print(f"[bold green]{confirmation}[/bold green]")
            await asyncio.to_thread(SaveToChatLog, user_summary, confirmation)
            await asyncio.to_thread(SpeakConfirmation, confirmation)
    
    for result in results: #process the results
        if isinstance(result, str):
            yield result
        else:
            yield result

#asynchronous function to automate command execution
async def Automation(commands: list[str]):
    
    async for result in TranslateAndExecute(commands): #tranlate and execute commands
        pass
    
    return True #indicate success