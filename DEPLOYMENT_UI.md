# Web Scraping Agent with UI - Development Guide

This guide provides step-by-step instructions to set up and run the web scraping agent with its integrated user interface for local development.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.x:** (Specify exact version if necessary, e.g., Python 3.9+)
    *   Verify with: `python3 --version`
*   **pip:** Python package installer (usually comes with Python)
    *   Verify with: `pip --version`
*   **Node.js (LTS recommended):** Required for the frontend development.
    *   Verify with: `node --version`
*   **npm (Node Package Manager):** Usually comes with Node.js.
    *   Verify with: `npm --version`

## 2. Integrating with Your Existing Project

This section details how to transform your current web scraping agent into a web application with a separate backend API and a frontend UI.

### 2.1. Backend API Conversion (FastAPI Example)

You will create a new directory for your backend API and adapt your existing Python logic to be exposed via API endpoints.

1.  **Create a `backend` directory:**
    ```bash
    mkdir backend
    ```
2.  **Add `__init__.py` files:**
    For Python to recognize `backend` and its subdirectories as packages, create empty `__init__.py` files:
    ```bash
    touch backend/__init__.py
    touch backend/agent/__init__.py
    touch backend/prompts/__init__.py
    touch backend/tools/__init__.py
    ```
3.  **Move/Adapt Core Logic:**
    *   Move your existing `agent/`, `prompts/`, and `tools/` directories into the new `backend/` directory.
    *   Your project structure should now look like:
        ```
        web-scraping-agent/
          - backend/
            - agent/
              - __init__.py
              - llm_agent.py
            - prompts/
              - __init__.py
              - general_prompts.py
              - scraping_prompts.py
            - tools/
              - __init__.py
              - web_tools.py
            - __init__.py
            - main.py (new FastAPI app file)
          - frontend/ (will be created in next step)
          - requirements.txt
          - .env_example
          - main.py (original, can be deleted or kept for reference)
          - ... (other root files)
        ```
    *   **Refactor `main.py`:** Your existing `main.py` likely orchestrates the scraping process. You'll need to create a new `main.py` inside the `backend/` directory that defines FastAPI endpoints, and then call your existing scraping functions from within these endpoints.

    *   **CRITICAL: Update All Import Paths:** After moving `agent/`, `prompts/`, and `tools/` into `backend/`, any Python files (including `llm_agent.py`, `web_tools.py`, and the new `backend/main.py`) that import modules from these directories will need their import statements updated to reflect the new `backend.` prefix. For example, `from agent.llm_agent import LLMAgent` would become `from backend.agent.llm_agent import LLMAgent`. Review *all* Python files within the `backend` directory for these changes.

    *Example `backend/agent/llm_agent.py` (Relevant sections):*
    ```python
    # backend/agent/llm_agent.py
    import asyncio
    import json
    import os
    from dotenv import load_dotenv
    from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_community.llms import Ollama
    import ast
    import re

    from backend.tools.web_tools import fetch_and_parse_webpage
    from backend.prompts.scraping_prompts import SCRAPING_ANALYSIS_PROMPT
    from backend.prompts.general_prompts import FINAL_SUMMARY_PROMPT

    load_dotenv()

    class LLMAgent:
        def __init__(self):
            self.llm = Ollama(model=os.getenv("OLLAMA_MODEL", "gemma3:4b"), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
            self.search_tool = TavilySearchResults()

        # ... existing run_search_agent and simple_llm_call methods ...

        def analyze_webpage_and_suggest_selectors(self, url: str, user_query: str):
            print(f"Fetching and parsing webpage: {url}")
            content = fetch_and_parse_webpage.func(url)

            if "Error fetching webpage" in content:
                return {"relevance": "Error", "message": content}

            print("Analyzing content with LLM...")
            analysis_chain = (SCRAPING_ANALYSIS_PROMPT | self.llm | JsonOutputParser())
            
            try:
                analysis_result = analysis_chain.invoke({"query": user_query, "content": content})
                return analysis_result # This now directly returns extracted data or relevance status
            except Exception as e:
                print(f"An error occurred during webpage analysis: {e}")
                return {"relevance": "Error", "message": f"LLM analysis failed: {e}"}

        async def run_full_scraping_workflow(self, user_query: str):
            print("\n--- Starting Full Scraping Workflow ---")
            print(f"User Query: {user_query}")

            # Step 1: Web Search
            yield {"step": "1. Performing web search...", "status": "in_progress"}
            print("\nStep 1: Performing web search...")
            search_result = await asyncio.to_thread(self.run_search_agent, f"Search relevant websites for: {user_query}")
            print(f"Search Results Summary: {search_result.get('search_output', 'N/A')}")
            candidate_urls = search_result.get("urls", [])
            print(f"Candidate URLs found: {candidate_urls}")

            if not candidate_urls:
                yield {"step": "No relevant URLs found.", "status": "error", "final_result": "No relevant URLs found from search. Cannot proceed with scraping.", "extracted_data": ""}
                return # Ensure it stops execution if no URLs

            all_extracted_data = []

            # Step 2: Analyze Webpages & Generate Scraping Parameters
            yield {"step": f"Analyzing {len(candidate_urls)} candidate webpages...", "status": "in_progress"}
            for url in candidate_urls:
                print(f"\nStep 2: Analyzing webpage: {url}")
                analysis_feedback = await asyncio.to_thread(self.analyze_webpage_and_suggest_selectors, url, user_query)
                
                if analysis_feedback.get("relevance") == "Relevant":
                    print(f"Page {url} is relevant. Extracting data...")
                    extracted_item_data = analysis_feedback.get("extracted_data")
                    
                    if extracted_item_data:
                        all_extracted_data.append({"url": url, "data": extracted_item_data})
                        print(f"Successfully extracted data from {url}:")
                        print(json.dumps(extracted_item_data, indent=2))
                    else:
                        print(f"No data extracted for {url}. Skipping.")
                elif analysis_feedback.get("relevance") == "Not Relevant":
                    print(f"Page {url} is not relevant to the query. Skipping.")
                else:
                    print(f"Error or unknown relevance for {url}: {analysis_feedback.get('message', 'Unknown error')}")

            if all_extracted_data:
                yield {"step": f"Finished analyzing webpages. Extracted data from {len(all_extracted_data)} relevant pages.", "status": "info"}
            else:
                yield {"step": "No relevant data extracted from any webpages.", "status": "warning"}

            if not all_extracted_data:
                final_response = "No relevant data could be extracted from any of the search results."
                yield {"step": "No data extracted.", "status": "error", "final_result": final_response, "extracted_data": ""}
            else:
                processed_data_summary = json.dumps(all_extracted_data, indent=2)

                # Step 5: Summarize Findings
                yield {"step": "Summarizing findings with LLM...", "status": "in_progress"}
                print("\nStep 4: Summarizing findings with LLM...")
                summary_chain = (FINAL_SUMMARY_PROMPT | self.llm | StrOutputParser())
                final_response = await asyncio.to_thread(summary_chain.invoke, {"user_query": user_query, "extracted_data": processed_data_summary})
                yield {"step": "Scraping Workflow Finished.", "status": "complete", "final_result": final_response}
            
            print("\n--- Scraping Workflow Finished ---")
    ```

    *Example `backend/main.py` (FastAPI):*
    ```python
    # backend/main.py
    import asyncio # Needed for running synchronous functions in an async context
    import os
    from dotenv import load_dotenv # New: For loading environment variables

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from fastapi.responses import StreamingResponse
    import json

    # Adjust these imports based on your actual file structure after moving:
    from backend.agent.llm_agent import LLMAgent
    from backend.tools.web_tools import fetch_and_parse_webpage
    from backend.prompts.general_prompts import FINAL_SUMMARY_PROMPT

    # Load environment variables from .env.backend
    load_dotenv(dotenv_path='../.env.backend') # Adjust path if .env.backend is not in parent directory

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
    ```
5.  **Update `requirements.txt`:**
    Add FastAPI, Uvicorn, and `python-dotenv` to your `requirements.txt` file at the root of your project. **Crucially, ensure ALL your original project dependencies (e.g., `playwright`, `langchain`, `beautifulsoup4`, etc.) are also present in this file.**
    ```
    # ... existing requirements from your original project ...
    fastapi==0.103.2 # Or the latest stable version
    uvicorn[standard]==0.23.2 # Or the latest stable version
    python-dotenv==1.0.0 # Or the latest stable version
    ```

### 2.2. Frontend UI Creation (React Example)

You will create a new directory for your frontend application.

1.  **Create a `frontend` directory and initialize a new project:**
    (Ensure you are in the `web-scraping-agent` root directory first: `cd ..` if you are in `backend/`)
    ```bash
    npx create-react-app frontend --template typescript # Or just 'create-react-app frontend' for JS
    cd frontend
    ```
    *   This will create a new React project in the `frontend` directory. If you prefer Vue or Angular, use their respective CLI commands (e.g., `vue create frontend`, `ng new frontend`).
2.  **Design the UI and connect to the Backend:**
    *   Inside `frontend/src/App.js` (or `App.tsx` for TypeScript), you'll create the input fields, buttons, and display areas.
    *   You'll use JavaScript's `fetch` API or a library like Axios to make HTTP requests to your new backend API (e.g., `http://localhost:8000/scrape_and_summarize/`).

    *Example `frontend/src/App.js` (Simplified React):*
    ```javascript
    // frontend/src/App.js
    import React, { useState } from 'react';
    import './App.css';

    function App() {
      const [query, setQuery] = useState('');
      const [summary, setSummary] = useState('');
      const [loading, setLoading] = useState(false);
      const [error, setError] = useState('');
      const [progressSteps, setProgressSteps] = useState([]); // New state for progress

      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

      const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSummary('');
        setProgressSteps([]); // Clear previous steps

        try {
          const response = await fetch(`${API_URL}/scrape_and_summarize/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: query }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder('utf-8');
          let result = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            result += chunk;

            // Process each line as a separate JSON object
            const lines = result.split('\n');
            result = lines.pop(); // Keep the last, possibly incomplete, line

            for (const line of lines) {
              if (line.trim() === '') continue;
              try {
                const data = JSON.parse(line);
                setProgressSteps((prevSteps) => {
                  const newSteps = [...prevSteps, data];
                  // Update final summary/extracted data only when status is complete
                  if (data.status === 'complete') {
                    setSummary(data.final_result);
                  } else if (data.status === 'error') {
                    setError(data.final_result || data.step || 'An error occurred during a step.');
                  }
                  return newSteps;
                });

              } catch (jsonError) {
                console.error('Error parsing JSON from stream:', jsonError, 'Line:', line);
                setError('Error processing stream data.');
              }
            }
          }

        } catch (err) {
          setError(err.message || 'Failed to connect to the backend API.');
          console.error(err);
        } finally {
          setLoading(false);
        }
      };

      return (
        <div className="App">
          <header className="App-header">
            <h1>Web Scraping Agent UI</h1>
            <form onSubmit={handleSubmit}>
              <div>
                <label htmlFor="query-input">Your Query:</label>
                <textarea
                  id="query-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., Summarize the main points of this article."
                  rows="4"
                  required
                />
              </div>
              <button type="submit" disabled={loading}>
                {loading ? (
                  <div className="spinner"></div>
                ) : (
                  'Scrape & Summarize'
                )}
              </button>
            </form>

            {loading && progressSteps.length === 0 && <p>Starting process...</p>}
            {progressSteps.length > 0 && (
              <div className="progress-log">
                <h2>Progress:</h2>
                {progressSteps.map((step, index) => (
                  <p key={index} className={`step-status-${step.status}`}>
                    Step {index + 1}: {step.step}
                  </p>
                ))}
              </div>
            )}

            {error && <p className="error-message">Error: {error}</p>}
            {summary && (
              <div className="results">
                <h2>Summary:</h2>
                <p>{summary}</p>
              </div>
            )}
          </header>
        </div>
      );
    }

    export default App;
    ```

### 2.3. Environment Variables (`.env.backend` and `.env` for Frontend)

*   **Backend (`.env.backend`):** Create a file named `.env.backend` in the root of your `web-scraping-agent` project (at the same level as the `backend` and `frontend` directories). This file will store your API keys and other sensitive information.
    *Example `.env.backend`:*
    ```
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY_HERE"
    # OLLAMA_MODEL="gemma3:4b" # Uncomment and set if you want to override default
    # OLLAMA_BASE_URL="http://localhost:11434" # Uncomment and set if you want to override default
    ```
    *   **CRITICAL: Loading .env.backend:** Ensure `python-dotenv` is used in your `backend/main.py` to load these variables. The path to `dotenv_path` should be correct relative to `main.py`. If `.env.backend` is in the project root, and `main.py` is in `backend/`, the path should be `../.env.backend`.

*   **Frontend (`frontend/.env`):** Create a file named `.env` inside your `frontend/` directory. This file is used by Create React App to load environment variables for the frontend.
    *Example `frontend/.env`:*
    ```
    REACT_APP_API_URL=http://localhost:8000
    ```
    *   **CRITICAL:** React environment variables must be prefixed with `REACT_APP_`.

## 3. Running the Application

Follow these steps to run your web scraping agent with the UI:

### 3.1. Install Backend Dependencies & Playwright Browsers

1.  **Navigate to the project root:**
    ```bash
    cd /path/to/your/web-scraping-agent
    ```
2.  **Create and activate a Python virtual environment (if you haven't already):**
    ```bash
    python3 -m venv venv_backend
    source venv_backend/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Playwright browser binaries:**
    ```bash
    playwright install
    ```
    *   If you encounter errors related to missing system dependencies (e.g., `libflite`, `libwoff2`), you may need to install them manually on your Linux distribution. For Debian/Ubuntu, you can try:
        ```bash
        sudo apt-get update
        sudo apt-get install libflite1 libwoff2-1
        ```

### 3.2. Run the Backend Server

1.  **Ensure your virtual environment is active.**
2.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
3.  **Start the FastAPI server:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    *   The `--reload` flag will automatically restart the server when you make code changes.
    *   The `--port 8000` flag ensures it runs on port 8000, which is what the frontend expects by default.
    *   Keep this terminal window open; the backend server will continue to run.

### 3.3. Run the Frontend Development Server

1.  **Open a new terminal window.**
2.  **Navigate to the frontend directory:**
    ```bash
    cd /path/to/your/web-scraping-agent/frontend
    ```
3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```
4.  **Start the React development server:**
    ```bash
    npm start
    ```
    *   This will typically open your browser to `http://localhost:3000`. If not, navigate there manually.
    *   Keep this terminal window open; the frontend development server will continue to run.

## 4. Troubleshooting

*   **CORS Errors:** If your frontend cannot connect to the backend, check the `origins` list in `backend/main.py` and ensure `http://localhost:3000` is included.
*   **ModuleNotFoundError:** Double-check your import paths in all Python files, especially after moving directories. Remember the `backend.` prefix for internal imports.
*   **Playwright Issues:** Ensure `playwright install` ran successfully and that all necessary system dependencies are installed on your OS.
*   **Environment Variables:** Verify that your `.env.backend` and `frontend/.env` files are correctly set up and loaded.
*   **Backend/Frontend Not Updating:** Ensure both `uvicorn` and `npm start` are running with their respective `--reload` (for Uvicorn) or automatic refresh (for Create React App) capabilities. 