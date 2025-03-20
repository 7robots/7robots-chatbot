from openai import OpenAI
import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Define a request model for the chat endpoint
class ChatRequest(BaseModel):
    message: str
    temperature: float = 1.0

MessageRequest = "what are the ten largest impact craters on the Moon, sorted by diameter?"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/chat")
async def chat(request: ChatRequest):
	response = client.responses.create(
		model="gpt-4o",
		input=request.message,
		temperature=request.temperature,
	)
	return {"response": response.output_text}


@app.get("/webchat")
async def get_chat_page():
    return FileResponse("static/index.html")
