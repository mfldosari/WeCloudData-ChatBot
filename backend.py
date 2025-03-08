import os
import json
import psycopg2
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from azure.storage.blob import BlobServiceClient
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Azure Blob Storage setup
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client("chatbot-storage")

# OpenAI and LangChain setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vector_store = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# Database connection dependency
def get_db():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models for request/response validation
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str

class RAGChatRequest(BaseModel):
    question: str
    chat_history: List[Message]

class SaveChatRequest(BaseModel):
    chat_id: str
    chat_name: str
    messages: List[Message]
    pdf_name: str = None
    pdf_path: str = None
    pdf_uuid: str = None

class DeleteChatRequest(BaseModel):
    chat_id: str

# FastAPI Endpoints

## Basic Chat Endpoint
@app.post("/chat/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle a simple chat request using the LLM."""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    response = llm.invoke(messages)
    return {"response": response.content}

## Load All Chats
@app.get("/load_chat/")
async def load_chat(db: psycopg2.extensions.connection = Depends(get_db)):
    """Load all chat records from the database and Azure Blob Storage."""
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT id, name, file_path, pdf_name, pdf_path, pdf_uuid FROM advanced_chats ORDER BY last_update DESC")
        rows = cursor.fetchall()

    records = []
    for row in rows:
        chat_id = row["id"]
        name = row["name"]
        chat_blob_name = row["file_path"]
        pdf_name = row["pdf_name"]
        pdf_blob_name = row["pdf_path"]
        pdf_uuid = row["pdf_uuid"]

        try:
            # Handle legacy local file paths
            if not chat_blob_name.startswith("chats/"):
                new_chat_blob_name = f"chats/{chat_id}.json"
                local_file_path = chat_blob_name
                if os.path.exists(local_file_path):
                    with open(local_file_path, "rb") as f:
                        blob_client = container_client.get_blob_client(new_chat_blob_name)
                        blob_client.upload_blob(f, overwrite=True)
                    with db.cursor() as cursor:
                        cursor.execute("UPDATE advanced_chats SET file_path = %s WHERE id = %s", (new_chat_blob_name, chat_id))
                    db.commit()
                    chat_blob_name = new_chat_blob_name
                else:
                    messages = []
            else:
                blob_client = container_client.get_blob_client(chat_blob_name)
                if blob_client.exists():
                    download_stream = blob_client.download_blob()
                    messages = json.loads(download_stream.readall())
                else:
                    messages = []
        except Exception as e:
            print(f"Error loading chat {chat_id}: {str(e)}")
            messages = []

        records.append({
            "id": chat_id,
            "chat_name": name,
            "messages": messages,
            "pdf_name": pdf_name,
            "pdf_path": pdf_blob_name,
            "pdf_uuid": pdf_uuid
        })

    return records

## Save a Chat
@app.post("/save_chat/")
async def save_chat(request: SaveChatRequest, db: psycopg2.extensions.connection = Depends(get_db)):
    """Save a chat to Azure Blob Storage and update the database."""
    chat_id = request.chat_id
    chat_name = request.chat_name
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    pdf_name = request.pdf_name
    pdf_path = request.pdf_path
    pdf_uuid = request.pdf_uuid

    chat_blob_name = f"chats/{chat_id}.json"
    blob_client = container_client.get_blob_client(chat_blob_name)
    blob_client.upload_blob(json.dumps(messages), overwrite=True)

    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO advanced_chats (id, name, file_path, pdf_name, pdf_path, pdf_uuid)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET name = %s, file_path = %s, pdf_name = %s, pdf_path = %s, pdf_uuid = %s, last_update = CURRENT_TIMESTAMP
            """, (chat_id, chat_name, chat_blob_name, pdf_name, pdf_path, pdf_uuid,
                  chat_name, chat_blob_name, pdf_name, pdf_path, pdf_uuid))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving chat: {str(e)}")

@app.post("/delete_chat/")
async def delete_chat(request: DeleteChatRequest, db: psycopg2.extensions.connection = Depends(get_db)):
    """Delete a chat, its history blob, and associated PDF blob from Azure Blob Storage and the database."""
    chat_id = request.chat_id
    try:
        # Step 1: Fetch chat and PDF blob names from the database
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT file_path, pdf_path FROM advanced_chats WHERE id = %s", (chat_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Chat not found")
            chat_blob_name = row["file_path"]  # Chat history blob name
            pdf_blob_name = row["pdf_path"]    # PDF blob name

        # Step 2: Delete the chat history blob
        if chat_blob_name:
            chat_blob_client = container_client.get_blob_client(chat_blob_name)
            if chat_blob_client.exists():
                chat_blob_client.delete_blob()
                print(f"Chat blob {chat_blob_name} deleted successfully.")
            else:
                print(f"Chat blob {chat_blob_name} does not exist.")

        # Step 3: Delete the PDF blob
        if pdf_blob_name:
            pdf_blob_client = container_client.get_blob_client(pdf_blob_name)
            if pdf_blob_client.exists():
                pdf_blob_client.delete_blob()
                print(f"PDF blob {pdf_blob_name} deleted successfully.")
            else:
                print(f"PDF blob {pdf_blob_name} does not exist in Azure Blob Storage.")
        else:
            print("No PDF blob name found for this chat in the database.")

        # Step 4: Delete the database record
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM advanced_chats WHERE id = %s", (chat_id,))
        db.commit()

        return {"status": "success"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

## RAG Chat Endpoint
@app.post("/rag_chat/", response_model=ChatResponse)
async def rag_chat(request: RAGChatRequest):
    """Handle a RAG-based chat request using retrieved context and chat history."""
    question = request.question
    chat_history = [{"role": m.role, "content": m.content} for m in request.chat_history]

    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    template = """Use the following pieces of context to answer the question. If you don't know the answer, just say that you don't know. Don't try to make up an answer.

    Context: {context}

    Chat History: {chat_history}

    Question: {question}

    Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough(), "chat_history": lambda x: json.dumps(chat_history)}
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke(question)
    return {"response": response}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)