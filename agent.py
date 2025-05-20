import os
import sys
import yaml
import json
import traceback
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from agents import Agent, Runner, WebSearchTool, FileSearchTool
from agents import set_default_openai_key
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

# ==========================================================
# Configuration and Initialization
# ==========================================================

# Load configuration from config.yaml
def load_config():
    config_path = "config.yaml"
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        default_config = {
            "openai": {
                "api_key": "",
                "vector_store_id": ""
            },
            "assistant": {
                "name": "AI Assistant"
            }
        }
        with open(config_path, "w") as file:
            yaml.dump(default_config, file)
        return default_config
    
    # Load existing config
    with open(config_path, "r") as file:
        config = yaml.safe_load(file) or {}
        
    # Ensure assistant section exists
    if "assistant" not in config:
        config["assistant"] = {
            "name": "AI Assistant"
        }
        with open(config_path, "w") as file:
            yaml.dump(config, file)
    
    return config

config = load_config()

# Get the API key and vector store ID from config
OPENAI_API_KEY = config.get("openai", {}).get("api_key")
set_default_openai_key(OPENAI_API_KEY)
VECTOR_STORE_ID = config.get("openai", {}).get("vector_store_id")

# Initialize the OpenAI client for API calls
client = OpenAI(api_key=OPENAI_API_KEY)

# Rename the existing function to create_rag_agent
def create_rag_agent(vector_store_id):
    # Get assistant name from config
    config = load_config()
    assistant_name = config.get("assistant", {}).get("name", "AI Assistant")
    
    return Agent(
        name=f"{assistant_name} Document Expert",
        instructions="You are a knowledgeable assistant that only answers questions from the files contained in the file search tool. If the information isn't found in the documents, clearly state that you don't have that information.",
        tools=[
            FileSearchTool(
                max_num_results=30,
                vector_store_ids=[vector_store_id],
            ),
        ]
    )

# Create the document agent instance
doc_agent = create_rag_agent(VECTOR_STORE_ID)

# Create the orchestrator agent directly (similar to orchestrator.py)
orchestrator_agent = Agent(
    name=load_config().get("assistant", {}).get("name", "AI Assistant"),
    instructions=prompt_with_handoff_instructions("""
You are a helpful virtual assistant who can answer questions based on the available documents.
When a user asks about information that might be in the documents, route their question to the document expert.
Be friendly and concise in your responses.
    """),
    handoffs=[doc_agent],
)

# Initialize FastAPI app
app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================
# Pydantic Models
# ==========================================================

class ChatRequest(BaseModel):
    message: str
    temperature: float = 1.0

class VectorStoreRequest(BaseModel):
    name: str

class FileDeleteRequest(BaseModel):
    file_ids: List[str]
    vector_store_id: str

class ApiKeyRequest(BaseModel):
    api_key: str

class VectorStoreIdRequest(BaseModel):
    vector_store_id: str

class AssistantNameRequest(BaseModel):
    assistant_name: str

# ==========================================================
# Basic Navigation Endpoints
# ==========================================================

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/webchat")
async def get_chat_page():
    return FileResponse("static/index.html")

@app.get("/admin")
async def get_admin_page():
    return FileResponse("static/admin.html")


# ==========================================================
# Chat/Assistant Endpoints
# ==========================================================

@app.post("/chat")
async def chat(request: ChatRequest):
    # Use orchestrator_agent instead of doc_agent
    result = await Runner.run(orchestrator_agent, input=request.message)
    return {"response": result.final_output}

# ==========================================================
# Configuration Management Endpoints
# ==========================================================

@app.get("/storage-admin/config")
async def get_config():
    try:
        # Return API key (masked) and vector store ID for security
        api_key = OPENAI_API_KEY
        masked_key = "•" * (len(api_key) - 8) + api_key[-8:] if api_key else ""
        
        # Get assistant name from config
        config = load_config()
        assistant_name = config.get("assistant", {}).get("name", "AI Assistant")
        
        return {
            "api_key": masked_key,
            "vector_store_id": VECTOR_STORE_ID,
            "assistant_name": assistant_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage-admin/config")
async def update_config(request: ApiKeyRequest):
    try:
        global OPENAI_API_KEY
        global client
        
        # Update the config file
        config_path = "config.yaml"
        
        # Read existing config
        with open(config_path, "r") as file:
            config = yaml.safe_load(file) or {}
            
        # Make sure we have the openai section
        if "openai" not in config:
            config["openai"] = {}
            
        # Update the API key
        config["openai"]["api_key"] = request.api_key
        
        # Save the updated config
        with open(config_path, "w") as file:
            yaml.dump(config, file)
            
        # Update the global variables and client
        OPENAI_API_KEY = request.api_key
        set_default_openai_key(OPENAI_API_KEY)
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        return {"status": "success", "message": "API key updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage-admin/config/vector-store")
async def update_vector_store_id(request: VectorStoreIdRequest):
    try:
        global VECTOR_STORE_ID
        global doc_agent
        global orchestrator_agent
        
        # Update the config file
        config_path = "config.yaml"
        
        # Read existing config
        with open(config_path, "r") as file:
            config = yaml.safe_load(file) or {}
            
        # Make sure we have the openai section
        if "openai" not in config:
            config["openai"] = {}
            
        # Update the vector store ID
        config["openai"]["vector_store_id"] = request.vector_store_id
        
        # Save the updated config
        with open(config_path, "w") as file:
            yaml.dump(config, file)
            
        # Update the global variables
        VECTOR_STORE_ID = request.vector_store_id
        
        # Update the doc agent with the new vector store ID
        doc_agent = create_rag_agent(VECTOR_STORE_ID)
        
        # Update the orchestrator agent with the new doc_agent
        orchestrator_agent = Agent(
            name=config.get("assistant", {}).get("name", "AI Assistant"),
            instructions=prompt_with_handoff_instructions("""
You are a helpful virtual assistant who can answer questions based on the available documents.
When a user asks about information that might be in the documents, route their question to the document expert.
Be friendly and concise in your responses.
            """),
            handoffs=[doc_agent],
        )
        
        return {"status": "success", "message": "Vector store ID updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage-admin/config/assistant-name")
async def update_assistant_name(request: AssistantNameRequest):
    try:
        global orchestrator_agent
        global doc_agent
        
        # Update the config file
        config_path = "config.yaml"
        
        # Read existing config
        with open(config_path, "r") as file:
            config = yaml.safe_load(file) or {}
            
        # Make sure we have the assistant section
        if "assistant" not in config:
            config["assistant"] = {}
            
        # Update the assistant name
        config["assistant"]["name"] = request.assistant_name
        
        # Save the updated config
        with open(config_path, "w") as file:
            yaml.dump(config, file)
            
        # Recreate the doc_agent with the new name
        doc_agent = create_rag_agent(VECTOR_STORE_ID)
        
        # Update the orchestrator agent with the new name and doc_agent
        orchestrator_agent = Agent(
            name=request.assistant_name,
            instructions=prompt_with_handoff_instructions("""
You are a helpful virtual assistant who can answer questions based on the available documents.
When a user asks about information that might be in the documents, route their question to the document expert.
Be friendly and concise in your responses.
            """),
            handoffs=[doc_agent],
        )
        
        return {"status": "success", "message": "Assistant name updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================================
# Vector Store Management Endpoints
# ==========================================================

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
            name=request.name
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

@app.get("/storage-admin/vector-stores/{vector_store_id}/files")
async def list_files(vector_store_id: str):
    try:
        # Get the list of files in the vector store
        response = client.vector_stores.files.list(vector_store_id=vector_store_id)
        
        # Return the file data directly
        return {"files": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================================
# File Management Endpoints
# ==========================================================

@app.post("/storage-admin/vector-stores/{vector_store_id}/files")
async def upload_file(vector_store_id: str, file: UploadFile = File(...)):
    temp_file_path = None
    try:
        # Get the original filename
        original_filename = file.filename
        
        # Read the file content
        file_content = await file.read()
        
        # Create a temporary file with the original filename
        os.makedirs("temp_uploads", exist_ok=True)
        temp_file_path = os.path.join("temp_uploads", original_filename)
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # First upload file to OpenAI files API
        with open(temp_file_path, "rb") as f:
            file_upload_response = client.files.create(
                file=f,
                purpose="assistants"
            )
            file_id = file_upload_response.id
        
        # Then associate the file_id with the vector store
        response = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        return response
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        # Detailed error logging
        error_details = str(e) + "\n" + traceback.format_exc()
        print(error_details)
        
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/storage-admin/files/{file_id}")
async def get_file_details(file_id: str):
    try:
        # Retrieve the file details from OpenAI API
        file_details = client.files.retrieve(file_id)
        
        # Format the response with the requested details
        return {
            "id": file_id,
            "filename": getattr(file_details, "filename", None),
            "bytes": getattr(file_details, "bytes", None),
            "created_at": getattr(file_details, "created_at", None),
            "status": getattr(file_details, "status", None),
            "purpose": getattr(file_details, "purpose", None),
            "format": getattr(file_details, "format", None)
        }
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
