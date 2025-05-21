class SupervisorAgent:
    def __init__(self, sec_agent, market_agent, technical_agent):
        self.sec_agent = sec_agent
        self.market_agent = market_agent
        self.technical_agent = technical_agent

    def coordinate_workflow(self, company: str):
        sec_analysis = self.sec_agent.analyze_sec_filings(company)
        market_data = self.market_agent.gather_market_data(company)
        technical_analysis = self.technical_agent.perform_technical_analysis(company)

        report = {
            "company": company,
            "sec_analysis": sec_analysis,
            "market_data": market_data,
            "technical_analysis": technical_analysis
        }
        return report

supervisor_agent = SupervisorAgent(sec_agent, market_agent, technical_agent)
report = supervisor_agent.coordinate_workflow("TSLA")
print(report)
