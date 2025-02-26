from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os


load_dotenv('./.env')

client = OpenAI(api_key=os.environ.get("GPT-ACCESS-TOKEN"))
model = "gpt-3.5-turbo"

app = FastAPI()

# request model
class ChatRequest(BaseModel):
    messages: list

@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
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
