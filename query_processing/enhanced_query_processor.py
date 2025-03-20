import re
from typing import Dict, List, Tuple
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class EnhancedQueryProcessor:
    def __init__(self, llm_api_key: str):
        # Load NER model for financial entity extraction
        self.nlp = spacy.load("en_core_web_lg")
        
        # Connect to LLM for query understanding
        self.llm = OpenAI(api_key=llm_api_key)
        
        # Initialize company to ticker mapping database
        self.company_to_ticker = self._initialize_company_database()
        
        # Create matcher for financial metrics
        self.matcher = Matcher(self.nlp.vocab)
        self.metric_patterns = self._create_financial_metric_patterns()
        
    def _initialize_company_database(self) -> Dict[str, str]:
        # In production, this would connect to a comprehensive database
        # For now, we'll use a small example dict
        return {
            "tesla": "TSLA",
            "apple": "AAPL",
            "nvidia": "NVDA",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META"
            # Would include thousands more in production
        }
        
    def _create_financial_metric_patterns(self):
        # Register patterns for financial metrics
        self.matcher.add("REVENUE", [[{"LOWER": "revenue"}]])
        self.matcher.add("EBITDA", [[{"LOWER": "ebitda"}]])
        self.matcher.add("EPS", [[{"LOWER": "eps"}, {"LOWER": "earnings"}, {"LOWER": "per"}, {"LOWER": "share"}]])
        self.matcher.add("PE_RATIO", [[{"LOWER": "p/e"}, {"LOWER": "ratio"}]])
        self.matcher.add("INTEREST_RATE", [[{"LOWER": "interest"}, {"LOWER": "rate"}]])
        # Many more financial metrics would be added
        
    def extract_companies(self, query: str) -> List[Dict[str, str]]:
        """Extract company entities and map to stock tickers"""
        doc = self.nlp(query.lower())
        companies = []
        
        # Extract organization entities
        for ent in doc.ents:
            if ent.label_ == "ORG":
                company_name = ent.text.lower()
                if company_name in self.company_to_ticker:
                    companies.append({
                        "name": company_name,
                        "ticker": self.company_to_ticker[company_name]
                    })
        
        # Also check for ticker symbols directly in text
        ticker_pattern = r'\b[A-Z]{1,5}\b'  # Simple pattern for stock tickers
        potential_tickers = re.findall(ticker_pattern, query)
        for ticker in potential_tickers:
            # Verify if it's a valid ticker (would connect to a ticker validation service)
            companies.append({
                "name": ticker,
                "ticker": ticker
            })
            
        return companies
    
    def extract_time_frame(self, query: str) -> Dict[str, str]:
        """Extract time frame information from query"""
        # Using LLM to extract time frame information
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""
            Extract the time frame from this financial query: {query}
            
            Return the result as a JSON with:
            - start_date: YYYY-MM-DD or 'None' if not specified
            - end_date: YYYY-MM-DD or 'None' if not specified
            - period: (e.g., '5 years', 'Q3 2024', etc.) or 'None' if not specified
            """
        )
        
        prompt = prompt_template.format(query=query)
        time_frame_json = self.llm(prompt)
        
        # In a real implementation, we would parse the JSON response
        # For this example, we'll return a simplified version
        
        # Simple regex extraction as fallback
        year_pattern = r'\b\d{4}\b'
        years = re.findall(year_pattern, query)
        
        quarter_pattern = r'\bQ[1-4]\s+\d{4}\b'
        quarters = re.findall(quarter_pattern, query)
        
        time_period_pattern = r'\blast\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b'
        period_match = re.search(time_period_pattern, query)
        
        return {
            "years": years,
            "quarters": quarters,
            "period": period_match.group(0) if period_match else None
        }
    
    def extract_metrics(self, query: str) -> List[str]:
        """Extract financial metrics of interest"""
        doc = self.nlp(query)
        matches = self.matcher(doc)
        
        metrics = []
        for match_id, start, end in matches:
            span = doc[start:end]
            metrics.append(span.text)
            
        # Add additional logic for complex metrics
        if "financials" in query.lower():
            metrics.extend(["revenue", "profit", "ebitda", "eps", "cash flow"])
            
        return metrics
    
    def determine_analysis_type(self, query: str) -> str:
        """Determine the type of financial analysis requested"""
        analysis_types = {
            "summarize": "summary",
            "analyze": "analysis",
            "compare": "comparison",
            "benchmark": "benchmarking",
            "forecast": "forecast",
            "predict": "prediction",
            "impact": "impact_analysis"
        }
        
        for keyword, analysis_type in analysis_types.items():
            if keyword in query.lower():
                return analysis_type
                
        # Default to summary if no specific type detected
        return "summary"
    
    def process_query(self, query: str) -> Dict:
        """Main method to process financial queries"""
        # Extract all relevant information
        companies = self.extract_companies(query)
        time_frame = self.extract_time_frame(query)
        metrics = self.extract_metrics(query)
        analysis_type = self.determine_analysis_type(query)
        
        # Determine which APIs to query based on the extracted information
        apis_to_query = self._select_apis(metrics, analysis_type)
        
        return {
            "companies": companies,
            "time_frame": time_frame,
            "metrics": metrics,
            "analysis_type": analysis_type,
            "apis_to_query": apis_to_query
        }
    
    def _select_apis(self, metrics: List[str], analysis_type: str) -> List[str]:
        """Select which financial APIs to query based on metrics and analysis type"""
        apis = []
        
        if any(m in ["revenue", "profit", "ebitda", "eps", "financials"] for m in metrics):
            apis.append("alpha_vantage_fundamentals")
            
        if analysis_type in ["summary", "analysis"]:
            apis.append("yahoo_finance_summary")
            
        if "technical" in metrics or analysis_type == "technical_analysis":
            apis.append("twelve_data_technical")
            
        # Always include price data
        apis.append("yahoo_finance_price")
        
        return apis
