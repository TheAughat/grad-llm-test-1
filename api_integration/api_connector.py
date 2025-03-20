import requests

class APIConnector:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys

    def fetch_alpha_vantage_data(self, symbol: str) -> Dict:
        base_url = "https://www.alphavantage.co/query"
        params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": self.api_keys["alpha_vantage"]}
        response = requests.get(base_url, params=params)
        return response.json()

api_keys = {"alpha_vantage": "demo"}
api_connector = APIConnector(api_keys)
data = api_connector.fetch_alpha_vantage_data("TSLA")
print(data)
