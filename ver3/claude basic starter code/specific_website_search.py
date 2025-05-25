import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import time
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

class SpecificWebsiteSearchTool:
    """
    Search tool that specifically searches within given websites
    Regardless of whether results are found, it attempts to search the specified sites
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_specific_websites(self, query: str, websites: List[str], max_results_per_site: int = 3) -> Dict[str, Any]:
        """
        Search for information within specific websites
        
        Args:
            query: The search query
            websites: List of website URLs/domains to search within
            max_results_per_site: Maximum results per website
        """
        all_results = []
        site_results = {}
        
        for website in websites:
            site_results[website] = {
                "results": [],
                "error": None,
                "searched": True
            }
            
            try:
                # Use site-specific search with DuckDuckGo
                site_query = f"site:{website} {query}"
                results = list(self.ddgs.text(site_query, max_results=max_results_per_site))
                
                if results:
                    formatted_results = []
                    for i, result in enumerate(results):
                        formatted_result = {
                            "title": result.get("title", ""),
                            "snippet": result.get("body", ""),
                            "url": result.get("href", ""),
                            "website": website,
                            "rank": len(all_results) + i + 1
                        }
                        formatted_results.append(formatted_result)
                        all_results.append(formatted_result)
                    
                    site_results[website]["results"] = formatted_results
                else:
                    # If no results from search, try direct scraping
                    scraped_content = self._try_direct_scrape(website, query)
                    if scraped_content:
                        site_results[website]["results"] = [scraped_content]
                        all_results.append(scraped_content)
                
                # Add small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                site_results[website]["error"] = str(e)
                # Still try direct scraping even if search fails
                try:
                    scraped_content = self._try_direct_scrape(website, query)
                    if scraped_content:
                        site_results[website]["results"] = [scraped_content]
                        all_results.append(scraped_content)
                except Exception as scrape_error:
                    site_results[website]["error"] = f"Search error: {str(e)}, Scrape error: {str(scrape_error)}"
        
        return {
            "query": query,
            "websites_searched": websites,
            "all_results": all_results,
            "results_by_site": site_results,
            "total_results": len(all_results),
            "summary": self._create_summary(query, all_results, websites)
        }
    
    def _try_direct_scrape(self, website: str, query: str) -> Dict[str, Any]:
        """
        Attempt to scrape the website directly for relevant content
        This is a fallback when search doesn't return results
        """
        try:
            # Ensure proper URL format
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            
            response = self.session.get(website, timeout=self.timeout)
            response.raise_for_status()
            
            soap = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soap(["script", "style"]):
                script.extract()
            
            # Get text content
            text = soap.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Simple relevance check - look for query terms
            query_terms = query.lower().split()
            text_lower = text.lower()
            
            relevant_snippets = []
            sentences = text.split('.')
            
            for sentence in sentences[:50]:  # Limit to first 50 sentences
                if any(term in sentence.lower() for term in query_terms):
                    relevant_snippets.append(sentence.strip())
                    if len(relevant_snippets) >= 3:  # Limit snippets
                        break
            
            if relevant_snippets:
                return {
                    "title": f"Direct content from {website}",
                    "snippet": " ... ".join(relevant_snippets),
                    "url": website,
                    "website": website,
                    "rank": 999,  # Mark as scraped content
                    "source_type": "direct_scrape"
                }
            
        except Exception as e:
            # Silently fail for direct scraping
            pass
            
        return None
    
    def _create_summary(self, query: str, results: List[Dict], websites: List[str]) -> str:
        """Create a summary of the search results"""
        if not results:
            return f"No results found for '{query}' on the specified websites: {', '.join(websites)}"
        
        summary = f"Found {len(results)} results for '{query}' across specified websites:\n\n"
        
        for result in results:
            summary += f"• **{result['title']}**\n"
            summary += f"  {result['snippet'][:200]}{'...' if len(result['snippet']) > 200 else ''}\n"
            summary += f"  Source: {result['url']}\n"
            if result.get('source_type') == 'direct_scrape':
                summary += f"  (Content found via direct website analysis)\n"
            summary += "\n"
        
        return summary

def create_website_search_tool_function():
    """Create the website search tool function for integration"""
    search_tool = SpecificWebsiteSearchTool()
    
    def website_search_function(query: str, websites: List[str], max_results_per_site: int = 3) -> str:
        """Website search function that can be registered as a tool"""
        if isinstance(websites, str):
            # Handle single website passed as string
            websites = [websites]
        
        results = search_tool.search_specific_websites(query, websites, max_results_per_site)
        
        if results["all_results"]:
            response = f"Results from specific websites for '{query}':\n\n"
            response += results["summary"]
            
            # Add site-by-site breakdown
            response += "\n--- Results by Website ---\n"
            for site, site_data in results["results_by_site"].items():
                response += f"\n**{site}:**\n"
                if site_data["results"]:
                    response += f"  Found {len(site_data['results'])} result(s)\n"
                elif site_data["error"]:
                    response += f"  Error: {site_data['error']}\n"
                else:
                    response += f"  No results found\n"
        else:
            response = f"No results found for '{query}' on any of the specified websites: {', '.join(websites)}\n\n"
            response += "Websites searched:\n"
            for site, site_data in results["results_by_site"].items():
                response += f"• {site}: {'Error - ' + site_data['error'] if site_data['error'] else 'No results'}\n"
        
        return response
    
    return search_tool, website_search_function

# Example usage
if __name__ == "__main__":
    search_tool = SpecificWebsiteSearchTool()
    
    # Test searching specific websites
    websites_to_search = [
        "python.org",
        "docs.python.org",
        "realpython.com"
    ]
    
    results = search_tool.search_specific_websites(
        query="asyncio tutorial",
        websites=websites_to_search,
        max_results_per_site=2
    )
    
    print("Specific Website Search Results:")
    print(results["summary"])
    
    # Integration with tool binding
    from langgraph_manual_tools import ManualToolBinding
    from claude_basic_setup import ClaudeClient
    
    claude = ClaudeClient()
    tool_binding = ManualToolBinding(claude)
    
    _, website_search_func = create_website_search_tool_function()
    
    tool_binding.register_tool(
        name="website_search",
        func=website_search_func,
        description="Search for information within specific websites only",
        parameters={
            "type": "object", 
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "websites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of website domains to search within"
                },
                "max_results_per_site": {"type": "integer", "default": 3}
            },
            "required": ["query", "websites"]
        }
    )