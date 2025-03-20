from openai import OpenAI
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, FileSearchTool

# Load environment variables from .env file
load_dotenv()

# Get the API key and vector store ID from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

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
