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

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

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


# Function to connect to MongoDB instance
def connect_to_mongodb():
    # url = "mongodb://localhost:27017/" LOCAL
    url = "mongodb+srv://phillipandrewespina:Firiyuu77@cluster0.gvlsxm5.mongodb.net/"
    client = pymongo.MongoClient(url)
    return client

# Function to save conversation data to MongoDB
# Function to save conversation data to MongoDB
def save_to_mongodb(client, database_name, collection_name, data):
    db = client[database_name]
    collection = db[collection_name]
    collection.insert_one(data)


def interact_with_voiceflow(user_id, user_message):
    voiceflow_api_key = "VF.DM.65aa7ba36894de0007bad42e.50qQAVpQyapvOmMI"
    user_id.replace("-", "")
    #User message into string
    print(user_message[0]["content"])
    body = {"action": {"type": "text", "payload": user_message[0]["content"]}}

    url = f"https://general-runtime.voiceflow.com/state/user/{user_id}/interact?logs=off"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": voiceflow_api_key
    }

    response = requests.post(
        url,
        json=body,
        headers=headers,
    )


    # Extracting the 'payload' field from the second item in the list
    payload = response.json()
    chatbot_response = ""
    # Loop through the payload
    for item in payload:
        # Check if 'slate' key exists in the current item
        if 'payload' in item:
            new_item = item["payload"]
            if 'slate' in new_item:
                # Extracting the 'slate' field from the current item
                slate = new_item['slate']
                # Extracting the 'content' field from the 'slate'
                content = slate['content']
                for content_item in content:
                    # Extracting the 'text' field from the 'content'
                    if 'children' in content_item:
                        if len(content_item['children']) > 0:
                            for i in range(len(content_item['children'])):
                                text = content_item['children'][i].get('text', '')
                                # Concatenate the extracted text to the chatbot response string
                                chatbot_response += text + " \n"
        else:
            # If 'slate' key doesn't exist, continue to the next item
            continue

    # Display chatbot response
    # print(chatbot_response)
    return chatbot_response



def main():
    # Generate random user ID

    # Initialize user ID
    # Initialize user ID
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())

    # Initialize disabled state
    if "disabled" not in st.session_state:
        st.session_state["disabled"] = False

    # Function to disable the input
    def disable_username_input():
        st.session_state["disabled"] = True

    # Username input
    user_name = st.text_input("Enter your username", disabled=st.session_state.disabled,
                              on_change=disable_username_input)
    
    #Get users collection
    client = connect_to_mongodb()
    db = client["apeiron"]
    #Get all user name via list on user column
    users = db.users.distinct("user")
    allowed_users = users

    # Change user ID upon history clear or logout
    if st.session_state.get("clear_chat_history") or st.session_state.get("logout"):
        st.session_state["user_id"] = str(uuid.uuid4())

    if user_name in allowed_users and st.session_state["disabled"]:
        head_col = st.columns([1, 8])
        with head_col[0]:
            st.image(project_icon)
        with head_col[1]:
            st.title(project_title)

        # Hide text input "Enter your username"
        st.markdown(f"Welcome, {user_name}!")

        st.write(project_desc)
        expander = st.expander("Additional Information")
        expander.markdown(add_info_md)
        bot_background = ""
        show_edit = st.checkbox("Show Edit Section")

        if show_edit:
            with st.expander("Edit Messages"):
                bot_background = st.text_input("Enter the bot's background (optional)")
                for i, message in enumerate(st.session_state.messages):
                    if message["content"] != "":
                        with st.form(key=f"form{i}"):
                            st.write(message["role"])
                            new_content = st.text_area("Content", value=message["content"], key=f"content{i}")
                            st.form_submit_button("Update")
                            if new_content != message["content"]:
                                st.session_state.messages[i]["content"] = new_content
                                st.session_state.messages[i]["bot_background"] = bot_background

        for message in st.session_state.messages:
            avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])



        if prompt := st.chat_input("Enter message here:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt)

            assistant_responses = interact_with_voiceflow(st.session_state["user_id"], st.session_state["messages"])
            assistant_responses = assistant_responses.split("\n")

            for response in assistant_responses:
                if response.strip() != "":
                    with st.chat_message("assistant", avatar=BOT_AVATAR):
                        message_placeholder = st.empty()
                        full_response = ""

                        st.session_state.messages.append({"role": "assistant", "content": response})
                        message_placeholder.markdown(response)

        # Logout button
        if st.button("Logout"):
            # Set logout flag
            st.session_state["logout"] = True
            # Clear current user and hide interface
            st.session_state["disabled"] = False
            st.session_state.messages = []
            # Refresh page
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

        # Clear chat history button (visible only when logged in)
        if st.session_state["disabled"] and st.button("Clear chat history"):
            # Set clear chat history flag
            st.session_state["clear_chat_history"] = True
            st.session_state.messages = []
            st.success("Chat history cleared.")


        # Save button (visible only when logged in)
        if st.session_state["disabled"] and st.button("Save", key="save_button"):
            # Connect to MongoDB

            # Serialize conversation data
            conversation_data = {
                "user_id": st.session_state["user_id"],
                "user_name": user_name,
                "role": "staff",  # Assuming staff role for the user
                "transcript": st.session_state.messages,
                "bot_background": bot_background if bot_background else ""  # Empty if not provided
            }

            # Save conversation data to MongoDB
            save_to_mongodb(client, "apeiron", "datacorrection", conversation_data)
            st.success("Conversation data saved.")


    else:
        st.warning("Sorry, you are not authorized to access this interface.")





# Run this app (local testing: "streamlit run streamlit_app.py")
if __name__ == "__main__":
    main()