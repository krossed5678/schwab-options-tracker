import logging
import time
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import requests
import pandas as pd
from .auth import SchwabAuth

logger = logging.getLogger(__name__)

class SchwabClient:
    """
    Client for interacting with Schwab Trader API to fetch options and market data.
    
    This class provides methods to:
    - Fetch option chains
    - Get real-time quotes
    - Retrieve market data
    - Handle rate limiting and retries
    """
    
    def __init__(self, auth: SchwabAuth):
        """
        Initialize the Schwab API client.
        
        Args:
            auth: Authenticated SchwabAuth instance
        """
        self.auth = auth
        self.base_url = "https://api.schwabapi.com"
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make an authenticated API request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: URL parameters
            data: Request body data
            
        Returns:
            Response object or None if all retries failed
        """
        # Ensure we have a valid token
        token = self.auth.get_valid_token()
        if not token:
            logger.error("No valid authentication token available")
            return None
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                self.last_request_time = time.time()
                
                # Handle different response codes
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    # Token might be expired, try to refresh
                    logger.warning("Received 401, attempting to refresh token")
                    if self.auth.refresh_access_token():
                        # Update token and retry
                        token = self.auth.get_valid_token()
                        headers['Authorization'] = f'Bearer {token}'
                        continue
                    else:
                        logger.error("Failed to refresh token")
                        return None
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying in {self.retry_delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return None
        
        return None
    
    def get_option_chain(self, symbol: str, contract_type: str = "ALL", 
                        strike_count: int = 10, include_quotes: bool = True,
                        strategy: str = "SINGLE", interval: Optional[str] = None,
                        strike: Optional[float] = None, range_type: str = "ALL",
                        from_date: Optional[str] = None, to_date: Optional[str] = None,
                        volatility: Optional[float] = None, underlying_price: Optional[float] = None,
                        interest_rate: Optional[float] = None, days_to_expiration: Optional[int] = None,
                        exp_month: str = "ALL", option_type: str = "ALL") -> Optional[Dict[str, Any]]:
        """
        Get option chain data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "SPY")
            contract_type: Type of contracts to return (CALL, PUT, ALL)
            strike_count: Number of strikes to return
            include_quotes: Whether to include quote data
            strategy: Options strategy (SINGLE, ANALYTICAL, COVERED, VERTICAL, etc.)
            interval: Strike interval for spread strategies
            strike: Specific strike price
            range_type: Range of strikes (ITM, NTM, OTM, SAK, SBK, SNK, ALL)
            from_date: Start date for expiration filtering (YYYY-MM-DD)
            to_date: End date for expiration filtering (YYYY-MM-DD)
            volatility: Volatility to use in calculations
            underlying_price: Underlying price to use in calculations
            interest_rate: Interest rate to use in calculations
            days_to_expiration: Days to expiration
            exp_month: Expiration month (ALL, JAN, FEB, etc.)
            option_type: Option type (S=Standard, NS=Non-Standard, ALL=All)
            
        Returns:
            Option chain data or None if request failed
        """
        params = {
            'symbol': symbol.upper(),
            'contractType': contract_type,
            'strikeCount': strike_count,
            'includeQuotes': str(include_quotes).lower(),
            'strategy': strategy,
            'range': range_type,
            'expMonth': exp_month,
            'optionType': option_type
        }
        
        # Add optional parameters
        if interval:
            params['interval'] = interval
        if strike:
            params['strike'] = strike
        if from_date:
            params['fromDate'] = from_date
        if to_date:
            params['toDate'] = to_date
        if volatility:
            params['volatility'] = volatility
        if underlying_price:
            params['underlyingPrice'] = underlying_price
        if interest_rate:
            params['interestRate'] = interest_rate
        if days_to_expiration:
            params['daysToExpiration'] = days_to_expiration
        
        response = self._make_request('GET', '/marketdata/v1/chains', params=params)
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse option chain response: {str(e)}")
                return None
        
        return None
    
    def get_quotes(self, symbols: Union[str, List[str]], fields: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get real-time quotes for one or more symbols.
        
        Args:
            symbols: Single symbol or list of symbols
            fields: Comma-separated list of fields to return
            
        Returns:
            Quote data or None if request failed
        """
        if isinstance(symbols, list):
            symbol_string = ','.join(symbols)
        else:
            symbol_string = symbols
        
        params = {
            'symbols': symbol_string.upper()
        }
        
        if fields:
            params['fields'] = fields
        
        response = self._make_request('GET', '/marketdata/v1/quotes', params=params)
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse quotes response: {str(e)}")
                return None
        
        return None
    
    def get_quote(self, symbol: str, fields: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a single symbol.
        
        Args:
            symbol: Stock symbol
            fields: Comma-separated list of fields to return
            
        Returns:
            Quote data or None if request failed
        """
        params = {}
        if fields:
            params['fields'] = fields
        
        response = self._make_request('GET', f'/marketdata/v1/{symbol.upper()}/quotes', params=params)
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse quote response: {str(e)}")
                return None
        
        return None
    
    def get_option_expiration_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get option expiration dates for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Expiration data or None if request failed
        """
        response = self._make_request('GET', f'/marketdata/v1/expirationchain', 
                                    params={'symbol': symbol.upper()})
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse expiration chain response: {str(e)}")
                return None
        
        return None
    
    def get_market_hours(self, markets: Union[str, List[str]], 
                        date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get market hours for specified markets.
        
        Args:
            markets: Single market or list of markets (equity, option, bond, etc.)
            date: Date in YYYY-MM-DD format (defaults to current date)
            
        Returns:
            Market hours data or None if request failed
        """
        if isinstance(markets, list):
            market_string = ','.join(markets)
        else:
            market_string = markets
        
        params = {
            'markets': market_string.upper()
        }
        
        if date:
            params['date'] = date
        
        response = self._make_request('GET', '/marketdata/v1/markets', params=params)
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse market hours response: {str(e)}")
                return None
        
        return None
    
    def search_instruments(self, symbol: str, projection: str = "symbol-search") -> Optional[Dict[str, Any]]:
        """
        Search for instruments/symbols.
        
        Args:
            symbol: Symbol or partial symbol to search for
            projection: Type of search (symbol-search, symbol-regex, desc-search, desc-regex, fundamental)
            
        Returns:
            Search results or None if request failed
        """
        params = {
            'symbol': symbol.upper(),
            'projection': projection
        }
        
        response = self._make_request('GET', '/marketdata/v1/instruments', params=params)
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse instrument search response: {str(e)}")
                return None
        
        return None
    
    def get_instrument(self, cusip: str) -> Optional[Dict[str, Any]]:
        """
        Get instrument details by CUSIP.
        
        Args:
            cusip: CUSIP identifier
            
        Returns:
            Instrument data or None if request failed
        """
        response = self._make_request('GET', f'/marketdata/v1/instruments/{cusip}')
        
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse instrument response: {str(e)}")
                return None
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get a simple quote
            result = self.get_quote("SPY")
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False