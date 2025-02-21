from datetime import datetime
import time
import os 
from dotenv import load_dotenv
import openai
import streamlit as st
from PIL import Image
import streamlit as st
from datetime import datetime
from PIL import Image
import base64
import io

# Initializing session state for username if it doesn't exist
if 'username' not in st.session_state:
    st.session_state.username = 'Guest'

# Initializing session state for bot status if it doesn't exist
if 'botStatus' not in st.session_state:
    st.session_state.botStatus = ['normal']
    
# Initializing session state for bot status if it doesn't exist
if 'useravatar' not in st.session_state:
    st.session_state.useravatar = ['defult']
    
# Loading the .env file
load_dotenv('../.env')

# Accessing the environment variable (access token for openai to run and generate the model)
api_key = os.getenv("GPTa-ACCESS-TOKEN")

# providing the key to the apiKey method in the openai class 
openai.api_key = api_key 


def get_openai_response(request:str):
    try:
            # using OpenAI's GPT-3.5-turbo model
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": request}
                ]
            )

            # Extract and return the assistant's reply from the response
            assistant_reply = response['choices'][0]['message']['content']
            return {"response": assistant_reply}
        # error throw
    except Exception as e:
            st.session_state.botStatus[0] = 'error'
            return f"Sorry {st.session_state.username}, but something went wrong. Please try again later"

# Helper function to convert image to base64 (to embed it in HTML)
def get_image_base64(img_path):
    img = Image.open(img_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to display chat messages with avatars
def display_chat_message(message, avatar_img_path):
    avatar_base64 = get_image_base64(avatar_img_path)
    # Displaing user message with avatar
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{avatar_base64}" width="40" height="40" style="border-radius: 50%; margin-right: 10px;">
            <div>{message}</div>
        </div>
    """, unsafe_allow_html=True)

# function for updating the avater if there is an error or be normal if there is no error by setting post = normal
def avatar_updater(role, post='normal'):
    path = None
    paths_bot = ['../Image_gallery/normalChatbot.jpg','../Image_gallery/errorImage.jpg']
    paths_user = ['../Image_gallery/boy.png','../Image_gallery/girl.png', "../Image_gallery/defult.png" ]
    
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


# MidSection function to display the chat and handle user input
def MidSection():
    # Initializing session state for chat history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # generating the first message of the chatbot to be displayed in the chat box
        bot_message = f"Chatbot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: \n \n Hello \
        {st.session_state.username}, How can I help you today?" 
        st.session_state.chat_history.append(bot_message)

    # Displaing chat input field for user to type their message
    user_msg = st.chat_input('Your message', key='Usermsg')

    # Handling user message and bot response
    if user_msg:
        # Appending user message to chat history only when the message is sent
        user_message_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_message = f"{st.session_state.username} - {user_message_time}: \n \n {user_msg}"
        st.session_state.chat_history.append(user_message)

        # get time and store it in bot_message_time
        bot_message_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            # try and expect block to handle errors and success responses
            st.session_state.botStatus[0] = 'normal'
            # call the openai and plug the usermsg to get the user reponse
            chatbot_response = get_openai_response(user_msg)
            #bot_response = chatbot_response
            # creating the bot message and formatting it
            bot_message = f"Chatbot - {bot_message_time}: \n \n {chatbot_response['response']}"
            # Saving the bot's response to the chat history after the delay
            st.session_state.chat_history.append(bot_message)
            
        except Exception as e:
            # Show a notification of the error and notify the user. (e.g api not givin or unaccessable api)
            st.session_state.botStatus[0] = 'error'
            st.toast("500: Failed to establish a new connection")
            bot_message = f"Chatbot - {bot_message_time}: \n \n Sorry {st.session_state.username}, but something went wrong. Please try again later."
            st.session_state.chat_history.append(bot_message)
            
    # Displaying updated chat history with user's and bot's messages
    for message in st.session_state.chat_history:
        assistant_avatar_path = avatar_updater(role='bot', post=f'{st.session_state.botStatus[0]}')
        User_avatar_path = avatar_updater(role='user', post=f'{st.session_state.useravatar[0]}')
        if "Chatbot" in message:
            # Displaying assistant message with assistant avatar
            display_chat_message(message, assistant_avatar_path)
        else:
            # Displaying user message with user avatar
            display_chat_message(message, User_avatar_path)

# Call the MidSection function to display chat interface
MidSection()

def greeting_effect():
    greetings = ['Hello User', 'How is your day?', 'I hope you are doing well', 'Remember! you are killing it!', 'Smile..', 'Bye Bye..']
    text = st.container()  # Placeholder to update text content
    while True:
        for greet in greetings:
            current_text = ""
            for g in greet:
                current_text += g
                text.text(current_text)  # Update the text displayed in Streamlit
                time.sleep(0.1)  # Delay for the typing effect
            time.sleep(0.5)  # Delay between greetings

#############       #####################################################################################################
#############       #####################################################################################################
#############       THIS SECTION IS THE END OF MID SECTION CHAT BOX AND IT CAN BE MODIFED AND EXTNED LONGER BUT MUST NOT
#############       ######################################################################################################
#############       CONFLICT WITH THE FOLLOWING SECTIONS AS EACH SECTION SHOULD HAVE ITS OWN SPACE TO STAY
#############       #####################################################################################################
#############       ORGANISABLE AND FIND WHATEVER WE WANT QUICKER AND FASTER. THANK YOU
#########################################################################################################################


#########################################################################################################################
#########################################################################################################################

#############       THIS SECTION IS THE START OF BUTTONS OPS SECTION AND IT CAN BE MODIFED AND EXTNED LONGER BUT MUST NOT
#############       #####################################################################################################
#############       CONFLICT WITH THE FOLLOWING SECTIONS AS EACH SECTION SHOULD HAVE ITS OWN SPACE TO STAY
#############       #####################################################################################################
#############       ORGANISABLE AND FIND WHATEVER WE WANT QUICKER AND FASTER. THANK YOU
#############       #####################################################################################################
          
#greeting_effect()
 
def button_ops_section():
    st.sidebar.image('../Image_gallery/g2.gif')
    st.sidebar.header("Chat Options:")
    st.sidebar.header("Upload PDF file")
    button_upload = st.sidebar.button(':material/file_upload: Upload')
    # If the button with the icon is clicked, open the sidebar
    st.sidebar.header("I am a:")
    
    # Create checkboxes for interaction inside the sidebar
    selection_boy = st.sidebar.checkbox(":material/male: Male", key='boy_echbox')
    selection_girl = st.sidebar.checkbox(":material/female: Female", key='girl_echbox')
    if selection_boy and selection_girl:
       st.session_state.useravatar[0] = 'defult'
       st.rerun()

    if selection_boy:
        st.session_state.useravatar[0] = 'boy'
        st.sidebar.success("updated successfully..")
        st.rerun()
    if selection_girl:
        st.session_state.useravatar[0] = 'girl'
        st.sidebar.success("updated successfully..")
        st.rerun()
        
    
button_ops_section()
 


#############       #############################################################################################
#############       #############################################################################################
#############       THIS SECTION IS THE END OF BUTTONS OPS AND IT CAN BE MODIFED AND EXTNED LONGER BUT MUST NOT
#############       #############################################################################################
#############       CONFLICT WITH THE FOLLOWING SECTIONS AS EACH SECTION SHOULD HAVE ITS OWN SPACE TO STAY
#############       #############################################################################################
#############       ORGANISABLE AND FIND WHATEVER WE WANT QUICKER AND FASTER. THANK YOU
#################################################################################################################