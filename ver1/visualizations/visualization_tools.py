import matplotlib.pyplot as plt

class ReportGenerator:
    def generate_report(self, company: str, sec_analysis: Dict, market_data: Dict, technical_analysis: Dict):
        report = f"""
            Financial Report for {company}
            ======================================
            SEC Analysis: {sec_analysis['insights']}
            Market Data: {market_data['market_data']}
            Technical Analysis: {technical_analysis['technical_analysis']}
            """
        return report

    def generate_visualization(self, data: pd.DataFrame):
        plt.figure(figsize=(10, 6))
        plt.plot(data['date'], data['value'], marker='o')
        plt.title("Stock Performance")
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.grid(True)
        plt.show()

report_generator = ReportGenerator()
data_to_visualize = pd.DataFrame({"date": ["2025-01-01", "2025-01-02"], "value": [100, 110]})
report_generator.generate_visualization(data_to_visualize)
