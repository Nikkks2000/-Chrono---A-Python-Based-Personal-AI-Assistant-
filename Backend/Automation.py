from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import sys

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "User")

if not GroqAPIKey:
    print("CRITICAL ERROR: GroqAPIKey not found in .env file. Please set it to use this module.")
    sys.exit(1)

try:
    client = Groq(api_key=GroqAPIKey)
    print("DEBUG: Groq client initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Groq client. Check your API key. Error: {e}")
    sys.exit(1)

classes = [
    "Cubwf", "hgKEL", "LTKOO", "SY7ric", "ZeLcW",
    "gsrt", "vk", "bk", "FzvwSb", "YwPhnf",
    "pclqee", "tw-Data-text", "tw-text-small", "tw-ta",
    "IZörde", "05uR6d", "vlzY6d", "webanswers-webanswers_table_webanswers-table",
    "dDoNo", "ikb4Bb", "sXLaße", "LWkfke", "VQF4g", "qv3Wpe",
    "kno-rdesc", "SPZz6b"
]

useragent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/100.0.4896.75 Safari/537.36"
)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need — don't hesitate to ask."
]

SystemChatBot = [
    {
        "role": "system",
        "content": f"Hello, I am {Username}. You're a content writer. You have to write content like a letter."
    }
]

def GoogleSearch(Topic):
    try:
        search(Topic)
        print(f"DEBUG: Performing Google search for: '{Topic}'")
        return True
    except Exception as e:
        print(f"ERROR: Google search failed for '{Topic}': {e}")
        return False

def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = "notepad.exe"
        try:
            subprocess.Popen([default_text_editor, File])
            print(f"DEBUG: Opened file '{File}' in Notepad.")
        except FileNotFoundError:
            print(f"ERROR: Notepad not found. Cannot open '{File}'.")
            return False
        return True

    def ContentWriterAI(prompt):
        current_messages = SystemChatBot + [{"role": "user", "content": prompt}]
        
        try:
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=current_messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=True,
                stop=None
            )
            Answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content
            
            Answer = Answer.replace("</s>", "").strip()
            print(f"DEBUG: AI generated content: '{Answer[:50]}...'")
            return Answer
        except Exception as e:
            print(f"ERROR: Groq API content generation failed: {e}")
            return "I am sorry, I am unable to generate content right now."

    Topic = Topic.removeprefix("content").strip()
    ContentByAI = ContentWriterAI(Topic)
    
    file_name = os.path.join("Data", f"{Topic.lower().replace(' ', '_')}.txt")
    
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(ContentByAI)
        print(f"DEBUG: AI content saved to '{file_name}'.")
        OpenNotepad(file_name)
    except IOError as e:
        print(f"ERROR: Failed to save or open file '{file_name}': {e}")
        return False
    
    return True

def YouTubeSearch(Topic):
    try:
        url_search = f"https://www.youtube.com/results?search_query={Topic}"
        webbrowser.open(url_search)
        print(f"DEBUG: Performing Youtube for: '{Topic}'")
        return True
    except Exception as e:
        print(f"ERROR: Youtube failed for '{Topic}': {e}")
        return False

def PlayYouTube(Query):
    try:
        playonyt(Query)
        print(f"DEBUG: Playing YouTube video for: '{Query}'")
        return True
    except Exception as e:
        print(f"ERROR: Playing YouTube video failed for '{Query}': {e}")
        return False

def OpenApp(app):
    try:
        appopen(app, match_closest=True, output=False, throw_errors=True)
        print(f"DEBUG: Opened app via AppOpener: '{app}'")
        return True
    except Exception as e:
        print(f"WARNING: AppOpener failed for '{app}': {e}. Falling back to web search.")
        try:
            webopen(f"https://www.google.com/search?q={app}")
            print(f"DEBUG: Opened web search for '{app}' as a fallback.")
            return True
        except Exception as e2:
            print(f"ERROR: Web search fallback failed for '{app}': {e2}")
            return False

def CloseApp(app):
    if "chrome" in app.lower():
        print("DEBUG: Skipping close command for Chrome (potentially unstable).")
        return True
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        print(f"DEBUG: Closed app via AppOpener: '{app}'")
        return True
    except Exception as e:
        print(f"ERROR: Closing app '{app}' failed: {e}")
        return False

def System(command):
    if command == "mute" or command == "unmute":
        keyboard.press_and_release("volume mute")
        print(f"DEBUG: Toggled system volume mute/unmute.")
    elif command == "volume up":
        keyboard.press_and_release("volume up")
        print(f"DEBUG: Increased system volume.")
    elif command == "volume down":
        keyboard.press_and_release("volume down")
        print(f"DEBUG: Decreased system volume.")
    else:
        print(f"WARNING: Unknown system command: '{command}'")
        return False
    return True

async def TranslateAndExecute(commands: list[str]):
    funcs = []
    for command in commands:
        command = command.strip()
        if command.lower().startswith("open "):
            app_name = command.lower().removeprefix("open").strip()
            funcs.append(asyncio.to_thread(OpenApp, app_name))
        elif command.lower().startswith("close "):
            app_name = command.lower().removeprefix("close").strip()
            funcs.append(asyncio.to_thread(CloseApp, app_name))
        elif command.lower().startswith("play "):
            query = command.lower().removeprefix("play").strip()
            funcs.append(asyncio.to_thread(PlayYouTube, query))
        elif command.lower().startswith("content "):
            topic = command.lower().removeprefix("content").strip()
            funcs.append(asyncio.to_thread(Content, topic))
        elif command.lower().startswith("google search "):
            topic = command.lower().removeprefix("google search").strip()
            funcs.append(asyncio.to_thread(GoogleSearch, topic))
        elif command.lower().startswith("Youtube "):
            topic = command.lower().removeprefix("Youtube").strip()
            funcs.append(asyncio.to_thread(YouTubeSearch, topic))
        elif command.lower().startswith("system "):
            sys_command = command.lower().removeprefix("system").strip()
            funcs.append(asyncio.to_thread(System, sys_command))
        elif command.lower().startswith("general ") or command.lower().startswith("realtime "):
            pass
        else:
            print(f"WARNING: No automation function found for command: '{command}'")
    
    results = await asyncio.gather(*funcs)
    
    for result in results:
        yield result

async def Automation(commands: list[str]):
    print(f"DEBUG: Automation module received commands: {commands}")
    async for result in TranslateAndExecute(commands):
        print(f"DEBUG: Automation task completed with result: {result}")
    return True