import pandas as pd

class DataProcessor:
    def normalize_data(self, data: Dict) -> pd.DataFrame:
        return pd.DataFrame([data])

data_processor = DataProcessor()
normalized_data = data_processor.normalize_data({"company": "TSLA", "metric": "revenue", "value": 1000000})
print(normalized_data)
