import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Loading the .env file
load_dotenv('.env')

# Accessing the environment variable (access token for openai to run and generate the model)
# providing the key to the apiKey method in the openai class 
openai.api_key = os.getenv("GPT-ACCESS-TOKEN") 

# generating a CRUD ops web with fastapi framework and test the api with Swagger UI
app = FastAPI()


# creating an endpoint for communicating with chatgpt and returning a response. also generating a gpt model
# in this case we used gpt-3.5-turbo. why? becouse it is cheaper and only used for testing but for bigger project
# the best moodel option would be version 4 or other.
model = "gpt-3.5-turbo"

# request model
class ChatRequest(BaseModel):
    messages: list

@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=request.messages,
            # stream=True,
        )
        # if you don't want to stream the output
        # set the stream parameter to False in above function
        # and uncommnet the belowing line
        return {"reply": response.choices[0].message.content}

        # Function to send out the stream data
        # def stream_response():
        #     for chunk in stream:
        #         delta = chunk.choices[0].delta.content
        #         if delta:
        #             yield delta

        # Use StreamingResponse to return
        # return StreamingResponse(stream_response(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # importing uvicorn to run and deploy the fastapi
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
