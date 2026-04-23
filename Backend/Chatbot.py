from groq import Groq
from json import load,dump
import datetime
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

# retrieve specific environment variables for username, assitant name, api
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

#initailize groq client using api key
client = Groq(api_key=GroqAPIKey)

#initialize empty list to store chat messages
# messages = []

#provide system message that provides context to ai chatbot about its role and behavour
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI agent named {Assistantname} which can do system automation tasks like opening apps and generating images, it also has real-time up-to-date information from the internet.
*** Do not tell time until asked explicitly, Do not talk too much, just answer the question and make it short.***
*** Reply in only English, even if the question is in Hindi, reply in English and in a consice way.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
*** If query contains “can you / do you / are you able to / do you support” and mentions a tool action (open/close/play/generate image/system/reminder/search), classify it as general and ask for a proper prompt.***
*** Address the user as "sir" for confirmation (e.g., "Hello sir", "Ofcourse sir", "Understood sir"), do not use it inside the paragraph, do not use it very often.*** 
*** You can: general chat, automation tasks, image generation, and web search via ORA modules.*** 
*** If user asks about capabilities,  respond: confirm capability and ask if the user wants to perform that task also explain how to use them.*** 
*** Do NOT claim you cannot generate images or do automation. Instead, tell the user the correct command format.*** 
*** If the user asks "can you generate images?" respond: confirm capability and ask for an image prompt.*** 
*** If the user asks "can you open instagram?" respond: confirm capability and ask for an proper prompt.*** 
*** If the user asks "can you open settings?" respond: confirm capability and ask for an proper prompt.*** 
*** If the context is insufficient, say you do not have enough information and ask for the missing detail or document and make it short as possible*** 
*** Whenever users asks something that is not in your capabilities, never say 'I am just a text base AI assistant' response this instead "I am a simple AI agent..."*** 
*** When user says 'wake up daddy's home', consider this as wakeup word and respond with 'Of course sir, I am always here at your service. What kind of task do you want me to do?" 
"""

#list of system instructions for the chatbot
SystemChatBot = [
    {"role": "system", "content": System}
]

#attempt to load the chat log from json file
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    # if file doesnot exist create an empty json file for chatlog
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    
# function to get realtime data and time information
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date= current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    
    #format informatiion into string
    data = f"Please use this real-time information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds. \n"
    return data

#function to modify the chatbot's response for better formatting
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

#main chatbot function to handle user queries
def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response. """ 
    messages = []  # ensure messages is always defined
    try:
        #load the exsiting chatlog from json file
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
            
        #append the user queries to messages list
        messages.append({"role": "user", "content": f"{Query}"})
        
        # Make a request to Groq api for a response
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens = 1024,
            temperature=0.7,
            top_p=1,
            stream = True,
            stop=None
        )
        Answer = ""
        
        for chunk in completion:
            if chunk.choices[0].delta.content: # check if there is content in current chunk
                Answer += chunk.choices[0].delta.content #append the content in the answer
        Answer = Answer.replace("</s>", "")
        
        #Append the chatbot's response to the message list
        messages.append({"role": "assistant", "content": Answer})
        
        #save the updated chatlog to json file
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)
            
        #return the formatted response
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)
        return ChatBot(Query)

#main program entry point
if __name__ == "__main__":
    while True:
        user_input = input("Enter your question: ")
        print(ChatBot(user_input))
        