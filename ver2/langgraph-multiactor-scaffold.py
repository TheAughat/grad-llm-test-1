from langgraph.graph import Graph, Node, Edge, State
from typing import Dict, List

# --- Define the shared LangGraph state ---
class PitchbookState(State):
    user_prompt: str
    profile: Dict = {}
    public_data: Dict = {}
    market_summary: str = ""
    internal_matches: List[Dict] = []
    comps: Dict = {}
    chart: Dict = {}
    draft: str = ""
    refined_draft: str = ""
    final_pdf_path: str = ""

# --- Define your agent-like functions ---
def client_profiling_agent(state: PitchbookState):
    prompt = f"Extract company_name, sector, region, pitch_type, and company_size from: {state.user_prompt}"
    profile = call_claude(prompt)
    return {"profile": profile}


def public_data_collector(state: PitchbookState):
    company = state.profile["company_name"]
    sec_summary = fetch_sec_summary(company)
    yf_data = fetch_yahoo_finance(company)
    return {"public_data": {"sec_summary": sec_summary, **yf_data}}


def market_landscape_agent(state: PitchbookState):
    sector = state.profile["sector"]
    search_results = run_duckduckgo_search(sector)
    summary = call_claude(f"Summarize trends and competitors from: {search_results}")
    return {"market_summary": summary}


def internal_relevance_finder(state: PitchbookState):
    matches = query_internal_deals(state.profile, top_k=3)
    return {"internal_matches": matches}


def comparables_generator(state: PitchbookState):
    comps = fetch_comparables(state.profile["sector"])
    return {"comps": comps}


def infographics_generator(state: PitchbookState):
    chart_spec = call_claude(f"Based on these comps and deals, suggest chart type and data: {state.comps} and {state.internal_matches}")
    chart = render_chart(chart_spec)
    return {"chart": chart}


def narrative_drafting_agent(state: PitchbookState):
    prompt = f"Generate a structured pitchbook in Markdown using this data: Profile={state.profile}, Market={state.market_summary}, Deals={state.internal_matches}, Comps={state.comps}, Chart={state.chart}"
    draft = call_claude(prompt)
    return {"draft": draft}


def critique_refinement_agent(state: PitchbookState):
    refined = call_claude(f"Review and improve this pitchbook Markdown: {state.draft}")
    return {"refined_draft": refined}


def output_compiler(state: PitchbookState):
    path = convert_md_to_pdf(state.refined_draft)
    return {"final_pdf_path": path}

# --- Build the Graph ---
graph = Graph(name="PitchbookGeneration", state_type=PitchbookState)

graph.add_node("ClientProfiling", client_profiling_agent)
graph.add_node("PublicData", public_data_collector)
graph.add_node("MarketLandscape", market_landscape_agent)
graph.add_node("InternalMatches", internal_relevance_finder)
graph.add_node("Comparables", comparables_generator)
graph.add_node("Infographics", infographics_generator)
graph.add_node("DraftNarrative", narrative_drafting_agent)
graph.add_node("CritiqueRefine", critique_refinement_agent)
graph.add_node("CompileOutput", output_compiler)

# Edges define dataflow order
graph.add_edge("ClientProfiling", "PublicData")
graph.add_edge("PublicData", "MarketLandscape")
graph.add_edge("MarketLandscape", "InternalMatches")
graph.add_edge("InternalMatches", "Comparables")
graph.add_edge("Comparables", "Infographics")
graph.add_edge("Infographics", "DraftNarrative")
graph.add_edge("DraftNarrative", "CritiqueRefine")
graph.add_edge("CritiqueRefine", "CompileOutput")

# --- Orchestration ---
def run_pitchbook_pipeline(user_prompt: str):
    initial_state = PitchbookState(user_prompt=user_prompt)
    final_state = graph.invoke(initial_state)
    return final_state.final_pdf_path

# Example
if __name__ == "__main__":
    pdf_path = run_pitchbook_pipeline("Create a pitchbook for XYZ Corp, a mid-cap fintech in New York")
    print(f"Generated pitchbook PDF: {pdf_path}")
