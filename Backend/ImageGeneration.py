import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import dotenv_values # Use dotenv_values for clearer variable loading
import os
from time import sleep

# Load environment variables from .env file
env_vars = dotenv_values(".env")
HuggingFaceAPIKey = env_vars.get("HuggingFaceAPIKey")

# Ensure the Hugging Face API key is loaded
if not HuggingFaceAPIKey:
    print("Error: HuggingFaceAPIKey not found in .env file. Please make sure it's set.")
    # In a production environment, you might want to exit here:
    exit("Exiting due to missing HuggingFaceAPIKey.")

# Ensure Data folder exists
DATA_FOLDER = "Data"
if not os.path.exists(DATA_FOLDER):
    print(f"Creating missing folder: {DATA_FOLDER}")
    os.makedirs(DATA_FOLDER)

# Ensure Frontend\Files folder exists for ImageGeneration.data
FRONTEND_FILES_FOLDER = os.path.join("Frontend", "Files")
if not os.path.exists(FRONTEND_FILES_FOLDER):
    print(f"Creating missing folder: {FRONTEND_FILES_FOLDER}")
    os.makedirs(FRONTEND_FILES_FOLDER)

# Define the path to the ImageGeneration.data file
IMAGE_GEN_DATA_FILE = os.path.join(FRONTEND_FILES_FOLDER, "ImageGeneration.data")

# --- Consistent filename sanitization function ---
def sanitize_filename(prompt_text):
    # This function will be used by both generate_images and open_images
    # to ensure consistent filenames.
    # It removes spaces and non-alphanumeric characters, except underscore.
    return "".join(char for char in prompt_text if char.isalnum() or char == '_').replace(" ", "")

# Function to open and display images based on a given prompt
def open_images(prompt):
    print(f"Attempting to open images for prompt: '{prompt}'")
    
    sanitized_prompt = sanitize_filename(prompt) # Use the new sanitize function

    # Generate the filenames for the images - consistent with saving
    Files = [f"{sanitized_prompt}_{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(DATA_FOLDER, jpg_file)
        
        try:
            print(f"Checking for image: {image_path}")
            if os.path.exists(image_path):
                img = Image.open(image_path)
                print(f"Opening image: {image_path}")
                img.show()
                sleep(1) # Small delay between showing images
            else:
                print(f"Image file not found: {image_path}")
        except FileNotFoundError: # Specific catch for file not found
            print(f"Error: Image file not found at {image_path}. It might not have been generated or saved correctly.")
        except IOError as e:
            print(f"Error opening image {image_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while opening {image_path}: {e}")


# API details for the Hugging Face Stable Diffusion model
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {
    "Authorization": f"Bearer {HuggingFaceAPIKey}"
}

# Async function to send a query to the Hugging Face API
async def query(payload):
    try:
        # Add a timeout to prevent hanging indefinitely
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"API response status: {response.status_code}")
        # If the API returns JSON, it might contain an error message
        if response.headers.get('Content-Type') == 'application/json':
            json_response = response.json()
            if 'error' in json_response:
                print(f"Hugging Face API returned error: {json_response['error']}")
                # If there's a detailed_message, print that too
                if 'detailed_message' in json_response:
                    print(f"Detailed message: {json_response['detailed_message']}")
                return None # Indicate failure
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        # Log the response content if available, for API specific errors
        if hasattr(e, 'response') and e.response is not None:
            print(f"API error response status: {e.response.status_code}")
            try:
                print(f"API error response content: {e.response.json()}")
            except requests.exceptions.JSONDecodeError:
                print(f"API error response content (non-JSON): {e.response.text}")
        return None # Return None or raise a custom exception to signal failure
    except Exception as e:
        print(f"An unexpected error occurred during API query: {e}")
        return None

# Async function to generate images based on the given prompt
async def generate_images(prompt: str):
    print(f"Starting image generation for prompt: '{prompt}'")
    tasks = []

    sanitized_prompt = sanitize_filename(prompt) # Use the new sanitize function

    # Create 4 image generation tasks
    for i in range(4): # Loop 4 times for 4 images
        seed = randint(0, 1000000)
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={seed}",
        }
        print(f"Queueing image generation {i+1} with seed {seed}...")
        task = asyncio.create_task(query(payload))  # Create async task
        tasks.append(task)

    # Wait for all tasks to complete, returning exceptions if they occur
    image_bytes_list = await asyncio.gather(*tasks, return_exceptions=True)

    # Save the generated images to files
    for i, image_bytes in enumerate(image_bytes_list):
        if isinstance(image_bytes, Exception):
            print(f"Task {i+1} failed with exception: {image_bytes}")
            continue # Skip saving if the task failed

        if image_bytes: # Check if content was returned (not None)
            file_path = os.path.join(DATA_FOLDER, f"{sanitized_prompt}_{i + 1}.jpg") # Use sanitized_prompt here
            try:
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                print(f"Saved image: {file_path}")
            except IOError as e:
                print(f"Error saving image to {file_path}: {e}")
        else:
            print(f"No image content received for task {i+1} for prompt '{prompt}'. Image might not have been generated.")

    print(f"Finished image generation for prompt: '{prompt}'")


# Wrapper function to generate and open images
def GenerateImages(prompt: str):
    print(f"GenerateImages wrapper called for prompt: '{prompt}'")
    try:
        asyncio.run(generate_images(prompt))  # Run the async image generation
        print("Image generation complete in wrapper.")
        open_images(prompt)  # Open the generated images
        return True # Indicate success
    except Exception as e:
        print(f"Error in GenerateImages wrapper: {e}")
        return False # Indicate failure

# Main loop to check for image generation requests
print("Image generation script started. Waiting for requests in ImageGeneration.data...")
while True:
    try:
        # Read the status and prompt from the data file
        if not os.path.exists(IMAGE_GEN_DATA_FILE):
            print(f"Warning: Data file not found at {IMAGE_GEN_DATA_FILE}. Creating it with default content.")
            with open(IMAGE_GEN_DATA_FILE, "w") as f:
                f.write("False,False")
            sleep(1) # Give system a moment after creating file
            continue # Skip to next loop iteration

        with open(IMAGE_GEN_DATA_FILE, "r") as f:
            Data: str = f.read().strip() # Use .strip() to remove leading/trailing whitespace

        if not Data: # Handle empty file case
            print(f"Warning: {IMAGE_GEN_DATA_FILE} is empty. Writing default content.")
            with open(IMAGE_GEN_DATA_FILE, "w") as f:
                f.write("False,False")
            sleep(1)
            continue

        try:
            # Use maxsplit=1 to handle commas that might appear in the prompt itself
            Prompt, Status = Data.split(",", 1)
        except ValueError:
            print(f"Error: Invalid format in {IMAGE_GEN_DATA_FILE}. Expected 'Prompt,Status'. Content: '{Data}'. Resetting file.")
            with open(IMAGE_GEN_DATA_FILE, "w") as f:
                f.write("False,False")
            sleep(1)
            continue # Skip to next loop iteration


        # If the status indicates an image generation request
        if Status.strip().lower() == "true": # Use .lower() for case-insensitive check
            print(f"Image generation request detected. Prompt: '{Prompt}'")
            ImageStatus = GenerateImages(prompt=Prompt) # This calls async generate and then open

            # Reset the status in the file after attempting to generate images, regardless of success
            print(f"Resetting {IMAGE_GEN_DATA_FILE} to 'False,False'")
            with open(IMAGE_GEN_DATA_FILE, "w") as f:
                f.write("False,False")
            
            # If you want it to run once and exit, uncomment 'break'.
            # If you want it to continuously monitor for new requests, keep 'break' commented.
            # break 
            print("Processing complete for this request. Continuing to monitor...")
        else:
            # print(f"No active image generation request. Status: '{Status.strip()}'") # This can be too chatty
            sleep(1) # Wait before checking again

    except FileNotFoundError:
        print(f"Fatal Error: {IMAGE_GEN_DATA_FILE} not found. Please ensure the path is correct or it can be created.")
        sleep(5) # Wait before retrying to prevent rapid error spam
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
        sleep(5) # Wait before retrying to prevent rapid error spam