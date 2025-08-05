# backend/main.py
import asyncio # Needed for running synchronous functions in an async context
import os
from dotenv import load_dotenv, find_dotenv # New: For loading environment variables
import bleach

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from fastapi.responses import StreamingResponse
import json

# Adjust these imports based on your actual file structure after moving:
from backend.agent.llm_agent import LLMAgent
from backend.tools.web_tools import fetch_and_parse_webpage
from backend.prompts.general_prompts import FINAL_SUMMARY_PROMPT

# Load environment variables from .env file
load_dotenv(find_dotenv())

app = FastAPI()

# Configure CORS to allow your frontend to communicate with the backend
# IMPORTANT: In production, restrict origins to your frontend's domain!
origins = [
    "http://localhost",
    "http://localhost:3000", # Allow your React/frontend dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeQuery(BaseModel):
    user_query: str

    @validator('user_query')
    def sanitize_query(cls, value):
        # Sanitize the input to prevent XSS
        return bleach.clean(value)

@app.get("/")
async def read_root():
    return {"message": "Web Scraping Agent API is running!"}

@app.post("/scrape_and_summarize/")
async def scrape_and_summarize_endpoint(query: ScrapeQuery):
    async def generate_events():
        agent = LLMAgent()
        async for progress_update in agent.run_full_scraping_workflow(user_query=query.user_query):
            yield json.dumps(progress_update) + "\n"
    return StreamingResponse(generate_events(), media_type="application/x-ndjson")

# Add other endpoints as needed, e.g., for specific tools or functionalities 