from langchain_core.prompts import PromptTemplate

FINAL_SUMMARY_PROMPT = PromptTemplate.from_template(
    """You are an AI assistant tasked with summarizing scraped data and answering a user's query.
    The user's original query was: {user_query}

    Here is the extracted data:
    {extracted_data}

    Write the answer as plain prose only. Do NOT use Markdown, tables, bullet
    points, headings, bold/italic syntax (no **, *, _, #, backticks), or HTML
    tags (no <br>, <p>, etc.). Use normal paragraphs separated by blank lines.
    If you need to list sources, put them at the end on their own lines as
    "Source: <title or domain> - <url>".

    Based on the extracted data, give a concise plain-text answer to the user's
    query. If no relevant data was extracted, state that the information could
    not be found.
    """
)

