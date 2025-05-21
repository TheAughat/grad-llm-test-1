import requests
import pandas as pd
import yfinance as yf
from typing import Dict, List, Any, Union
import time

class EnhancedAPIConnector:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.cache = {}  # Simple in-memory cache
        
    def query_apis(self, query_params: Dict) -> Dict[str, Any]:
        """Query multiple financial APIs based on processed query parameters"""
        results = {}
        apis_to_query = query_params.get("apis_to_query", [])
        
        for api in apis_to_query:
            if api == "alpha_vantage_fundamentals":
                for company in query_params["companies"]:
                    ticker = company["ticker"]
                    results[f"{ticker}_fundamentals"] = self.get_alpha_vantage_fundamentals(ticker)
                    
            elif api == "yahoo_finance_summary":
                for company in query_params["companies"]:
                    ticker = company["ticker"]
                    results[f"{ticker}_summary"] = self.get_yahoo_finance_summary(ticker)
                    
            elif api == "yahoo_finance_price":
                for company in query_params["companies"]:
                    ticker = company["ticker"]
                    time_frame = query_params["time_frame"]
                    results[f"{ticker}_price_history"] = self.get_yahoo_finance_price_history(ticker, time_frame)
                    
            elif api == "twelve_data_technical":
                for company in query_params["companies"]:
                    ticker = company["ticker"]
                    results[f"{ticker}_technical"] = self.get_twelve_data_technical(ticker)
        
        return results
    
    def get_alpha_vantage_fundamentals(self, ticker: str) -> Dict:
        """Get fundamental financial data from Alpha Vantage"""
        cache_key = f"av_fundamentals_{ticker}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        base_url = "https://www.alphavantage.co/query"
        
        # Income Statement
        income_params = {
            "function": "INCOME_STATEMENT",
            "symbol": ticker,
            "apikey": self.api_keys["alpha_vantage"]
        }
        income_response = requests.get(base_url, params=income_params)
        income_data = income_response.json()
        
        # Balance Sheet
        balance_params = {
            "function": "BALANCE_SHEET",
            "symbol": ticker,
            "apikey": self.api_keys["alpha_vantage"]
        }
        balance_response = requests.get(base_url, params=balance_params)
        balance_data = balance_response.json()
        
        # Cash Flow
        cash_flow_params = {
            "function": "CASH_FLOW",
            "symbol": ticker,
            "apikey": self.api_keys["alpha_vantage"]
        }
        cash_flow_response = requests.get(base_url, params=cash_flow_params)
        cash_flow_data = cash_flow_response.json()
        
        # Overview
        overview_params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": self.api_keys["alpha_vantage"]
        }
        overview_response = requests.get(base_url, params=overview_params)
        overview_data = overview_response.json()
        
        result = {
            "income_statement": income_data,
            "balance_sheet": balance_data,
            "cash_flow": cash_flow_data,
            "overview": overview_data
        }
        
        # Cache the result
        self.cache[cache_key] = result
        
        return result
    
    def get_yahoo_finance_summary(self, ticker: str) -> Dict:
        """Get company summary from Yahoo Finance"""
        cache_key = f"yf_summary_{ticker}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            result = {
                "info": info,
                "recommendations": stock.recommendations,
                "major_holders": stock.major_holders,
                "institutional_holders": stock.institutional_holders,
                "news": stock.news
            }
            
            # Cache the result
            self.cache[cache_key] = result
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_yahoo_finance_price_history(self, ticker: str, time_frame: Dict) -> pd.DataFrame:
        """Get historical price data from Yahoo Finance"""
        # Determine period and interval based on time frame
        period = "5y"  # Default to 5 years
        
        if time_frame.get("period"):
            if "day" in time_frame["period"]:
                period = time_frame["period"].replace("last ", "")
            elif "week" in time_frame["period"]:
                period = time_frame["period"].replace("last ", "")
            elif "month" in time_frame["period"]:
                period = time_frame["period"].replace("last ", "")
            elif "year" in time_frame["period"]:
                period = time_frame["period"].replace("last ", "")
        
        cache_key = f"yf_prices_{ticker}_{period}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            
            # Cache the result
            self.cache[cache_key] = history
            
            return history
        except Exception as e:
            return pd.DataFrame({"error": [str(e)]})
    
    def get_twelve_data_technical(self, ticker: str) -> Dict:
        """Get technical indicators from Twelve Data"""
        cache_key = f"twelve_data_{ticker}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        base_url = "https://api.twelvedata.com"
        
        # Get multiple technical indicators
        indicators = {
            "sma": {"endpoint": "/sma", "params": {"symbol": ticker, "interval": "1day", "time_period": 20}},
            "ema": {"endpoint": "/ema", "params": {"symbol": ticker, "interval": "1day", "time_period": 20}},
            "rsi": {"endpoint": "/rsi", "params": {"symbol": ticker, "interval": "1day", "time_period": 14}},
            "macd": {"endpoint": "/macd", "params": {"symbol": ticker, "interval": "1day"}}
        }
        
        results = {}
        
        for indicator, config in indicators.items():
            endpoint = config["endpoint"]
            params = config["params"]
            params["apikey"] = self.api_keys["twelve_data"]
            
            url = base_url + endpoint
            response = requests.get(url, params=params)
            results[indicator] = response.json()
            
            # Avoid rate limiting
            time.sleep(0.5)
        
        # Cache the result
        self.cache[cache_key] = results
        
        return results
