# AI Web Scraping Agent

This project is a full-stack AI-powered web scraping agent. It features a React frontend and a FastAPI backend. The agent can understand user queries, search the web, analyze webpages, extract structured data, and provide a summarized answer.

## Project Flow

1.  **[User Query]**: A user enters a query into the React-based web interface.
2.  **[Frontend to Backend]**: The frontend sends the query to the FastAPI backend.
3.  **[Backend API]**: The backend serves as the interface to the core LLM agent.
4.  **[LLM Agent]**: The agent, built with Langchain, receives the query and orchestrates the workflow.
5.  **[Web Search]**: The agent uses the Tavily Search API to find relevant webpages. The LLM formulates an effective search query.
6.  **[Analyze & Extract]**: Webpages are fetched (using `requests`, `BeautifulSoup4`, and potentially `Playwright` for dynamic sites). The LLM directly analyzes the content to determine relevance and extract the requested information into a structured JSON format.
7.  **[Summarize Findings]**: The LLM generates a final, human-readable summary based on all the extracted data.
8.  **[Stream to Frontend]**: The backend streams the entire process (search, analysis, final summary) back to the frontend in real-time, providing step-by-step feedback to the user.

## Tech Stack

*   **Frontend**:
    *   **Framework**: React
    *   **Styling**: Standard CSS
*   **Backend**:
    *   **Framework**: FastAPI
    *   **Programming Language**: Python 3.12
    *   **LLM**: Groq (using `moonshotai/kimi-k2-instruct` model via API)
*   **Key Python Libraries**:
    *   `langchain`: For building the agent and orchestrating LLM calls.
    *   `langchain-groq`: For Groq API integration.
    *   `fastapi`: High-performance web framework for the backend API.
    *   `uvicorn`: ASGI server for FastAPI.
    *   `tavily-python`: For performing web searches.
    *   `requests`: For making HTTP requests.
    *   `beautifulsoup4`: For parsing HTML.
    *   `playwright`: For advanced browser automation and scraping dynamic websites.
    *   `python-dotenv`: For managing environment variables.
    *   `bleach`: For sanitizing HTML content.

## Project Structure

```
web-scraping-agent/
├── backend/
│   ├── agent/              # Core LLM agent logic
│   │   └── llm_agent.py
│   ├── prompts/            # LLM prompt templates
│   │   ├── general_prompts.py
│   │   └── scraping_prompts.py
│   ├── tools/              # Reusable tools (web fetching, parsing)
│   │   └── web_tools.py
│   └── main.py             # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   └── index.js        # React entry point
│   ├── public/
│   │   └── index.html      # Main HTML file
│   └── package.json        # Frontend dependencies and scripts
├── main.py                 # Main script to run the application
├── requirements.txt        # Python package dependencies
├── .env_example            # Example environment file for API keys
└── README.md               # This file
```