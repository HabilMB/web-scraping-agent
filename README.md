# Web Scraping Agent

This project is an AI-powered web scraping agent that can understand user queries, search the web, analyze webpages, generate and execute scraping logic, process the extracted data, and summarize the findings.

## Project Flow

1.  **[User Query]**: User provides a query via a Command Line Interface (CLI) for information to be scraped.
2.  **[LLM Agent]**: The core agent, built with Langchain and using a local Ollama model, orchestrates the workflow.
3.  **[Web Search]**: The agent uses Tavily Search API to find relevant pages based on the user query. The LLM helps formulate effective search terms.
4.  **[Analyze Webpages]**: Potentially relevant webpages are fetched (using libraries like `requests`) and their HTML is parsed (using `BeautifulSoup4`). The LLM directly analyzes the content to determine suitability and extract specific data in a structured JSON format.
5.  **[Process Data]**: The extracted raw data is cleaned, structured (e.g., using Pandas), and validated. The LLM can assist in this stage.
6.  **[Summarize Findings]**: The LLM generates a summary of the processed data and presents it to the user.

## Tech Stack

*   **Programming Language**: Python 3.12.7
*   **LLM**: Ollama (running `gemma3:4b` local model)
*   **Core Framework**: Langchain
*   **Key Python Libraries**:
    *   `langchain`: For building the agent and orchestrating LLM calls.
    *   `langchain-community`: For Ollama integration.
    *   `ollama`: Python client for Ollama if direct interaction is needed.
    *   `tavily-python`: For performing web searches.
    *   `requests` or `httpx`: For making HTTP requests to fetch webpage content.
    *   `beautifulsoup4`: For parsing HTML and XML.
    *   `pandas` (optional, for data processing): For handling and structuring tabular data.
    *   `python-dotenv` (recommended): For managing environment variables (API keys, configurations).

## Project Structure

```
web-scraping-agent/
├── main.py                 # Main script to run the agent (CLI entry point)
├── agent/                  # Core LLM agent logic, orchestration
│   ├── __init__.py
│   └── llm_agent.py        # Main agent class/logic
├── tools/                  # Reusable tools (search, web fetching, parsing)
│   ├── __init__.py
│   └── web_tools.py        # Functions for web interaction (fetching, parsing)
├── prompts/                # Stores prompt templates for the LLM
│   ├── __init__.py
│   └── general_prompts.py  # General purpose prompts
│   └── scraping_prompts.py # Prompts specific to web analysis and data extraction
├── data/                   # For storing scraped data, temporary files, vectorstores (if used)
├── requirements.txt        # Python package dependencies
├── .env_example            # Example environment file for API keys and secrets
└── DEVELOPMENT_INSTRUCTIONS.md # Step-by-step guide for developing this project
```