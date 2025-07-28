from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
from time import sleep
import sys

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en")
ChromeExecutablePath = env_vars.get("ChromeExecutablePath")
ChromeProfilePath = env_vars.get("ChromeProfilePath")


HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition = null;
        let finalTranscript = '';

        function startRecognition() {
            output.textContent = '';
            if (recognition) {
                recognition.stop();
            }
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '{language}';
            recognition.interimResults = false;
            recognition.continuous = false;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                finalTranscript += transcript;
                output.textContent = finalTranscript;
                recognition.stop();
            };
            
            recognition.onend = function() {
                console.log("Recognition ended.");
            };
            
            recognition.onerror = function(event) {
                console.error("Speech recognition error:", event.error);
                output.textContent = "Error: " + event.error;
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
        }
    </script>
</body>
</html>'''.replace('{language}', InputLanguage)

try:
    if not os.path.exists("Data"):
        os.makedirs("Data")
    with open(os.path.join("Data", "Voice.html"), "w") as f:
        f.write(HtmlCode)
    print("DEBUG: Voice.html written successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to write Voice.html: {e}")
    sys.exit(1)

current_dir = os.getcwd()
Link = f"file:///{os.path.join(current_dir, 'Data', 'Voice.html')}"

chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")
if ChromeExecutablePath and os.path.exists(ChromeExecutablePath):
    chrome_options.binary_location = ChromeExecutablePath
if ChromeProfilePath and os.path.exists(ChromeProfilePath):
    chrome_options.add_argument(f"user-data-dir={ChromeProfilePath}")

speech_driver = None
try:
    service = Service(ChromeDriverManager().install())
    speech_driver = webdriver.Chrome(service=service, options=chrome_options)
    print("DEBUG: Chrome WebDriver initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Chrome WebDriver: {e}")
    sys.exit(1)

TempDirPath = os.path.join(current_dir, "Frontend", "Files")

def SetAssistantStatus(Status):
    try:
        with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
            file.write(Status)
    except IOError as e:
        print(f"ERROR: Could not write status to Status.data: {e}")

def QueryModifier(Query):
    if not Query:
        return ""
    
    new_query = Query.lower().strip()
    query_words = new_query.split()
    
    if not query_words:
        return ""

    question_words = [
        "how", "what", "who", "where", "when", "why", "which",
        "whose", "whom", "can you", "what's", "where's", "how's"
    ]

    if any(word in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    if not Text:
        return ""
    print(f"DEBUG: Translating text: '{Text}'")
    try:
        english_translation = mt.translate(Text, "en", "auto")
        print(f"DEBUG: Translated text: '{english_translation}'")
        return english_translation.capitalize()
    except Exception as e:
        print(f"ERROR: Translation failed: {e}")
        return ""

def SpeechRecognition():
    print("DEBUG: Starting SpeechRecognition in Selenium browser.")
    SetAssistantStatus("Listening...")
    try:
        speech_driver.get(Link)
        speech_driver.find_element(by=By.ID, value="start").click()
        print("DEBUG: Recognition started in browser. Waiting for text...")
        
        wait = WebDriverWait(speech_driver, 30)
        output_element = wait.until(
            lambda driver: speech_driver.find_element(by=By.ID, value="output").text.strip() != ""
        )
        
        Text = output_element.text.strip()
        print(f"DEBUG: Recognized text from browser: '{Text}'")
        
        speech_driver.find_element(by=By.ID, value="end").click()
        
        if Text:
            if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                return QueryModifier(Text)
            else:
                SetAssistantStatus("Translating...")
                translated_query = UniversalTranslator(Text)
                return QueryModifier(translated_query)
        else:
            return ""
            
    except Exception as e:
        print(f"ERROR: SpeechRecognition failed or timed out: {e}")
        SetAssistantStatus("Recognition Failed.")
        return ""

if __name__ == "__main__":
    try:
        while True:
            text = SpeechRecognition()
            if text:
                print(f"Final Recognized Text: {text}")
            else:
                print("No text recognized or an error occurred.")
            sleep(1)
    finally:
        print("Closing WebDriver.")
        speech_driver.quit()