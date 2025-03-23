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

# Define vector_store_id (was undefined before)
vector_store_id = VECTOR_STORE_ID

response = client.vector_stores.files.list(vector_store_id=vector_store_id)
        
# For each file, get additional details
files_with_details = []

for file in response.data:
    try:
        # Get file details
        file_details = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=file.id
        )
        files_with_details.append({
            "id": file.id,
            "filename": file_details.filename,
            "created_at": file_details.created_at,
            "status": file_details.status,
            "size": getattr(file_details, "size", None),
            "object": file_details.object
        })
    except Exception as file_error:
        # If we can't get details, still include the file with basic info
        files_with_details.append({
            "id": file.id,
            "filename": getattr(file, "filename", "Unknown"),
            "error": str(file_error)
        })
print(files_with_details)
