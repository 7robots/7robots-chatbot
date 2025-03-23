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


response = client.files.retrieve("file-YHiVvmpkQYwjBFhrrsaeZT")
print(response)

