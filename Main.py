from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealTimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation, StartReminderDaemon
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import sys
import json
import os


env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you? {Assistantname} : Welcome {Username}. I am doing well. How may I help you?'''
processes = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "reminder"]

def ShowDefaultChatIfNoChats():
    File = open(r"Data\ChatLog.json", "r", encoding='utf-8')
    if len(File.read()) < 5:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write('')
        with open(TempDirectoryPath('Response.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8')
    Data = File.read()
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Response.data'), 'w', encoding='utf-8')
        File.write(result)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    StartReminderDaemon()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()

    # ── GUARD: skip empty queries — prevents Cohere BadRequestError ───────────
    if not Query or not Query.strip():
        SetAssistantStatus("Available...")
        return False

    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    # ── GUARD: skip if model returned nothing usable ──────────────────────────
    if not Decision:
        SetAssistantStatus("Available...")
        return False

    print("")
    print(f"Decision : {Decision}")
    print("")

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])

    Mearged_Query = " and ".join(
        [
            " ".join(i.split()[1:])
            for i in Decision
            if i.startswith("general") or i.startswith("realtime")
        ]
    ).strip()

    for queries in Decision:
        if queries.startswith("generate image"):
            ImageGenerationQuery = queries.replace("generate image", "").replace("of", "").strip()
            ImageExecution = True

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution == True:
        with open(r"Frontend\Files\ImageGeneration.data", "w", encoding="utf-8") as file:
            file.write(f"{ImageGenerationQuery},True")

        img_confirm = "Sure sir, I will let you know when the images are ready."
        ShowTextToScreen(f"{Assistantname} : {img_confirm}")
        SetAssistantStatus("Answering...")
        TextToSpeech(img_confirm)
        SetAssistantStatus("Available...")

        try:
            with open(r"Data\ChatLog.json", "r", encoding="utf-8") as f:
                chatlog = json.load(f)
            chatlog.append({"role": "user", "content": f"Generate image of {ImageGenerationQuery}"})
            chatlog.append({"role": "assistant", "content": img_confirm})
            with open(r"Data\ChatLog.json", "w", encoding="utf-8") as f:
                json.dump(chatlog, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving image gen to chatlog: {e}")

        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(project_root, "Backend", "ImageGeneration.py")

            p1 = subprocess.Popen(
                [sys.executable, script_path],
                cwd=project_root,
                shell=False
            )
            processes.append(p1)

            def MonitorImageGeneration(process):
                process.wait()
                done_msg = "Sir, the images are ready."
                print(f"[bold green]{done_msg}[/bold green]")
                try:
                    ShowTextToScreen(f"{Assistantname} : {done_msg}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(done_msg)
                    SetAssistantStatus("Available...")
                    with open(r"Data\ChatLog.json", "r", encoding="utf-8") as f:
                        chatlog = json.load(f)
                    chatlog.append({"role": "assistant", "content": done_msg})
                    with open(r"Data\ChatLog.json", "w", encoding="utf-8") as f:
                        json.dump(chatlog, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    print(f"Error notifying image completion: {e}")

            monitor_thread = threading.Thread(target=MonitorImageGeneration, args=(p1,), daemon=True)
            monitor_thread.start()

        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_Query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True

    else:
        for Queries in Decision:

            if "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True

            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True

            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering...")
                os._exit(1)


def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()

            if "Available..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available...")


def SecondThread():
    GraphicalUserInterface()


if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()