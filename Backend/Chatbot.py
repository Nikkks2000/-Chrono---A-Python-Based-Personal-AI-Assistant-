from groq import Groq  # Importing the Groq library
from json import load, dump  # Importing JSON functions
import datetime  # Importing datetime module
from dotenv import dotenv_values  # For loading .env variables

# Load environment variables from the .env file
env_vars = dotenv_values(".env")

# Retrieve specific environment variables
Username = env_vars.get("Username",)  # Default to "Nikhil" if not set
Assistantname = env_vars.get("Assistantname", )  # Default to "Jarvis" if not set
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client
client = Groq(api_key=GroqAPIKey)

# Initialize an empty list to store chat messages
messages = []

System = f"""Hello, I am{Assistantname} {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# Attempt to load the chat log from a JSON file
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)  # Load existing messages
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Real-time context data
def RealtimeInformation():
    current_date_time = datetime.datetime.now()

    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

# Clean AI response output
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Main chatbot function
def ChatBot(Query):
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        messages.append({"role": "user", "content": f"{Query}"})

        # ✅ This line should be indented like this
        messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        # Streamed response
        Answer = ""
        for chunk in completion:
            if hasattr(chunk.choices[0].delta, "content"):
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")

        # Add assistant reply to log
        messages.append({"role": "assistant", "content": Answer})

        # Save chat log
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)  # Retry

# Entry point
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Questions: ")
        print(ChatBot(user_input))


