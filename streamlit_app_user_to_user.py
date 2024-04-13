# Run this app (local testing: "streamlit run streamlit_app.py")

#!!! IMPORTANT !!! PyTorch for CPU is installed by default in the requirements.txt file. To install PyTorch for GPU:
# 1. Go to https://pytorch.org/get-started/locally/
# 2. Select your OS, Package, Python version, CUDA version, and Architecture
# 3. Copy the command and run it in your terminal (make sure environment is activated)
# Example: pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
import streamlit as st
import transformers
import requests
import torch
import time
import pymongo
import uuid
from streamlit_js_eval import streamlit_js_eval
import websocket
import json
import logging

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# App information and setup
# App information and setup
project_title = "AI Group Awareness Exercise"
project_desc = """
This App will help you perform the Group Awareness Exercise with an AI as a stand-in for a participant.
Conduct the back-and-forth conversation using the chat interface below.
"""

project_icon = "apeiron.png"
st.set_page_config(page_title=project_title, initial_sidebar_state='collapsed', page_icon=project_icon)

# additional info from the readme
add_info_md = """
This is an app that simulates the Group Awareness Exercise (GAE) with an AI as a stand-in for a participant.
The prescribed user for this is on Staff level, if not stop using this interface. Your goal is to conduct the back-and-forth conversation using the chat interface below.
And then tailor the conversation towards a proper/realistic GAE session - this will help train the AI model to better simulate a human participant.

-You can edit the messages in the chat history by clicking the "Show Edit Section" checkbox.
-You can clear the chat history by clicking the "Clear chat history" button.
-You can give the bot a background by entering it in the "Enter the bot's background" text input.
"""

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ws = None


if "model" not in st.session_state:
    st.session_state.model = {"model":None,"model_name":None}
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []






def parse_conversation(conversation_history, count_from_last = 20, display_only = True, reverse=False):
    conversation = ""
    conv_len = len(conversation_history)
    # parsing_dict = {"user":"### User: ", "assistant":"### AI Participant: "}
    parsing_dict = {"user":"User: ", "assistant":"Assistant: "}
    if conv_len > count_from_last:
        for i in range((conv_len-1) - (count_from_last-1), conv_len):
            conversation += parsing_dict[conversation_history[i]["role"]] + conversation_history[i]["content"] + "\n\n"
    else:
        for message in conversation_history:
            conversation += parsing_dict[message["role"]] + message["content"] + "\n\n"

    return conversation


def launch_with_voiceflow():
    voiceflow_api_key = "VF.DM.65aa7ba36894de0007bad42e.50qQAVpQyapvOmMI"
    user_id = "user_123"

    body = {
        "action": {"type": "launch"},
        "config": {
            "tts": False,
            "stripSSML": True,
            "stopAll": True,
            "excludeTypes": ["block", "debug", "flow"]
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": voiceflow_api_key
    }
    response = requests.post(
        f"https://general-runtime.voiceflow.com/state/user/{user_id}/interact",
        json=body,
        headers=headers,
    )

    # Extract chatbot response from Voiceflow
    print(response.json())

# Function to connect to MongoDB instance
def connect_to_mongodb():
    url = "mongodb://localhost:27017/"
    client = pymongo.MongoClient(url)
    return client

# Function to save conversation data to MongoDB
# Function to save conversation data to MongoDB
def save_to_mongodb(client, database_name, collection_name, data):
    db = client[database_name]
    collection = db[collection_name]
    collection.insert_one(data)


# Define the WebSocket server URL
WEBSOCKET_SERVER_URL = "ws://localhost:8000"

# Initialize chat messages list
chat_messages = []

# Function to handle new incoming messages
# WebSocket connection callback function to handle incoming messages
# Function to handle new incoming messages
def on_message(ws, message):
    global chat_messages
    message_data = json.loads(message)
    logger.info("Received message: %s", message_data)  # Log received message
    chat_messages.append(message_data)

def start_websocket_connection():
    ws = websocket.WebSocketApp(WEBSOCKET_SERVER_URL,
                                on_message=on_message,
                                on_close=on_close)
    ws.run_forever()
    return ws

# Function to handle WebSocket connection close
def on_close(ws):
    # Handle WebSocket connection close
    logger.error("WebSocket connection closed unexpectedly. Reconnecting...")
    time.sleep(3)  # Wait before reconnecting
    start_websocket_connection()

# Function to send message via WebSocket
# Function to send a message through WebSocket
def send_message(ws, sender, message):
    # Format the message to include sender information
    formatted_message = {"sender": sender, "message": message}
    # Convert the message to JSON and send it through WebSocket
    ws.send(json.dumps(formatted_message))

# Main function
def main():
    global chat_messages

    # Generate random user ID
    user_id = str(uuid.uuid4())

    # WebSocket connection

    # Display chat messages
    for message in chat_messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        st.write(f"{avatar}: {message['content']}")

    # Username input
    user_name = st.text_input("Enter your username")

    # Chat input
    new_message = st.text_input("Type your message here:")
    if st.button("Send"):
        ws = start_websocket_connection()

        send_message(ws, user_name, new_message)

    # Save button
    if st.button("Save", key="save_button"):
        # Connect to MongoDB
        client = connect_to_mongodb()

        # Serialize conversation data
        conversation_data = {
            "user_id": user_id,
            "user_name": user_name,
            "role": "user",
            "transcript": chat_messages
        }

        # Save conversation data to MongoDB
        save_to_mongodb(client, "apeiron", "datacorrection", conversation_data)
        st.success("Conversation data saved.")

    # Logout button
    if st.button("Logout"):
        # Clear current user and chat history
        user_name = ""
        chat_messages = []
        st.success("Logged out successfully.")

    # Clear chat history button
    if st.button("Clear chat history"):
        chat_messages = []
        st.success("Chat history cleared.")



# Run this app (local testing: "streamlit run streamlit_app.py")
if __name__ == "__main__":
    main()