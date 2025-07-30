import requests
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json

@tool
def fetch_webpage(url: str) -> str:
    """Fetches the content of a given URL and returns its HTML content as a string.
    Handles basic error handling and sets a User-Agent.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error fetching webpage {url}: {e}"

@tool
def fetch_and_parse_webpage(url: str) -> str:
    """Fetches a webpage, parses its content using BeautifulSoup4, and returns a cleaned text representation.
    This tool is designed to pre-process HTML to reduce noise for the LLM.
    """
    try:
        # Using WebBaseLoader with bs_kwargs for parsing only relevant content
        loader = WebBaseLoader(
            url,
            # bs_kwargs={
            #     "parse_only": BeautifulSoup("", "html.parser").find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div"]) # focus on common content tags
            # }
        )
        docs = loader.load()
        # Concatenate page content from all documents/parts if any
        cleaned_content = " ".join([doc.page_content for doc in docs])
        return cleaned_content
    except Exception as e:
        return f"Error fetching and parsing webpage {url}: {e}"
