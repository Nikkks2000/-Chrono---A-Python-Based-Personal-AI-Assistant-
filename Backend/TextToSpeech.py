import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values
from time import sleep

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")

if not isinstance(AssistantVoice, str):
    print("Warning: AssistantVoice not found or not a string in .env. Using 'en-US-AriaNeural' as default.")
    AssistantVoice = "en-US-AriaNeural"

AUDIO_FILE_PATH = os.path.join("Data", "speech.mp3")

is_mixer_initialized = False

def TTS_init():
    global is_mixer_initialized
    if not is_mixer_initialized:
        print("DEBUG: Initializing pygame mixer.")
        try:
            pygame.mixer.init()
            is_mixer_initialized = True
            print("DEBUG: Pygame mixer initialized successfully.")
        except Exception as e:
            print(f"ERROR: Failed to initialize pygame mixer: {e}")
            is_mixer_initialized = False
            return False
    return True

def TTS_quit():
    global is_mixer_initialized
    if is_mixer_initialized:
        print("DEBUG: Quitting pygame mixer.")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            is_mixer_initialized = False
        except Exception as e:
            print(f"ERROR: Failed to quit pygame mixer: {e}")

async def TextToAudioFile(text) -> None:
    if os.path.exists(AUDIO_FILE_PATH):
        os.remove(AUDIO_FILE_PATH)
    
    print(f"DEBUG: Generating audio for text: '{text[:50]}...'")
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(AUDIO_FILE_PATH)
    print("DEBUG: Audio file saved.")

def TTS(Text):
    if not is_mixer_initialized:
        print("ERROR: Pygame mixer is not initialized. Cannot play audio.")
        return

    try:
        if not Text or not Text.strip():
            print("DEBUG: No text to speak.")
            return

        asyncio.run(TextToAudioFile(Text))

        pygame.mixer.music.load(AUDIO_FILE_PATH)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            sleep(0.1)
        
        pygame.mixer.music.stop()
        print("DEBUG: Audio playback finished.")

    except Exception as e:
        print(f"ERROR: Error in TTS during playback: {e}")

def TextToSpeech(Text):
    if not Text or not Text.strip():
        print("DEBUG: No text provided to TextToSpeech function.")
        return

    Data = str(Text).split(".")

    responses = [
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
        "Sir, look at the chat screen for the complete answer."
    ]

    if len(Data) > 4 and len(Text) >= 250:
        shortened_text = " ".join(Data[0:2]).strip() + ". " + random.choice(responses)
        TTS(shortened_text)
        print(f"DEBUG: Spoke shortened text. Full text: {Text}")
    else:
        TTS(Text)

if __name__ == "__main__":
    if TTS_init():
        while True:
            text_input = input("Enter the text: ")
            if text_input.lower() == "exit":
                break
            TextToSpeech(text_input)
        TTS_quit()
    else:
        print("Failed to initialize TTS. Exiting.")