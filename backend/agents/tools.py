import os
import httpx
import json

async def perform_web_search(query: str, max_results: int = 3) -> str:
    """
    Performs a web search using Tavily API.
    Returns a formatted string of results.
    """
    try:
        api_key = os.environ.get("SERP_KEY") 
        if not api_key: return "Error: SERP_KEY not set."
        
        print(f"    > [Tool] Searching Tavily for: {query}")
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_item_list": False,
            "max_results": max_results
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            
        if response.status_code != 200:
            return f"Tavily Search Error: {response.status_code} - {response.text}"
            
        results = response.json()
        formatted_output = ""
        
        if "results" in results:
            for i, result in enumerate(results["results"]):
                title = result.get('title', 'Unknown Title')
                link = result.get("url", "")
                snippet = result.get("content", "")
                formatted_output += f"SOURCE [{i+1}]\nTitle: {title}\nURL: {link}\nWrapper: {snippet}\n\n"
                
        return formatted_output if formatted_output else "No relevant results found."
        
    except Exception as e:
        return f"Search Tool Error: {e}"
