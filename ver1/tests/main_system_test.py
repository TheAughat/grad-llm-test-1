class FinancialAnalysisSystem:
    def __init__(self, openai_api_key, alpha_vantage_key, twelve_data_key):
        # Initialize components
        self.api_keys = {
            "openai": openai_api_key,
            "alpha_vantage": alpha_vantage_key,
            "twelve_data": twelve_data_key
        }
        
        # Create LLM instance
        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4")
        
        # Initialize components
        self.query_processor = EnhancedQueryProcessor(openai_api_key)
        self.api_connector = EnhancedAPIConnector(self.api_keys)
        
        # Create the workflow graph
        self.workflow = create_financial_analysis_graph(
            self.api_connector,
            self.query_processor,
            self.llm
        )
    
    def process_financial_query(self, query: str):
        """Process a financial query and return a comprehensive report"""
        # Initialize the state
        initial_state = {
            "query": query,
            "query_parameters": {},
            "api_results": {},
            "sec_analysis": {},
            "market_analysis": {},
            "technical_analysis": {},
            "report": {},
            "error": ""
        }
        
        # Execute the workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Check for errors
        if final_state["error"]:
            return {"error": final_state["error"]}
        
        # Generate visualizations
        visualizations = generate_visualizations(final_state["api_results"], final_state["report"])
        
        # Add visualizations to the report
        final_state["report"]["visualizations"] = list(visualizations.keys())
        
        return {
            "report": final_state["report"],
            "visualizations": visualizations
        }

# Usage example
if __name__ == "__main__":
    system = FinancialAnalysisSystem(
        openai_api_key="your_openai_api_key",
        alpha_vantage_key="your_alpha_vantage_key",
        twelve_data_key="your_twelve_data_key"
    )
    
    # Process a financial query
    result = system.process_financial_query("Analyze the impact of recent interest rate changes on the housing sector")
    
    # Print the report
    print(json.dumps(result["report"], indent=2))
    
    # Display visualizations
    for name, fig in result["visualizations"].items():
        plt.figure(fig.number)
        plt.show()
