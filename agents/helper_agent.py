from typing import Dict, List, Any, TypedDict, Annotated, Literal
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from langgraph.graph import END, StateGraph

# Define the state schema
class FinancialAnalysisState(TypedDict):
    query: str
    query_parameters: Dict[str, Any]
    api_results: Dict[str, Any]
    sec_analysis: Dict[str, Any]
    market_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    report: Dict[str, Any]
    error: str

def create_financial_analysis_graph(api_connector, query_processor, llm):
    # Initialize the state graph
    workflow = StateGraph(FinancialAnalysisState)
    
    # Define the nodes
    
    # Query Processing Node
    def process_query(state: FinancialAnalysisState) -> FinancialAnalysisState:
        query = state["query"]
        try:
            query_parameters = query_processor.process_query(query)
            return {"query_parameters": query_parameters}
        except Exception as e:
            return {"error": f"Error processing query: {str(e)}"}
    
    # API Querying Node
    def query_apis(state: FinancialAnalysisState) -> FinancialAnalysisState:
        query_parameters = state["query_parameters"]
        try:
            api_results = api_connector.query_apis(query_parameters)
            return {"api_results": api_results}
        except Exception as e:
            return {"error": f"Error querying APIs: {str(e)}"}
    
    # SEC Analysis Node
    def analyze_sec_filings(state: FinancialAnalysisState) -> FinancialAnalysisState:
        api_results = state["api_results"]
        query_parameters = state["query_parameters"]
        
        prompt_template = PromptTemplate(
            input_variables=["api_results", "query_parameters"],
            template="""
            As a financial SEC filing expert, analyze the following financial data:
            
            API Results: 
            {api_results}
            
            Query Parameters:
            {query_parameters}
            
            Provide an analysis focused on SEC filing data, financial statements, and official company disclosures.
            Focus on the official financial metrics requested in the query.
            
            Return your analysis as a JSON with keys for insights, key_metrics, and trends.
            """
        )
        
        prompt = prompt_template.format(
            api_results=json.dumps(api_results),
            query_parameters=json.dumps(query_parameters)
        )
        
        sec_analysis = json.loads(llm(prompt))
        return {"sec_analysis": sec_analysis}
    
    # Market Research Node
    def perform_market_research(state: FinancialAnalysisState) -> FinancialAnalysisState:
        api_results = state["api_results"]
        query_parameters = state["query_parameters"]
        
        prompt_template = PromptTemplate(
            input_variables=["api_results", "query_parameters"],
            template="""
            As a market research expert, analyze the following financial data:
            
            API Results: 
            {api_results}
            
            Query Parameters:
            {query_parameters}
            
            Provide market context, competitor analysis, and industry trends that relate to the query.
            Focus on market positioning, analyst sentiment, and news impact.
            
            Return your analysis as a JSON with keys for market_context, competitor_analysis, and news_impact.
            """
        )
        
        prompt = prompt_template.format(
            api_results=json.dumps(api_results),
            query_parameters=json.dumps(query_parameters)
        )
        
        market_analysis = json.loads(llm(prompt))
        return {"market_analysis": market_analysis}
    
    # Technical Analysis Node
    def perform_technical_analysis(state: FinancialAnalysisState) -> FinancialAnalysisState:
        api_results = state["api_results"]
        query_parameters = state["query_parameters"]
        
        # Only perform technical analysis if price data is available
        if not any("price_history" in key for key in api_results.keys()):
            return {"technical_analysis": {"message": "No price data available for technical analysis"}}
        
        prompt_template = PromptTemplate(
            input_variables=["api_results", "query_parameters"],
            template="""
            As a technical analysis expert, analyze the following price and technical indicator data:
            
            API Results: 
            {api_results}
            
            Query Parameters:
            {query_parameters}
            
            Provide technical analysis of price patterns, indicators, and trading signals.
            Focus on trend direction, support/resistance levels, and indicator readings.
            
            Return your analysis as a JSON with keys for trend_analysis, support_resistance, and indicator_signals.
            """
        )
        
        prompt = prompt_template.format(
            api_results=json.dumps(api_results),
            query_parameters=json.dumps(query_parameters)
        )
        
        technical_analysis = json.loads(llm(prompt))
        return {"technical_analysis": technical_analysis}
    
    # Report Generation Node
    def generate_report(state: FinancialAnalysisState) -> FinancialAnalysisState:
        query = state["query"]
        query_parameters = state["query_parameters"]
        sec_analysis = state.get("sec_analysis", {})
        market_analysis = state.get("market_analysis", {})
        technical_analysis = state.get("technical_analysis", {})
        
        prompt_template = PromptTemplate(
            input_variables=["query", "query_parameters", "sec_analysis", "market_analysis", "technical_analysis"],
            template="""
            Generate a comprehensive financial report answering this query: {query}
            
            Base your report on these analyses:
            
            SEC Filing Analysis: {sec_analysis}
            Market Research: {market_analysis}
            Technical Analysis: {technical_analysis}
            
            The report should be comprehensive and address all aspects of the query.
            Include sections for:
            1. Executive Summary
            2. Financial Performance Analysis
            3. Market Context and Positioning
            4. Technical Outlook
            5. Conclusion and Recommendations
            
            Return your report as a JSON with keys for each section, and a visualizations key that specifies what charts should be generated.
            """
        )
        
        prompt = prompt_template.format(
            query=query,
            query_parameters=json.dumps(query_parameters),
            sec_analysis=json.dumps(sec_analysis),
            market_analysis=json.dumps(market_analysis),
            technical_analysis=json.dumps(technical_analysis)
        )
        
        report = json.loads(llm(prompt))
        return {"report": report}
    
    # Add nodes to the graph
    workflow.add_node("process_query", process_query)
    workflow.add_node("query_apis", query_apis)
    workflow.add_node("analyze_sec_filings", analyze_sec_filings)
    workflow.add_node("perform_market_research", perform_market_research)
    workflow.add_node("perform_technical_analysis", perform_technical_analysis)
    workflow.add_node("generate_report", generate_report)
    
    # Define edges (workflow)
    workflow.add_edge("process_query", "query_apis")
    workflow.add_edge("query_apis", "analyze_sec_filings")
    workflow.add_edge("analyze_sec_filings", "perform_market_research")
    workflow.add_edge("perform_market_research", "perform_technical_analysis")
    workflow.add_edge("perform_technical_analysis", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # Error handling
    def should_end(state: FinancialAnalysisState) -> Literal["continue", "end"]:
        if state.get("error"):
            return "end"
        return "continue"
    
    workflow.add_conditional_edges(
        "process_query",
        should_end,
        {
            "continue": "query_apis",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "query_apis",
        should_end,
        {
            "continue": "analyze_sec_filings",
            "end": END
        }
    )
    
    # Set the entry point
    workflow.set_entry_point("process_query")
    
    return workflow.compile()

# Visualization function
def generate_visualizations(api_results, report):
    """Generate visualizations based on API results and report specifications"""
    visualizations = {}
    
    # Create various visualizations based on report requirements
    for ticker, price_data in ((k.replace("_price_history", ""), v) for k, v in api_results.items() if "_price_history" in k):
        if isinstance(price_data, pd.DataFrame) and 'Close' in price_data.columns:
            # Price chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(price_data.index, price_data['Close'])
            ax.set_title(f"{ticker} Stock Price")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.grid(True)
            visualizations[f"{ticker}_price_chart"] = fig
            
            # Volume chart
            if 'Volume' in price_data.columns:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(price_data.index, price_data['Volume'])
                ax.set_title(f"{ticker} Trading Volume")
                ax.set_xlabel("Date")
                ax.set_ylabel("Volume")
                visualizations[f"{ticker}_volume_chart"] = fig
    
    # Create more visualizations based on fundamental data
    for ticker, fundamentals in ((k.replace("_fundamentals", ""), v) for k, v in api_results.items() if "_fundamentals" in k):
        if "income_statement" in fundamentals and "annualReports" in fundamentals["income_statement"]:
            try:
                # Extract revenue data
                annual_reports = fundamentals["income_statement"]["annualReports"]
                years = [report["fiscalDateEnding"] for report in annual_reports]
                revenue = [float(report["totalRevenue"]) for report in annual_reports]
                
                # Revenue chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(years, revenue)
                ax.set_title(f"{ticker} Annual Revenue")
                ax.set_xlabel("Fiscal Year")
                ax.set_ylabel("Revenue")
                plt.xticks(rotation=45)
                visualizations[f"{ticker}_revenue_chart"] = fig
            except (KeyError, ValueError) as e:
                print(f"Error creating revenue chart: {e}")
    
    return visualizations
