# TERMINAL ONLY

# Main script to run the web scraping agent
from agent.llm_agent import LLMAgent
import argparse

def main():
    parser = argparse.ArgumentParser(description="AI-powered web scraping agent.")
    parser.add_argument("query", type=str, help="The user query for web scraping.")
    args = parser.parse_args()

    user_query = args.query
    print(f"User Query: {user_query}")

    agent = LLMAgent()
    final_output = agent.run_full_scraping_workflow(user_query)
    print("\n--- Final Output ---")
    print(final_output)

if __name__ == "__main__":
    main() 