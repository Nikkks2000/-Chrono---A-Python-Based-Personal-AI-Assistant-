import sys
import os
import json
import threading
import subprocess
from asyncio import run
from time import sleep

# Add Frontend and Backend directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "Frontend"))
sys.path.append(os.path.join(current_dir, "Backend"))

from Frontend.GUI import (GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen, TempDirectoryPath, SetMicrophoneStatus, AnswerModifier, QueryModifier, GetMicrophoneStatus, GetAssistantStatus)

# Import Backend modules after adding to path
try:
    from Backend.Model import FirstLayerDMM
    from Backend.RealtimeSearchEngine import RealtimeSearchEngine
    from Backend.Automation import Automation
    # FIX: Corrected the import statement to use the correct variable name, speech_driver
    from Backend.SpeechToText import SpeechRecognition, speech_driver
    from Backend.Chatbot import ChatBot
    from Backend.TextToSpeech import TextToSpeech, TTS_init, TTS_quit
    print("DEBUG: All Backend modules imported successfully.")
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import Backend modules. Check your Backend folder structure and file names. Error: {e}")
    sys.exit(1)

from dotenv import dotenv_values

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f"""{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?"""

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "Youtube"]

def ShowDefaultChatIfNoChats():
    """
    Checks if ChatLog.json exists and has content.
    If not, it ensures Database.data is empty and sets a default message in Responses.data.
    """
    chat_log_path = os.path.join('Data', 'ChatLog.json')
    print(f"DEBUG: Checking default chat for {chat_log_path}")

    try:
        data_dir = os.path.dirname(chat_log_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"DEBUG: Created directory: {data_dir}")

        should_set_default = False
        if not os.path.exists(chat_log_path) or os.path.getsize(chat_log_path) == 0:
            print(f"DEBUG: ChatLog.json is empty or not found. Needs default setup.")
            should_set_default = True
        else:
            try:
                with open(chat_log_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        should_set_default = True
                    else:
                        json.loads(content)
                        print(f"DEBUG: ChatLog.json exists and is valid JSON.")
            except json.JSONDecodeError:
                print(f"WARNING: ChatLog.json is malformed. Re-initializing to default.")
                should_set_default = True
            except Exception as e:
                print(f"ERROR checking ChatLog.json content: {e}. Re-initializing to default.")
                should_set_default = True

        if should_set_default:
            with open(chat_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"DEBUG: Initialized empty ChatLog.json.")

            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            print(f"DEBUG: Cleared Database.data.")

            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(DefaultMessage)
            print(f"DEBUG: Wrote DefaultMessage to Responses.data.")

    except Exception as e:
        print(f"ERROR in ShowDefaultChatIfNoChats (outer block): {e}")
        try:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(DefaultMessage)
            print(f"DEBUG: Fallback: Wrote DefaultMessage to Responses.data due to error.")
        except Exception as e_fallback:
            print(f"ERROR: Fallback write to Responses.data also failed: {e_fallback}")


def ReadChatLogJson():
    """Reads and returns the content of ChatLog.json."""
    chat_log_path = os.path.join('Data', 'ChatLog.json')
    print(f"DEBUG: Reading ChatLog.json from: {chat_log_path}")
    if not os.path.exists(chat_log_path):
        print(f"WARNING: ChatLog.json not found at {chat_log_path}. Returning empty list.")
        return []
    try:
        with open(chat_log_path, 'r', encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                print("DEBUG: ChatLog.json is empty. Returning empty list.")
                return []
            chatlog_data = json.loads(content)
        print(f"DEBUG: Successfully read ChatLog.json. Data length: {len(chatlog_data)}")
        return chatlog_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode ChatLog.json. It might be empty or malformed: {e}")
        try:
            with open(chat_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print("DEBUG: Reset ChatLog.json to empty list due to decode error.")
        except IOError as e_fix:
            print(f"ERROR: Could not reset ChatLog.json: {e_fix}")
        return []
    except IOError as e:
        print(f"ERROR: Could not read ChatLog.json due to IOError: {e}")
        return []

def ChatLogIntegration():
    """
    Reads chat history from ChatLog.json, formats it, and writes to Database.data.
    """
    print("DEBUG: Starting ChatLogIntegration.")
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry.get("role") == "user":
            formatted_chatlog += f"{Username}: {entry.get('content', '')}\n"
        elif entry.get("role") == "assistant":
            formatted_chatlog += f"{Assistantname}: {entry.get('content', '')}\n"

    final_chatlog = AnswerModifier(formatted_chatlog)

    db_file_path = TempDirectoryPath('Database.data')
    try:
        with open(db_file_path, 'w', encoding='utf-8') as file:
            file.write(final_chatlog)
        print(f"DEBUG: Wrote formatted chatlog to Database.data. Length: {len(final_chatlog)}")
    except IOError as e:
        print(f"ERROR: Could not write formatted chatlog to Database.data: {e}")

def ShowChatsOnGUI():
    """
    Reads chat data from 'Database.data' and writes it to 'Responses.data'
    for display on the GUI.
    """
    db_file_path = TempDirectoryPath('Database.data')
    responses_file_path = TempDirectoryPath('Responses.data')
    data = ""
    print(f"DEBUG: Starting ShowChatsOnGUI. Reading from {db_file_path}")
    try:
        with open(db_file_path, 'r', encoding='utf-8') as db_file:
            data = db_file.read()
        print(f"DEBUG: Read {len(data)} characters from Database.data.")
    except FileNotFoundError:
        print(f"WARNING: Database.data not found at {db_file_path}. No chats to load for GUI.")
        data = ""
    except IOError as e:
        print(f"ERROR: Could not read Database.data for GUI: {e}")
        data = ""

    if len(data) > 0:
        result = data
        print(f"DEBUG: Writing {len(result)} characters from Database.data to Responses.data for GUI display.")
        try:
            with open(responses_file_path, 'w', encoding='utf-8') as response_file:
                response_file.write(result)
        except IOError as e:
            print(f"ERROR: Could not write to Responses.data for GUI: {e}")
    else:
        print("DEBUG: Database.data is empty, clearing Responses.data.")
        try:
            with open(responses_file_path, 'w', encoding='utf-8') as response_file:
                response_file.write("")
        except IOError as e:
            print(f"ERROR: Could not clear Responses.data: {e}")

def InitialExecution():
    """Performs initial setup for the GUI and chat system."""
    print("DEBUG: Starting InitialExecution.")
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    print("DEBUG: InitialExecution finished.")

def MainExecution():
    """Main logic for processing user queries and generating responses."""
    print("DEBUG: Starting MainExecution.")
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening....")
    try:
        Query = SpeechRecognition()
        if not Query:
            print("DEBUG: SpeechRecognition returned empty query. Skipping processing.")
            SetAssistantStatus("Available...")
            return False
        ShowTextToScreen(f"{Username}: {Query}")
        SetAssistantStatus("Thinking...")
    except Exception as e:
        print(f"ERROR: SpeechRecognition failed: {e}")
        SetAssistantStatus("Error in SpeechRec...")
        return False

    try:
        Decision = FirstLayerDMM(Query)
        print("\n")
        print(f"Decision: {Decision}")
        print("\n")
    except Exception as e:
        print(f"ERROR: FirstLayerDMM failed: {e}")
        SetAssistantStatus("Error in DMM...")
        TextToSpeech(f"I encountered an error trying to understand that, {Username}.")
        return False

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    MergedQuery = " and ".join([
        " ".join(i.split()[1:]) for i in Decision
        if i.startswith("general") or i.startswith("realtime")
    ])

    for queries in Decision:
        if "generate" in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True
            break

    if ImageExecution:
        image_gen_file_path = TempDirectoryPath("ImageGeneration.data")
        try:
            with open(image_gen_file_path, "w", encoding="utf-8") as file:
                file.write(f"{ImageGenerationQuery}, True")
            print(f"DEBUG: Image generation query written to {image_gen_file_path}")

            p1 = subprocess.Popen(
                ['python', os.path.join(current_dir, r'Backend\ImageGeneration.py')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            subprocesses.append(p1)
            print("DEBUG: ImageGeneration.py subprocess started.")
        except Exception as e:
            print(f"ERROR handling image generation subprocess: {e}")

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                try:
                    run(Automation(list(Decision)))
                    TaskExecution = True
                    print(f"DEBUG: Automation task executed: {queries}")
                    break
                except Exception as e:
                    print(f"ERROR: Automation failed for '{queries}': {e}")
                    SetAssistantStatus("Automation failed.")
                    TextToSpeech(f"I couldn't perform the requested automation, {Username}.")

    if G or R:
        SetAssistantStatus("Searching...")
        try:
            Answer = RealtimeSearchEngine(QueryModifier(MergedQuery))
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True
        except Exception as e:
            print(f"ERROR: RealtimeSearchEngine failed: {e}")
            SetAssistantStatus("Search failed.")
            TextToSpeech(f"I couldn't perform the search, {Username}.")
            return False
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general", "").strip()
                try:
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                except Exception as e:
                    print(f"ERROR: ChatBot failed: {e}")
                    SetAssistantStatus("Chatbot failed.")
                    TextToSpeech(f"My brain is having a moment, {Username}.")
                    return False

            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime", "").strip()
                try:
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                except Exception as e:
                    print(f"ERROR: RealtimeSearchEngine failed: {e}")
                    SetAssistantStatus("Search failed.")
                    TextToSpeech(f"I couldn't perform the search, {Username}.")
                    return False

            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                try:
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                except Exception as e:
                    print(f"WARNING: ChatBot failed for exit message: {e}")
                    ShowTextToScreen(f"{Assistantname}: Goodbye!")
                    TextToSpeech("Goodbye!")
                finally:
                    SetAssistantStatus("Idle")
                    for p in subprocesses:
                        if p.poll() is None:
                            p.terminate()
                            p.wait(timeout=1)
                            if p.poll() is None:
                                p.kill()
                                print(f"DEBUG: Force killed subprocess {p.pid}")
                        print(f"DEBUG: Subprocess {p.pid} terminated.")
                    sys.exit(0)

        print("DEBUG: No specific action matched in MainExecution for query.")
        SetAssistantStatus("Available...")
        fallback_message = f"{Assistantname}: I'm not sure how to respond to that."
        ShowTextToScreen(fallback_message)
        TextToSpeech(fallback_message)
        return False

def FirstThread():
    """Manages the main execution loop based on microphone status."""
    print("DEBUG: FirstThread (Main Logic) started.")
    while True:
        try:
            current_status = GetMicrophoneStatus()
            if current_status == "True":
                print("DEBUG: Microphone status is TRUE. Calling MainExecution.")
                MainExecution()
            else:
                ai_status = GetAssistantStatus()
                if "Available..." in ai_status:
                    pass
                else:
                    SetAssistantStatus("Available...")
                sleep(0.1)
        except Exception as e:
            print(f"ERROR in FirstThread loop: {e}")
            sleep(1)

def SecondThread():
    """Starts the Graphical User Interface."""
    print("DEBUG: SecondThread (GUI) started.")
    try:
        GraphicalUserInterface()
        print("DEBUG: GraphicalUserInterface call returned. GUI possibly closed.")
    except Exception as e:
        print(f"CRITICAL ERROR: GraphicalUserInterface failed to start or crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def CleanupAndExit():
    """Performs cleanup operations before exiting."""
    print("DEBUG: Running cleanup operations.")
    try:
        if speech_driver:
            print("DEBUG: Quitting speech recognition WebDriver.")
            speech_driver.quit()
    except Exception as e:
        print(f"ERROR: Failed to quit speech recognition WebDriver: {e}")
    
    try:
        TTS_quit()
    except Exception as e:
        print(f"ERROR: Failed to quit TTS mixer: {e}")
    
    sys.exit(0)

if __name__ == "__main__":
    print("DEBUG: __main__ block started.")

    try:
        temp_files_dir = os.path.join(current_dir, "Frontend", "Files")
        if not os.path.exists(temp_files_dir):
            os.makedirs(temp_files_dir)
            print(f"DEBUG: Created directory: {temp_files_dir}")

        if not os.path.exists(TempDirectoryPath('Mic.data')):
            SetMicrophoneStatus("False")
            print("DEBUG: Created Mic.data and set to False.")
        if not os.path.exists(TempDirectoryPath('Status.data')):
            SetAssistantStatus("Idle")
            print("DEBUG: Created Status.data and set to Idle.")
        if not os.path.exists(TempDirectoryPath('Database.data')):
            with open(TempDirectoryPath('Database.data'), "w", encoding='utf-8') as f:
                f.write("")
            print("DEBUG: Created empty Database.data.")
    except Exception as e:
        print(f"ERROR during initial file creation in __main__: {e}")
        sys.exit(1)

    data_dir_path = os.path.join(current_dir, 'Data')
    if not os.path.exists(data_dir_path):
        os.makedirs(data_dir_path)
        print(f"DEBUG: Created directory: {data_dir_path}")

    chat_log_path = os.path.join(data_dir_path, 'ChatLog.json')
    if not os.path.exists(chat_log_path) or os.path.getsize(chat_log_path) == 0:
        try:
            with open(chat_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"DEBUG: Initialized empty ChatLog.json at {chat_log_path}.")
        except IOError as e:
            print(f"ERROR creating/initializing ChatLog.json: {e}")
            sys.exit(1)
    else:
        try:
            with open(chat_log_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print("DEBUG: Existing ChatLog.json is valid JSON.")
        except json.JSONDecodeError:
            print(f"WARNING: ChatLog.json at {chat_log_path} is corrupted. Re-initializing.")
            try:
                with open(chat_log_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print("DEBUG: Reset ChatLog.json to empty list due to corruption.")
            except IOError as e:
                print(f"ERROR resetting corrupted ChatLog.json: {e}")
                sys.exit(1)

    InitialExecution()
    
    if not TTS_init():
        CleanupAndExit()

    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    print("DEBUG: FirstThread (main logic) started in background.")

    try:
        print("DEBUG: Calling SecondThread (GUI) in main thread.")
        SecondThread()
    except KeyboardInterrupt:
        print("\nDEBUG: Keyboard interrupt detected.")
    finally:
        CleanupAndExit()