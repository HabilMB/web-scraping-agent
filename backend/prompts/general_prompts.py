from langchain.prompts import PromptTemplate

FINAL_SUMMARY_PROMPT = PromptTemplate.from_template(
    """You are an AI assistant tasked with summarizing scraped data and answering a user's query.
    The user's original query was: {user_query}

    Here is the extracted data:
    {extracted_data}

    Based on the extracted data, provide a concise summary or answer the original user's query directly.
    If no relevant data was extracted, state that the information could not be found.
    """
)

