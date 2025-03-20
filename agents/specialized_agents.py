class SECFilingAgent:
    def analyze_sec_filings(self, company: str):
        return {"company": company, "insights": "Analyzed SEC filings."}

class MarketResearchAgent:
    def gather_market_data(self, company: str):
        return {"company": company, "market_data": "Collected market data."}

class TechnicalAnalysisAgent:
    def perform_technical_analysis(self, company: str):
        return {"company": company, "technical_analysis": "Performed technical analysis."}

sec_agent = SECFilingAgent()
market_agent = MarketResearchAgent()
technical_agent = TechnicalAnalysisAgent()

sec_analysis = sec_agent.analyze_sec_filings("TSLA")
market_data = market_agent.gather_market_data("TSLA")
technical_analysis = technical_agent.perform_technical_analysis("TSLA")

print(sec_analysis)
print(market_data)
print(technical_analysis)
