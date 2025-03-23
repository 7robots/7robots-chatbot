from openai import OpenAI
import os
import subprocess
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

# Initialize the OpenAI client for vector store API calls
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

# Define vector_store_id
vector_store_id = VECTOR_STORE_ID

# List files in the vector store
try:
    response = client.vector_stores.files.list(vector_store_id=vector_store_id)
    
    # For each file, get additional details
    files_with_details = []
    for file in response.data:
        try:
            # Get basic vector store file details
            file_details = client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=file.id
            )
            
            # Try to get additional file details from files API
            file_metadata = None
            try:
                file_metadata = client.files.retrieve(file.id)
            except Exception as metadata_error:
                # If this fails, continue with just vector store file details
                pass
            
            # Combine the details
            file_info = {
                "id": file.id,
                "status": getattr(file_details, "status", None),
                "created_at": getattr(file_details, "created_at", None),
                "object": getattr(file_details, "object", None)
            }
            
            # Add file metadata if available
            if file_metadata:
                file_info.update({
                    "filename": getattr(file_metadata, "filename", None),
                    "bytes": getattr(file_metadata, "bytes", None),
                    "purpose": getattr(file_metadata, "purpose", None),
                    "format": getattr(file_metadata, "format", None),
                    "detail_status": getattr(file_metadata, "status", None)
                })
            else:
                # If file metadata not available, use vector store file details
                file_info["filename"] = getattr(file_details, "filename", f"File-{file.id}")
            
            files_with_details.append(file_info)
        except Exception as file_error:
            # If we can't get details, still include the file with basic info
            files_with_details.append({
                "id": file.id,
                "error": str(file_error)
            })
    
    # Print out the results
    print(f"Found {len(files_with_details)} files:")
    for file_info in files_with_details:
        print(f"\nFile ID: {file_info.get('id')}")
        print(f"Filename: {file_info.get('filename', 'Unknown')}")
        if file_info.get('created_at'):
            print(f"Created at: {file_info.get('created_at')}")
        if file_info.get('bytes'):
            print(f"Size: {file_info.get('bytes')} bytes")
        if file_info.get('status'):
            print(f"Status: {file_info.get('status')}")
        if file_info.get('error'):
            print(f"Error: {file_info.get('error')}")
            
except Exception as e:
    print(f"Error: {str(e)}")
