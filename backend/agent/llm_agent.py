from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_react_agent
from langchain import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from dotenv import load_dotenv
import os
import json
import re
import ast # Import the ast module
import asyncio # Import asyncio for async operations

from backend.tools.web_tools import fetch_webpage, fetch_and_parse_webpage
from backend.prompts.scraping_prompts import SCRAPING_ANALYSIS_PROMPT
from backend.prompts.general_prompts import FINAL_SUMMARY_PROMPT

load_dotenv()

class LLMAgent:
    def __init__(self):
        # self.llm = Ollama(model=os.getenv("OLLAMA_MODEL", "gemma3:4b"), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        self.llm = ChatGroq(
            temperature=0,
            model_name="moonshotai/kimi-k2-instruct",
        )
        self.search_tool = TavilySearchResults()

    def run_search_agent(self, query: str):
        # Define a prompt for the LLM to generate a search query
        search_query_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant. Based on the user's request, generate a concise search query for Tavily. Respond with only the search query. Do not add any conversational filler."),
            ("human", "{input}"),
        ])

        # Create a simple chain: prompt -> llm -> execute search tool
        search_query_generator_chain = (search_query_prompt | self.llm | StrOutputParser())
        
        try:
            # LLM generates the search query
            generated_search_query = search_query_generator_chain.invoke({"input": query})
            print(f"Generated search query: {generated_search_query}")

            # Execute the Tavily search tool with the generated query
            search_results = self.search_tool.invoke(generated_search_query)
            print(f"Type of raw search results: {type(search_results)}")
            print(f"Raw search results: {search_results}")
            
            urls = []
            search_results_list = [] # Initialize here to ensure it's always defined
            if isinstance(search_results, list):
                search_results_list = search_results
            elif isinstance(search_results, str):
                # Parse the string as a Python literal (list of dicts)
                try:
                    search_results_list = ast.literal_eval(search_results)
                except (ValueError, SyntaxError):
                    print("Warning: Could not parse search results with ast.literal_eval. Attempting regex fallback.")
                    # Fallback to regex if literal_eval fails
                    search_results_list = []
                    found_urls = re.findall(r'https?://[\w./\-]+', search_results)
                    urls.extend([url for url in found_urls if '.' in url and len(url) > 10 and not any(ext in url for ext in ['.jpg', '.png', '.css', '.js'])])
            
            print(f"Parsed search results list: {search_results_list}")
            
            for result_item in search_results_list:
                if 'url' in result_item:
                    urls.append(result_item['url'])
            urls = list(set(urls)) # Remove duplicates
            
            return {"search_output": search_results, "urls": urls}

        except Exception as e:
            print(f"An error occurred during search agent execution: {e}")
            return {"search_output": f"Error: {e}", "urls": []}

    def simple_llm_call(self, prompt_text: str):
        return self.llm.invoke(prompt_text)

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
        yield {"step": "Performing web search...", "status": "in_progress"}
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
                print(f"Error or unknown relevance for {url}: {analysis_feedback.get("message", "Unknown error")}")

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
