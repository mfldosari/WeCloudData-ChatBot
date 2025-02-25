from datetime import datetime
import time
import streamlit as st
from PIL import Image
import streamlit as st
from datetime import datetime
from PIL import Image
import base64
import io

from chatbot_request import get_openai_response

# Initializing session state for username if it doesn't exist
if 'username' not in st.session_state:
    st.session_state.username = 'User'
    
# Initializing session state for chat name if it doesn't exist
if 'current_chat_name' not in st.session_state:
    st.session_state.current_chat_name = 'untitled chat'

# Initializing session state for bot status if it doesn't exist
if 'botStatus' not in st.session_state:
    st.session_state.botStatus = 'normal'
    
# Initializing session state for bot status if it doesn't exist
if 'useravatar' not in st.session_state:
    st.session_state.useravatar = 'defult'
     

# Helper function to convert image to base64 (to embed it in HTML)
def get_image_base64(img_path):
    img = Image.open(img_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to display chat messages with avatars
def display_chat_message(message, avatar_img_path):
    avatar_base64 = get_image_base64(avatar_img_path)
    # Displaing user and chatbot message with avatar
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{avatar_base64}" width="40" height="40" style="border-radius: 50%; margin-right: 10px;">
            <div> {message} </div>
        </div>
    """, unsafe_allow_html=True)

# function for updating the avater if there is an error or be normal if there is no error by setting post = normal
def avatar_updater(role, post='normal'):
    path = None
    paths_bot = ['Image_gallery/normalChatbot.jpg','Image_gallery/errorImage.jpg']
    paths_user = ['Image_gallery/boy.png','Image_gallery/girl.png', "Image_gallery/defult.png" ]
    
    if role == 'bot':
        if post=='error':
           path = paths_bot[1]
        else:
           path = paths_bot[0]
    else:
        if post == 'defult':
            path = paths_user[2]
        elif post =='boy':
           path = paths_user[0]
        else:
           path = paths_user[1]
         
    return path

bot_response_time = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
# MidSection function to display the chat area and handle user input
def MidSection():
    # Initializing session state for chat history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # generating the first message of the chatbot to be displayed in the chat box
        bot_msg = f"Hello {st.session_state.username}, How can I help you today?" 
        st.session_state.chat_history.append({"role": "assistant", "content": bot_msg, "time":bot_response_time})

    # Displaing chat input field for user to type their message
    user_msg = st.chat_input('Your message', key='Usermsg')

    # Handling user message and bot response
    if user_msg:
        # Appending user message to chat history only when the message is sent
        user_message_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.session_state.chat_history.append({"role": "user", "content": user_msg, "time":user_message_time})

        try:
            # try and expect block to handle errors and success responses
            st.session_state.botStatus = 'normal'
            # call the openai and plug the chat_history to get the chatbot reponse
            chatbot_response = get_openai_response(st.session_state.chat_history)
            # Saving the bot's response to the chat history after the delay
            st.session_state.chat_history.append({"role": "assistant", "content": chatbot_response, "time":bot_response_time})
            
        except Exception as e:
            # Show a notification of the error and notify the user. (e.g api not givin or unaccessable api)
            st.session_state.botStatus = 'error'
            st.toast("500: Failed to establish a new connection")
            chatbot_response = f"Sorry {st.session_state.username}, but something went wrong. Please try again later."
            st.session_state.chat_history.append({"role": "assistant", "content": chatbot_response, "time":bot_response_time})

            
    # Displaying updated chat history with user's and bot's messages
    for messages in st.session_state.chat_history:
        assistant_avatar_path = avatar_updater(role='bot', post=f'{st.session_state.botStatus[0]}')
        User_avatar_path = avatar_updater(role='user', post=f'{st.session_state.useravatar[0]}')
        if "assistant" == messages['role']:
            # Displaying assistant message with assistant avatar
            message = f" {messages['time']}: \n \n  {messages['content']} <br>"
            display_chat_message(message, assistant_avatar_path)
        else:
            message = f" {messages['time']}:\n \n  {messages['content']} <br> "
            # Displaying user message with user avatar
            display_chat_message(message, User_avatar_path)

# Call the MidSection function to display chat interface
MidSection()
# Side Bar section:
def button_ops_section():
    #creating some elements such as title, caption, checkboxes and a buttons
    st.sidebar.title("Chat Options:")
    
    # Creating columns to display buttons horizontally
    col1, col2, col3 = st.sidebar.columns(3)
    # delete button for deleting a current chat or stored chats
    with col1:
        delete_chat = st.button(':material/delete:')
    #add new button, to add a new chat and store it if needed
    with col2:
        add_new_chat = st.button(':material/add:')
    # loading old chats button to load chats that were stored in the storage
    with col3:
        load_prev_chat = st.button(':material/search:')
    
    # section to rename and name the current chat
    st.sidebar.caption("Current Chat Name:")
    name_input = st.sidebar.chat_input(f"{st.session_state.current_chat_name}")
    # section to upload pdf
    st.sidebar.caption("Upload PDF file")
    button_upload = st.sidebar.button(':material/file_upload: Upload')
    # section to chnage gendre (not necessary and could be deleted, if decided to delete make sure to delete its related functio too)
    st.sidebar.caption("I am a:")
    selection_boy = st.sidebar.checkbox(":material/male: Male", key='boy_echbox')
    selection_girl = st.sidebar.checkbox(":material/female: Female", key='girl_echbox')

    #if condition block to handle clikcing and entering a name
    if selection_boy and selection_girl:
       st.session_state.useravatar = 'defult'
       st.rerun()
    if selection_boy:
        st.session_state.useravatar = 'boy'
        st.rerun()
    if selection_girl:
        st.session_state.useravatar = 'girl'
        st.rerun()
    if name_input:
        st.session_state.current_chat_name = name_input
        with st.spinner('renaming new chat..'):
            time.sleep(1)  
        st.success(f"Good News, Chat named as ({name_input}) successfully..")
        st.rerun()
 
        
button_ops_section()
