import os
import json
from typing import Any, Dict, List
from openai import OpenAI

# Initialize OpenAI client for web-capable GPT model
dotenv_api_key = os.getenv("OPENAI_API_KEY")
_client = OpenAI(api_key=dotenv_api_key)


def fetch_competitors(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Tool to search the web for competitors of a given product or domain.

    Expects params:
      - product_name: str, name of the product or domain to search competitors for
      - max_results: int (optional), number of competitors to return (default 5)

    Returns:
      List of dicts, each with keys:
        * name: str
        * url: str
        * description: str
    """
    product = params.get("product_name")
    if not product:
        raise ValueError("Parameter 'product_name' is required")
    max_res = params.get("max_results", 5)

    system_prompt = (
        "You are an AI assistant with the ability to search the web for market intelligence. "
        "Your task is to find competitors for a given product or website."
    )
    user_prompt = (
        f"Find the top {max_res} competitors for the product or domain '{product}'. "
        "For each competitor, provide its name, website URL, and a concise description. "
        "Respond strictly in JSON as a list of objects with keys 'name', 'url', 'description'."
    )

    response = _client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        # ensure function calling is bypassed so we get plain JSON
        function_call=None
    )
    content = response.choices[0].message.content

    try:
        competitors = json.loads(content)
    except json.JSONDecodeError:
        # In case of minor formatting issues, try to clean and parse
        cleaned = content.strip().strip('`')
        try:
            competitors = json.loads(cleaned)
        except Exception:
            competitors = []
    return competitors

# Example registration in AgentOrchestrator.py:
# from retrievers.competitor_scrapper import fetch_competitors
# TOOLS["fetch_competitors"] = fetch_competitors
