import streamlit as st
from datetime import datetime
from PIL import Image
import base64
import io
import requests
import uuid

# Initialize session state
if "history_chats" not in st.session_state:
    st.session_state["history_chats"] = []  # List of chats: [{"id": "chat_id", "messages": [...]}, ...]
if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = None  # ID of the current chat
if "chat_names" not in st.session_state:
    st.session_state["chat_names"] = {}  # Dictionary mapping chat IDs to names
if "useravatar" not in st.session_state:
    st.session_state["useravatar"] = "default"  # User's avatar selection

# Helper functions
def get_image_base64(img_path):
    """Convert an image to base64 for embedding (if needed)."""
    img = Image.open(img_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def avatar_updater(role, post="normal"):
    """Determine the avatar image path based on role and status."""
    paths_bot = ["Image_gallery/normalChatbot.jpg", "Image_gallery/errorImage.jpg"]
    paths_user = ["Image_gallery/boy.png", "Image_gallery/girl.png", "Image_gallery/defult.png"]
    
    if role == "bot":
        return paths_bot[1] if post == "error" else paths_bot[0]
    else:
        if post == "boy":
            return paths_user[0]
        elif post == "girl":
            return paths_user[1]
        else:
            return paths_user[2]

# Chat management functions
def load_chats_from_db():
    """Load existing chats from the backend database."""
    response = requests.get("http://127.0.0.1:8000/load_chat/")
    if response.status_code == 200:
        records = response.json()
        for record in records:
            chat_id = record["id"]
            messages = record["messages"]
            name = record["chat_name"]
            st.session_state["history_chats"].append({"id": chat_id, "messages": messages})
            st.session_state["chat_names"][chat_id] = name
    else:
        st.toast(f"Failed to load chats. Status code: {response.status_code}")

def save_chat_to_db(chat_id, chat_name, messages):
    """Save a chat to the backend database."""
    payload = {"chat_id": chat_id, "chat_name": chat_name, "messages": messages}
    headers = {"Content-Type": "application/json"}
    response = requests.post("http://127.0.0.1:8000/save_chat/", json=payload, headers=headers)
    if response.status_code != 200:
        st.toast(f"Failed to save chat. Status code: {response.status_code}")

def create_chat(chat_name):
    """Create a new chat with an initial bot message."""
    new_chat_id = str(uuid.uuid4())
    initial_message = {
        "role": "assistant",
        "content": "Hello, How can I help you today?",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "normal"
    }
    new_chat = {"id": new_chat_id, "messages": [initial_message]}
    st.session_state["history_chats"].insert(0, new_chat)
    st.session_state["chat_names"][new_chat_id] = chat_name
    st.session_state["current_chat"] = new_chat_id
    save_chat_to_db(new_chat_id, chat_name, [initial_message])

def delete_chat():
    """Delete the current chat from session state and database."""
    if st.session_state["current_chat"]:
        chat_id = st.session_state["current_chat"]
        st.session_state["history_chats"] = [
            chat for chat in st.session_state["history_chats"] if chat["id"] != chat_id
        ]
        del st.session_state["chat_names"][chat_id]
        payload = {"chat_id": chat_id}
        headers = {"Content-Type": "application/json"}
        response = requests.post("http://127.0.0.1:8000/delete_chat/", json=payload, headers=headers)
        if response.status_code != 200:
            st.toast(f"Failed to delete chat. Status code: {response.status_code}")
        st.session_state["current_chat"] = (
            st.session_state["history_chats"][0]["id"] if st.session_state["history_chats"] else None
        )

def select_chat(chat_id):
    """Select a chat by its ID."""
    st.session_state["current_chat"] = chat_id

def get_current_messages():
    """Retrieve messages of the current chat."""
    if st.session_state["current_chat"]:
        for chat in st.session_state["history_chats"]:
            if chat["id"] == st.session_state["current_chat"]:
                return chat["messages"]
    return []

# Load existing chats
load_chats_from_db()

# Sidebar
with st.sidebar:
    st.title("Chat Options")

    # Create new chat
    chat_name = st.text_input("Enter Chat Name:", key="new_chat_name")
    if st.button("Create New Chat"):
        if chat_name.strip():
            create_chat(chat_name.strip())
        else:
            st.toast("Chat name cannot be empty.")

    # Select existing chat
    if st.session_state["history_chats"]:
        chat_options = {
            chat["id"]: st.session_state["chat_names"][chat["id"]]
            for chat in st.session_state["history_chats"]
        }
        default_index = 0
        if st.session_state["current_chat"] in chat_options:
            default_index = list(chat_options.keys()).index(st.session_state["current_chat"])
        selected_chat = st.radio(
            "Select Chat",
            options=list(chat_options.keys()),
            format_func=lambda x: chat_options[x],
            index=default_index,
            key="chat_selector",
        )
        if selected_chat != st.session_state["current_chat"]:
            select_chat(selected_chat)

    # Delete current chat
    if st.session_state["current_chat"]:
        if st.button("Delete Chat"):
            delete_chat()

    # Upload PDF
    st.caption("Upload PDF file")
    button_upload = st.button(":material/file_upload: Upload")
    # Add PDF upload logic here if needed

    # Select gender for user avatar
    st.caption("I am a:")
    selection_boy = st.checkbox(":material/male: Male", key="boy_echbox")
    selection_girl = st.checkbox(":material/female: Female", key="girl_echbox")
    if selection_boy and selection_girl:
        st.session_state["useravatar"] = "default"
    elif selection_boy:
        st.session_state["useravatar"] = "boy"
    elif selection_girl:
        st.session_state["useravatar"] = "girl"
    else:
        st.session_state["useravatar"] = "default"

# Main Content
st.title("Chatbot Application")

if st.session_state["current_chat"]:
    chat_id = st.session_state["current_chat"]
    chat_name = st.session_state["chat_names"][chat_id]
    st.subheader(f"Current Chat is => {chat_name}")

    current_messages = get_current_messages()

    # Display chat history with avatars
    for message in current_messages:
        role = message["role"]
        content = message["content"]
        timestamp = message.get("time", "")
        if role == "assistant":
            status = message.get("status", "normal")
            avatar_path = avatar_updater(role="bot", post=status)
        else:
            avatar_path = avatar_updater(role="user", post=st.session_state["useravatar"])
        avatar_img = Image.open(avatar_path)
        with st.chat_message(role, avatar=avatar_img):
            st.markdown(f"{timestamp}: {content}")

    # Handle user input
    if user_msg := st.chat_input("Enter your message", key="user_chat_entry"):
        user_message_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_messages.append({"role": "user", "content": user_msg, "time": user_message_time})
        save_chat_to_db(chat_id, chat_name, current_messages)

        try:
            # Send message to backend and stream response
            payload = {
                "messages": [{"role": m["role"], "content": m["content"]} for m in current_messages]
            }
            headers = {"Content-Type": "application/json"}

            def get_stream_response():
                with requests.post("http://127.0.0.1:8000/chat/", json=payload, headers=headers, stream=True) as r:
                    for chunk in r:
                        yield chunk.decode("utf-8")

            response = st.write_stream(get_stream_response)
            bot_response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_messages.append({
                "role": "assistant",
                "content": response,
                "time": bot_response_time,
                "status": "normal"
            })
            save_chat_to_db(chat_id, chat_name, current_messages)
        except Exception as e:
            error_msg = "\n Sorry, but something went wrong. Please try again later."
            bot_response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_messages.append({
                "role": "assistant",
                "content": error_msg,
                "time": bot_response_time,
                "status": "error"
            })
            save_chat_to_db(chat_id, chat_name, current_messages)
            st.toast("500: Failed to establish a new connection")
else:
    st.write("No chat selected. Use the sidebar to create or select a chat.")