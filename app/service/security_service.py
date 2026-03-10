from typing import List, Optional

from app.service.alpha_vantage_client import get_quote, SecurityQuote

class SecurityException(Exception):
    pass

class SecurityNotFoundException(SecurityException):
    pass

class SecurityFetchException(SecurityException):
    pass

def get_all_securities() -> List[SecurityQuote]:
    # Cannot fetch all securities from a search API, so we return an empty list 
    # or raise an exception if needed. The assignment states "fetch real-time prices instead of the local database Security table".
    return []

def get_security_by_ticker(ticker: str) -> Optional[SecurityQuote]:
    try:
        quote = get_quote(ticker)
    except Exception as e:
        raise SecurityFetchException(f"Failed to fetch security data for {ticker}: {str(e)}")
        
    if not quote:
        raise SecurityNotFoundException(f"Security with ticker {ticker} could not be found.")
    return quote
