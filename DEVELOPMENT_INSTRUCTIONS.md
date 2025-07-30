# Development Instructions for Web Scraping Agent

This document outlines the key development steps and architectural decisions for building the AI Web Scraping Agent, based on our discussions.

## Core Philosophy

*   **LLM for Orchestration and High-Level Reasoning:** The Large Language Model (LLM), integrated via Langchain and running locally with Ollama (specifically `gemma3:4b`), will be responsible for understanding user queries, planning steps, formulating search queries, analyzing web content at a high level, and determining *what* data to extract.
*   **Deterministic Tools for Execution:** Actual web fetching, parsing, and data extraction will be performed by robust, deterministic Python functions (Langchain Tools). **Crucially, the LLM's role in "generating scraping logic" is to generate *parameters* (e.g., URLs, CSS selectors, specific instructions) for these pre-defined, trusted tools, *not* to write and execute arbitrary scraping code.** This enhances reliability, security, and maintainability.
*   **Iterative Development:** Build and test each component of the flow incrementally.

## Phase 1: Setup & Foundation

1.  **Environment Setup:**
    *   Ensure Python 3.12.7 is installed and active.
    *   Set up a Python virtual environment (e.g., `.venv`).
    *   Install Ollama and pull your chosen model: `ollama pull gemma3:4b`. Ensure Ollama is running.
    *   Create `requirements.txt` (see `README.md` for initial content which includes `duckduckgo-search`, `langchain-community`, etc.) and install dependencies (`pip install -r requirements.txt`).
    *   Create a `.env` file from `.env_example` (see `README.md`) and ensure `OLLAMA_MODEL` is set to "gemma3:4b" and `OLLAMA_BASE_URL` is correct. DuckDuckGo search via the library typically doesn't require API keys for basic development use.

2.  **Project Structure:**
    *   Follow the structure outlined in `README.md` (main.py, agent/, tools/, prompts/, data/).

## Phase 2: Implementing Core Components (Iterative Steps)

**Step 1: User Query Input (CLI)**
*   Modify `main.py` to accept a user query as a command-line argument (e.g., using `argparse`).

**Step 2: LLM and Search Integration**
*   **LLM Setup (`agent/llm_agent.py`):**
    *   Initialize your Ollama LLM using `langchain_community.llms.Ollama` (or `langchain_community.chat_models.ChatOllama`), configured for `gemma3:4b` (loaded from `.env` or config).
    *   Load other configurations (like model name, temperature) from `.env` if applicable.
*   **Search Tool Setup (`tools/web_tools.py`):**
    *   Utilize the `duckduckgo-search` Python library for web searches. Langchain provides a `DuckDuckGoSearchRun` tool (from `langchain_community.tools`) that conveniently wraps this library.
    *   This approach is good for development as it generally doesn't require API keys for basic search functionality.
    *   *Advanced Note:* Components like Langchain's `WebResearchRetriever` showcase how an LLM can be used to generate search queries and retrieve documents, providing a useful pattern, though for this project, we are building the steps more explicitly to begin with.
    *   It should return the HTML content as a string.
    *   Consider adding basic error handling (e.g., for network errors, bad status codes) and setting a User-Agent.
*   **Initial Agent/Chain (`agent/llm_agent.py` or `main.py` for initial testing):**
    *   Create a simple Langchain chain or agent that:
        1.  Takes the user query.
        2.  Uses the LLM to potentially refine or directly use the query for search.
        3.  Invokes the `DuckDuckGoSearchRun` tool.
        4.  Prints the search results (URLs, snippets).

**Step 3: Webpage Fetching and Basic Parsing**
*   **Fetching Tool (`tools/web_tools.py`):**
    *   Create a Langchain `Tool` that takes a URL and fetches its content using `requests` or `httpx`.
    *   It should return the HTML content as a string.
    *   Consider adding basic error handling (e.g., for network errors, bad status codes) and setting a User-Agent.
*   **Agent Logic Update:**
    *   The agent should be able to take a URL (e.g., from search results) and use the fetching tool to get its content.

**Step 4: Content Analysis and Parameter Generation (LLM-Driven)**
*   **Parsing and Pre-processing (`tools/web_tools.py` or within the analysis step):
    *   Use `BeautifulSoup4` to parse the HTML obtained from the fetching tool.
    *   Implement functions to pre-process the HTML: remove scripts, styles, navbars, footers, and extract the main content area if possible. This helps reduce the token count for the LLM and improves focus.
    *   Langchain's `WebBaseLoader` is excellent for this. It can use `requests` and `BeautifulSoup` internally. Crucially, its `bs_kwargs` parameter can accept a `parse_only` argument with a `bs4.SoupStrainer` to fetch only specific parts of an HTML document, significantly aiding in pre-processing and reducing noise for the LLM.
*   **Prompt Engineering (`prompts/scraping_prompts.py`):**
    *   Develop prompts for the `gemma3:4b` LLM. The input to these prompts will be the user's original query and the cleaned/relevant section of the webpage HTML.
    *   The LLM should be instructed to:
        *   Verify if the page content is relevant to the user's query.
        *   Identify the specific data elements to be extracted.
        *   Output a structured representation of what to extract, primarily focusing on **CSS selectors** or precise **XPaths** for each piece of data. For example, a JSON string: `{"product_name": ".title-class", "price": "#price-id span.value"}`.
*   **Agent Logic Update:**
    *   After fetching a page, the agent will pass its content (or relevant parts) and the user query to the LLM with the analysis prompt.
    *   The agent will capture the LLM's response (the scraping parameters/selectors), potentially using an Output Parser.

**Step 5: Custom Extraction Tool(s)**
*   **Extraction Function(s) (`tools/web_tools.py`):**
    *   Create one or more Python functions that take the webpage content (or URL) and the selectors/parameters provided by the LLM.
    *   These functions use `BeautifulSoup4` to apply the selectors and extract the text or attributes.
    *   Handle cases where selectors don't find elements.
    *   Wrap these functions as Langchain `Tool`s. You might have a generic `extract_data_with_selectors` tool.
*   **Agent Logic Update:**
    *   The agent uses the LLM-generated selectors to invoke this custom extraction tool.

**Step 6: Summarization and Output**
*   **Summarization Prompt (`prompts/general_prompts.py`):**
    *   Develop a prompt to instruct the `gemma3:4b` LLM to summarize the extracted and processed data, or to answer the original user query based on this data.
*   **Agent Logic Update:**
    *   The agent passes the processed data to the LLM with the summarization prompt.
    *   The agent presents the final summary/answer to the user via the CLI.

## Phase 3: Refinement and Iteration

*   **Error Handling:** Implement robust error handling at every stage (network, parsing, LLM API errors, tool execution failures).
*   **Logging:** Add comprehensive logging throughout the agent's workflow for debugging.
*   **Configuration:** Use `.env` for secrets and critical configs (like `OLLAMA_MODEL="gemma3:4b"`).
*   **Advanced Scraping Needs:** Primarily rely on `requests` and `BeautifulSoup`. If JavaScript-heavy sites become a frequent target and cannot be scraped effectively, tools like `Selenium` or `Playwright` could be explored as a later enhancement, wrapped as secure, predefined tools.
*   **State Management:** For more complex interactions or multi-turn conversations, consider how the agent will maintain state (Langchain's memory modules can help).
*   **Ethical Scraping:** Implement delays, respect `robots.txt` (though automated interpretation is complex), and set a clear User-Agent.

## Key Langchain Components to Utilize:

*   **LLMs:** `langchain_community.llms.Ollama` (for `gemma3:4b`)
*   **ChatModels:** `langchain_community.chat_models.ChatOllama` (for `gemma3:4b`, if using chat-based interactions/prompts)
*   **Prompts:** `PromptTemplate`, `ChatPromptTemplate`, `HumanMessagePromptTemplate`, etc.
*   **Tools:** `@tool` decorator or `Tool` class for your custom functions. `DuckDuckGoSearchRun` from `langchain_community.tools`.
*   **Agents:** Consider standard agent types (like `create_react_agent` or `create_openai_tools_agent` adapted for Ollama if feasible) or simple LCEL chains if the flow is linear enough.
*   **Loaders:** `WebBaseLoader` for fetching and initial parsing of web content (utilize `bs_kwargs` with `bs4.SoupStrainer`).
*   **Output Parsers:** To structure LLM responses (e.g., `PydanticOutputParser`, `JsonOutputParser` for the scraping parameters).
*   **Python REPL Tool (`PythonREPLTool`):
    *   **Use with Extreme Caution.** While powerful, a Python REPL tool that allows the LLM to generate and execute arbitrary Python code should *not* be used for core web scraping tasks (fetching, parsing) due to security risks and reliability concerns.
    *   **Potential Use Cases:** It *could* be considered for:
        *   Complex data manipulation or calculations on *already extracted and cleaned data* if these operations are hard to define as a fixed tool.
        *   Simple, non-I/O, non-critical utility tasks or calculations if the LLM needs to perform them dynamically.
    *   Always prefer well-defined, secure tools for any I/O operations or interactions with external systems.

This document should serve as a roadmap. Be prepared to adapt and refine as you build! 