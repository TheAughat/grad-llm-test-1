import re
from typing import Dict

class QueryProcessor:
    def process_query(self, query: str) -> Dict[str, str]:
        company_pattern = r"\b(TSLA|Tesla|AAPL|Apple|NVDA|NVIDIA)\b"
        time_frame_pattern = r"\b(last \d+ years|Q\d+ \d{4}|\d{4})\b"
        metric_pattern = r"\b(financials|revenue|EBITDA|profit|loss|interest rates|housing sector)\b"

        company = re.search(company_pattern, query, re.IGNORECASE)
        time_frame = re.search(time_frame_pattern, query, re.IGNORECASE)
        metric = re.search(metric_pattern, query, re.IGNORECASE)

        return {
            "company": company.group(0) if company else None,
            "time_frame": time_frame.group(0) if time_frame else None,
            "metric": metric.group(0) if metric else None
        }

query_processor = QueryProcessor()
example_query = "Summarize TSLA's financials over the last 5 years"
processed_query = query_processor.process_query(example_query)
print(processed_query)
