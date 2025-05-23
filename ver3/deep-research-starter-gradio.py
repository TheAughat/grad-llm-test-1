import time
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import gradio as gr
# Placeholder PDF parser import (e.g. PyMuPDF or pdfminer)
# import fitz  # PyMuPDF

# LangGraph core imports (assuming a LangChain-style API)
from langgraph import Graph, Node, Edge, Tool

# ProxyLLM wrapper for Claude
class ClaudeTool:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate(self, prompt: str) -> str:
        # Placeholder: inject any required API parameters
        return self.llm.invoke(prompt)

# Tool: DuckDuckGo search
class DuckDuckGoSearchTool(Tool):
    name = "duckduckgo_search"

    def run(self, query: str, max_results: int = 5) -> list:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body"),
                })
        time.sleep(1)  # throttle
        return results

# Tool: Web scraper
class ScrapeTool(Tool):
    name = "scrape"

    def run(self, url: str) -> str:
        # Respect robots.txt externally if needed
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "lxml")
        # Simple text extraction; replace with trafilatura/newspaper3k if desired
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text() for p in paragraphs)

# Define prompts (placeholders to be filled dynamically)
PROMPTS = {
    "refine_query": "<REFINE QUERY PROMPT TEMPLATE>\n
User asked: '{input_query}'\n
Previous results: {previous_snippets}\n
Generate a refined search query.",
    "synthesis": "<SYNTHESIS PROMPT TEMPLATE>\n
Context snippets: {snippets}\n
Question: {input_query}\n
Answer with inline citations.",
}

# Build LangGraph workflow
graph = Graph(name="DeepResearchClone")

# Nodes
graph.add_node(Node(
    name="Input",
    action=lambda state: state.update({"query": state.get("user_input")}) or state,
    description="Accept raw user input",
    entrypoint=True
))

graph.add_node(Node(
    name="GenerateQuery",
    tool=DuckDuckGoSearchTool(),
    action=lambda state: state.update({
        "search_query": PROMPTS["refine_query"].format(
            input_query=state["query"],
            previous_snippets=state.get("snippets", "")
        )
    }) or state,
    description="Refine or rephrase the user query for search"
))

graph.add_node(Node(
    name="Search",
    tool=DuckDuckGoSearchTool(),
    action=lambda state: state.update({
        "results": DuckDuckGoSearchTool().run(state["search_query"])
    }) or state,
    description="Perform DuckDuckGo search"
))

graph.add_node(Node(
    name="Scrape",
    tool=ScrapeTool(),
    action=lambda state: state.update({
        "snippets": [ScrapeTool().run(item["link"]) for item in state["results"]]
    }) or state,
    description="Scrape and extract text from search results"
))

graph.add_node(Node(
    name="Synthesize",
    tool=ClaudeTool(p_llm),
    action=lambda state: state.update({
        "answer": ClaudeTool(p_llm).generate(
            PROMPTS["synthesis"].format(
                snippets="\n".join(state["snippets"][:5]),
                input_query=state["query"]
            )
        )
    }) or state,
    description="Use Claude to synthesize an answer with citations"
))

graph.add_node(Node(
    name="Output",
    action=lambda state: state,
    exitpoint=True,
    description="Return final markdown answer"
))

# Edges
graph.add_edge(Edge("Input", "GenerateQuery"))
graph.add_edge(Edge("GenerateQuery", "Search"))
graph.add_edge(Edge("Search", "Scrape"))
graph.add_edge(Edge("Scrape", "Synthesize"))
graph.add_edge(Edge("Synthesize", "Output"))

# Gradio interface
def deepresearch_interface(user_input):
    initial_state = {"user_input": user_input}
    final_state = graph.run(initial_state)
    return final_state.get("answer", "No response generated.")

iface = gr.Interface(
    fn=deepresearch_interface,
    inputs=gr.Textbox(lines=2, label="Enter Research Question"),
    outputs=gr.Markdown(label="Generated Answer"),
    title="DeepResearch (LLM + Search)",
    description="Ask a complex research question. The system will search online, scrape content, and synthesize an answer."
)

if __name__ == "__main__":
    iface.launch()
