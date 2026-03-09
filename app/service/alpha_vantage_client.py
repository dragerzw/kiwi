from dataclasses import dataclass
from typing import Optional
import os
import requests
from flask import current_app

from app.cache import cache

@dataclass
class SecurityQuote:
    ticker: str
    date: str
    price: float
    issuer: str

class AlphaVantageError(Exception):
    pass

@cache.memoize(timeout=300)
def get_company_name(ticker: str) -> Optional[str]:
    api_key = current_app.config.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise AlphaVantageError("ALPHA_VANTAGE_API_KEY is not configured")
    
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={ticker}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise AlphaVantageError(f"Failed to fetch company name for {ticker}: {e}")
    
    matches = data.get("bestMatches", [])
    if not matches:
        return None
        
    for match in matches:
        if match.get("1. symbol") == ticker:
            return match.get("2. name")
    
    return matches[0].get("2. name") if matches else None

@cache.memoize(timeout=300)
def get_price_data(ticker: str) -> Optional[dict]:
    api_key = current_app.config.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise AlphaVantageError("ALPHA_VANTAGE_API_KEY is not configured")
        
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise AlphaVantageError(f"Failed to fetch price data for {ticker}: {e}")
    
    quote = data.get("Global Quote", {})
    if not quote or "05. price" not in quote:
        return None
        
    return {
        "price": float(quote["05. price"]),
        "date": quote.get("07. latest trading day", "")
    }

def get_quote(ticker: str) -> Optional[SecurityQuote]:
    """
    Combines company search and global quote info to construct a full SecurityQuote
    """
    price_data = get_price_data(ticker)
    if not price_data:
        return None
        
    company_name = get_company_name(ticker)
    if not company_name:
        company_name = "Unknown Issuer"
        
    return SecurityQuote(
        ticker=ticker,
        date=price_data["date"],
        price=price_data["price"],
        issuer=company_name
    )
