import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json


class OptimizedWebFetcher:
    def __init__(self):
        self.session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch(self, url: str, timeout: int = 10) -> str:
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            return f"Error fetching webpage {url}: {e}"


_web_fetcher = OptimizedWebFetcher()

@tool
def fetch_webpage(url: str) -> str:
    """Fetches the content of a given URL and returns its HTML content as a string.
    Handles basic error handling and sets a User-Agent.
    """
    return _web_fetcher.fetch(url)

@tool
def fetch_and_parse_webpage(url: str, max_content_length: int = 5000) -> str:
    """Fetches a webpage, parses its content using BeautifulSoup4, and returns a cleaned text representation.
    This tool is designed to pre-process HTML to reduce noise for the LLM.
    """
    try:
        # Prefer session-based fetch for connection pooling
        html = _web_fetcher.fetch(url)
        if html.startswith("Error fetching webpage"):
            return html

        # Parse and extract common content tags to reduce noise
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style tags
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Extract text from relevant tags
        relevant_texts: List[str] = []
        for el in soup.find_all(["article", "main", "section", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
            text = el.get_text(separator=" ", strip=True)
            if text:
                relevant_texts.append(text)

        cleaned_content = " ".join(relevant_texts)

        # Truncate overly long content to cap LLM latency
        if len(cleaned_content) > max_content_length:
            cleaned_content = cleaned_content[:max_content_length] + "... [content truncated]"

        return cleaned_content
    except Exception as e:
        return f"Error fetching and parsing webpage {url}: {e}"
