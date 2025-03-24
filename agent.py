from openai import OpenAI
import os
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, FileSearchTool
from typing import List, Optional
import json

# Load environment variables from .env file
load_dotenv()

# Get the API key and vector store ID from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# initialize the OpenAI client for vector store API calls
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

# initialize the OpenAI agent, configure it for filesearch and specify the vector store at OpenAI
game_agent = Agent(
    name="Game agent",
    instructions="You only answer questions about D&D with data from the file search tool",
    tools=[
        FileSearchTool(
                max_num_results=2,
                vector_store_ids=[VECTOR_STORE_ID],
        ),
    ]
)

# initialize FastAPI app
app = FastAPI()

# mount static files directory - where the HTML page is
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define a request model for the chat endpoint
class ChatRequest(BaseModel):
    message: str
    temperature: float = 1.0

# Model for vector store operations
class VectorStoreRequest(BaseModel):
    name: str
    description: Optional[str] = None

# Model for file deletion
class FileDeleteRequest(BaseModel):
    file_ids: List[str]
    vector_store_id: str

# quick test message at root
@app.get("/")
async def root():
    return {"message": "Hello World"}

# this app serves up the API endpoint and calls the OpenAI agent to get a response
@app.post("/chat")
async def chat(request: ChatRequest):
    result = await Runner.run(game_agent, input=request.message)
    return {"response": result.final_output}

# this app serves up the HTML page
@app.get("/webchat")
async def get_chat_page():
    return FileResponse("static/index.html")

# Admin page endpoint
@app.get("/admin")
async def get_admin_page():
    return FileResponse("static/admin.html")

# Vector store management endpoints
@app.get("/storage-admin/vector-stores")
async def list_vector_stores():
    try:
        response = client.vector_stores.list()
        return {"vector_stores": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage-admin/vector-stores")
async def create_vector_store(request: VectorStoreRequest):
    try:
        response = client.vector_stores.create(
            name=request.name,
            description=request.description
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/storage-admin/vector-stores/{vector_store_id}")
async def delete_vector_store(vector_store_id: str):
    try:
        response = client.vector_stores.delete(vector_store_id=vector_store_id)
        return {"success": True, "message": f"Vector store {vector_store_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage-admin/vector-stores/{vector_store_id}/files")
async def upload_file(vector_store_id: str, file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload the file to OpenAI vector store
        with open(temp_file_path, "rb") as f:
            response = client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file=f
            )
            
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        return response
    except Exception as e:
        # Clean up the temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage-admin/vector-stores/{vector_store_id}/files")
async def list_files(vector_store_id: str):
    try:
        # Get the list of files in the vector store
        response = client.vector_stores.files.list(vector_store_id=vector_store_id)
        
        # Return the file data directly without additional processing
        return {"files": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/storage-admin/files")
async def delete_files(request: FileDeleteRequest):
    try:
        results = []
        for file_id in request.file_ids:
            response = client.vector_stores.files.delete(
                vector_store_id=request.vector_store_id,
                file_id=file_id
            )
            results.append({"file_id": file_id, "success": True})
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))