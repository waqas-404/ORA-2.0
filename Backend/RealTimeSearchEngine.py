from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
from ddgs import DDGS

#load env variables from .env
env_vars = dotenv_values(".env")
#retrieve env variables for chatbot configuration
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
#initialize groq client with provided api
client = Groq(api_key=GroqAPIKey)
#provide system message that provides context to ai chatbot about its role and behavour
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional and concise way. ***"""
#attempt to load the chat log from json file
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    # if file doesnot exist create an empty json file for chatlog
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
#function to perform google search and format the results
def GoogleSearch(query):
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            results.append(r)

    print("DEBUG | Search results count:", len(results))

    Answer = f"The search results for '{query}' are:\n[start]\n"

    if not results:
        Answer += "No results found.\n"
    else:
        for r in results:
            Answer += (
                f"Title: {r.get('title','')}\n"
                f"Description: {r.get('body','')}\n\n"
            )

    Answer += "[end]"
    return Answer

 # function to clean up the answer by removing empty lines
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer
# pre-defined chatbot conversation system messages and an initial user message
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"},
]
#function to get real-time information like date and time
def Information():
    date = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date= current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
  
    data = f"Please use this real-time information if needed: \n"
    data += f"Day: {day}\n"
    date += f"Date: {date}\n"
    date += f"Month: {month}\n"
    date += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds. \n"
    return data
#function to handle real-time search and response generation
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages
  
    #load the chatlogs from json file
    with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
          
        #append the user queries to messages list
    messages.append({"role": "user", "content": f"{prompt}"})
  
    #add google seach results to system chatbot messages
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})
  
    #Generate the response using Groq client
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        max_tokens = 2048,
        temperature=0.7,
        top_p=1,
        stream = True,
    )
    Answer = ""
  
    for chunk in completion:
        if chunk.choices[0].delta.content: # check if there is content in current chunk
            Answer += chunk.choices[0].delta.content #append the content in the answer
  
    #clean up the response
    Answer = Answer.replace("</s>", "")
      
    #Append the chatbot's response to the message list
    messages.append({"role": "assistant", "content": Answer})
  
     #save the updated chatlog to json file
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)
  
    #remove the most recent system messages from theh chatbot conversation
    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)
#main entry point of the program for interactive querying
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))
