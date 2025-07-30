from langchain.prompts import PromptTemplate

SCRAPING_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert web scraping assistant. Your task is to analyze the provided web page content 
    and the user's original query. Determine if the content is relevant to the query and extract 
    all key data points directly into a structured JSON format.

    User Query: {query}

    Webpage Content:
    {content}

    Based on the above, is this page relevant to the user's query? If yes, extract the relevant data 
    points such as 'Article Title', 'Publication Date', 'Author Name', 'Article Content' (a summary or key paragraphs),
    and 'Main Image URL' if available. If the page is not relevant, state 'Not Relevant'.

    Example Relevant Output:
    ```json
    {{
      "relevance": "Relevant",
      "extracted_data": {{
        "Article Title": "Example AI in Healthcare Article",
        "Publication Date": "2023-10-26",
        "Author Name": "John Doe",
        "Article Content": "This is a summary of the article content, focusing on key findings and advancements.",
        "Main Image URL": "https://example.com/image.jpg"
      }}
    }}
    ```

    Example Not Relevant Output:
    ```json
    {{
      "relevance": "Not Relevant"
    }}
    ```

    Your Response (JSON):
    """
)
