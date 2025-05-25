import requests
from duckduckgo_search import DDGS
from typing import List, Dict, Any
import json

class DuckDuckGoSearchTool:
    """
    Online search grounding tool using DuckDuckGo
    Provides search results with sources for grounding generations
    """
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()
    
    def search(self, query: str, max_results: int = None) -> Dict[str, Any]:
        """
        Perform a DuckDuckGo search and return formatted results with sources
        """
        if max_results is None:
            max_results = self.max_results
            
        try:
            # Perform the search
            results = list(self.ddgs.text(query, max_results=max_results))
            
            if not results:
                return {
                    "query": query,
                    "results": [],
                    "summary": f"No results found for query: '{query}'",
                    "sources": []
                }
            
            # Format results
            formatted_results = []
            sources = []
            
            for i, result in enumerate(results, 1):
                formatted_result = {
                    "rank": i,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                }
                formatted_results.append(formatted_result)
                sources.append({
                    "number": i,
                    "title": result.get("title", ""),
                    "url": result.get("href", "")
                })
            
            # Create a summary for grounding
            summary = f"Search results for '{query}':\n\n"
            for result in formatted_results:
                summary += f"{result['rank']}. {result['title']}\n"
                summary += f"   {result['snippet']}\n"
                summary += f"   Source: {result['url']}\n\n"
            
            return {
                "query": query,
                "results": formatted_results,
                "summary": summary,
                "sources": sources,
                "total_results": len(formatted_results)
            }
            
        except Exception as e:
            return {
                "query": query,
                "results": [],
                "summary": f"Error performing search: {str(e)}",
                "sources": [],
                "error": str(e)
            }
    
    def search_and_ground(self, query: str, user_question: str, claude_client) -> str:
        """
        Perform search and use results to ground Claude's response
        """
        search_results = self.search(query)
        
        if not search_results["results"]:
            grounding_prompt = f"""
User question: {user_question}
Search query used: {query}

No search results were found. Please provide the best answer you can based on your training data, 
and mention that you couldn't find current online information about this topic.
"""
        else:
            grounding_prompt = f"""
User question: {user_question}
Search query used: {query}

Here are current search results to help ground your response:

{search_results['summary']}

Please provide a comprehensive answer to the user's question using this current information. 
Make sure to cite the sources appropriately and distinguish between information from the search results 
and your general knowledge.

Sources found:
"""
            for source in search_results["sources"]:
                grounding_prompt += f"[{source['number']}] {source['title']} - {source['url']}\n"
        
        # Get grounded response from Claude
        response = claude_client.single_call(
            prompt=grounding_prompt,
            system_prompt="You are a helpful assistant that provides accurate, well-sourced information. When you use information from search results, cite the source numbers in your response."
        )
        
        return response

# Integration with the manual tool binding system
def create_search_tool_function():
    """Create the search tool function for integration with tool binding"""
    search_tool = DuckDuckGoSearchTool()
    
    def search_function(query: str, max_results: int = 5) -> str:
        """Search function that can be registered as a tool"""
        results = search_tool.search(query, max_results)
        
        # Return formatted results as a string for the LLM
        if results["results"]:
            response = f"Search Results for '{query}':\n\n"
            for result in results["results"]:
                response += f"{result['rank']}. **{result['title']}**\n"
                response += f"   {result['snippet']}\n"
                response += f"   Source: {result['url']}\n\n"
            return response
        else:
            return f"No search results found for query: '{query}'"
    
    return search_function

# Example usage
if __name__ == "__main__":
    # Direct usage
    search_tool = DuckDuckGoSearchTool()
    
    # Test search
    results = search_tool.search("Python programming best practices 2024")
    print("Search Results:")
    print(json.dumps(results, indent=2))
    
    # Test with Claude integration
    from claude_basic_setup import ClaudeClient
    claude = ClaudeClient()
    
    grounded_response = search_tool.search_and_ground(
        query="latest Python features 2024",
        user_question="What are the newest Python features I should know about?",
        claude_client=claude
    )
    print("\nGrounded Response:")
    print(grounded_response)
    
    # Integration with tool binding system
    from langgraph_manual_tools import ManualToolBinding
    
    tool_binding = ManualToolBinding(claude)
    search_func = create_search_tool_function()
    
    tool_binding.register_tool(
        name="web_search",
        func=search_func,
        description="Search the web using DuckDuckGo for current information",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {"type": "integer", "default": 5, "description": "Maximum number of results"}
            },
            "required": ["query"]
        }
    )