import requests

# Defining the FastAPI URLs (this would be local or hosted) as long as we have it up and running we could deine 
# the urls here for the Fastapi
CHAT_PUTS_URL = "http://localhost:8000/chat/"

# function to hundle assistant response 
def get_openai_response(messages):
    payload = {
        "messages": [
            {"role": m["role"], "content": m["content"], "time": m["time"]}
            for m in messages
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    # Making the POST request to the FastAPI server (which will forward to OpenAI)
    stream = requests.post(CHAT_PUTS_URL, json=payload, headers=headers)
    
    # Check if the status code is OK (200)
    if stream.status_code == 200:
        response = stream.json() 
        # Extract the reply safely
        reply = response.get("reply", "No reply found")  
        print(f"res: {reply}")
        return reply
    else:
        return f"Error: {stream.status_code}, {stream.text}"