import math
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple, Union
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

def calculate_days_to_expiration(expiration_date: Union[str, datetime, date]) -> int:
    """
    Calculate days to expiration from current date.
    
    Args:
        expiration_date: Expiration date (string, datetime, or date object)
        
    Returns:
        Number of days to expiration
    """
    if isinstance(expiration_date, str):
        # Handle different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
            try:
                exp_dt = datetime.strptime(expiration_date.split('T')[0] if 'T' in expiration_date else expiration_date, 
                                        fmt.split('T')[0])
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse date: {expiration_date}")
    elif isinstance(expiration_date, datetime):
        exp_dt = expiration_date
    elif isinstance(expiration_date, date):
        exp_dt = datetime.combine(expiration_date, datetime.min.time())
    else:
        raise ValueError(f"Invalid date type: {type(expiration_date)}")
    
    today = datetime.now().date()
    return (exp_dt.date() - today).days

def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate Black-Scholes call option price.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility (annualized)
        
    Returns:
        Call option theoretical price
    """
    if T <= 0:
        return max(0, S - K)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return max(0, call_price)

def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate Black-Scholes put option price.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility (annualized)
        
    Returns:
        Put option theoretical price
    """
    if T <= 0:
        return max(0, K - S)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return max(0, put_price)

def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, 
                    option_type: str = "call") -> Dict[str, float]:
    """
    Calculate option Greeks using Black-Scholes model.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility (annualized)
        option_type: "call" or "put"
        
    Returns:
        Dictionary containing Delta, Gamma, Theta, Vega, and Rho
    """
    if T <= 0:
        # For expired options
        if option_type.lower() == "call":
            delta = 1.0 if S > K else 0.0
        else:
            delta = -1.0 if S < K else 0.0
        
        return {
            'delta': delta,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Common terms
    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)
    pdf_d1 = norm.pdf(d1)
    
    if option_type.lower() == "call":
        delta = nd1
        theta = (-S * pdf_d1 * sigma / (2 * np.sqrt(T)) - 
                r * K * np.exp(-r * T) * nd2) / 365  # Per day
        rho = K * T * np.exp(-r * T) * nd2 / 100  # Per 1% change
    else:  # put
        delta = nd1 - 1
        theta = (-S * pdf_d1 * sigma / (2 * np.sqrt(T)) + 
                r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365  # Per day
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100  # Per 1% change
    
    # Gamma and Vega are the same for calls and puts
    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * pdf_d1 * np.sqrt(T) / 100  # Per 1% change in volatility
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

def implied_volatility(market_price: float, S: float, K: float, T: float, 
                      r: float, option_type: str = "call", 
                      max_iterations: int = 100, tolerance: float = 1e-5) -> Optional[float]:
    """
    Calculate implied volatility using Newton-Raphson method.
    
    Args:
        market_price: Current market price of the option
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        option_type: "call" or "put"
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance
        
    Returns:
        Implied volatility or None if convergence fails
    """
    if T <= 0 or market_price <= 0:
        return None
    
    # Initial guess
    sigma = 0.2
    
    for i in range(max_iterations):
        if option_type.lower() == "call":
            price = black_scholes_call(S, K, T, r, sigma)
        else:
            price = black_scholes_put(S, K, T, r, sigma)
        
        # Vega (sensitivity to volatility)
        if T > 0:
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)
        else:
            return None
        
        if abs(vega) < 1e-10:  # Avoid division by zero
            return None
        
        # Newton-Raphson update
        sigma_new = sigma - (price - market_price) / vega
        
        if abs(sigma_new - sigma) < tolerance:
            return max(0.001, sigma_new)  # Return positive volatility
        
        sigma = max(0.001, sigma_new)  # Ensure positive volatility
    
    return None  # Failed to converge

def format_option_data(option_chain_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert Schwab option chain data to a clean pandas DataFrame.
    
    Args:
        option_chain_data: Raw option chain data from Schwab API
        
    Returns:
        Formatted DataFrame with option data
    """
    if not option_chain_data or 'callExpDateMap' not in option_chain_data and 'putExpDateMap' not in option_chain_data:
        return pd.DataFrame()
    
    options_list = []
    underlying = option_chain_data.get('underlying', {})
    underlying_price = underlying.get('last', 0)
    
    # Process calls
    call_map = option_chain_data.get('callExpDateMap', {})
    for exp_date, strikes in call_map.items():
        for strike_str, option_list in strikes.items():
            for option in option_list:
                option_data = _extract_option_data(option, 'CALL', exp_date, underlying_price)
                if option_data:
                    options_list.append(option_data)
    
    # Process puts
    put_map = option_chain_data.get('putExpDateMap', {})
    for exp_date, strikes in put_map.items():
        for strike_str, option_list in strikes.items():
            for option in option_list:
                option_data = _extract_option_data(option, 'PUT', exp_date, underlying_price)
                if option_data:
                    options_list.append(option_data)
    
    if not options_list:
        return pd.DataFrame()
    
    df = pd.DataFrame(options_list)
    
    # Calculate additional metrics
    df = _calculate_additional_metrics(df, underlying_price)
    
    return df

def _extract_option_data(option: Dict[str, Any], option_type: str, 
                        exp_date: str, underlying_price: float) -> Optional[Dict[str, Any]]:
    """Extract and format individual option data."""
    try:
        # Parse expiration date
        exp_date_clean = exp_date.split(':')[0]  # Remove DTE part
        days_to_exp = calculate_days_to_expiration(exp_date_clean)
        
        # Extract basic option information
        strike = option.get('strikePrice', 0)
        bid = option.get('bid', 0)
        ask = option.get('ask', 0)
        last = option.get('last', 0)
        mark = option.get('mark', 0)
        
        # Calculate mid price
        mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else mark if mark > 0 else last
        
        option_data = {
            'symbol': option.get('symbol', ''),
            'description': option.get('description', ''),
            'option_type': option_type,
            'strike': strike,
            'expiration_date': exp_date_clean,
            'days_to_expiration': days_to_exp,
            'bid': bid,
            'ask': ask,
            'last': last,
            'mark': mark,
            'mid_price': mid_price,
            'volume': option.get('totalVolume', 0),
            'open_interest': option.get('openInterest', 0),
            'implied_volatility': option.get('volatility', 0),
            'delta': option.get('delta', 0),
            'gamma': option.get('gamma', 0),
            'theta': option.get('theta', 0),
            'vega': option.get('vega', 0),
            'rho': option.get('rho', 0),
            'time_value': option.get('timeValue', 0),
            'intrinsic_value': option.get('intrinsicValue', 0),
            'in_the_money': option.get('inTheMoney', False),
            'underlying_price': underlying_price
        }
        
        return option_data
        
    except Exception as e:
        logger.warning(f"Failed to extract option data: {str(e)}")
        return None

def _calculate_additional_metrics(df: pd.DataFrame, underlying_price: float) -> pd.DataFrame:
    """Calculate additional metrics for options data."""
    if df.empty:
        return df
    
    # Moneyness
    df['moneyness'] = df.apply(
        lambda row: (underlying_price / row['strike'] if row['option_type'] == 'CALL' 
                    else row['strike'] / underlying_price), axis=1
    )
    
    # Bid-Ask spread
    df['bid_ask_spread'] = df['ask'] - df['bid']
    df['bid_ask_spread_pct'] = np.where(
        df['mid_price'] > 0,
        (df['bid_ask_spread'] / df['mid_price']) * 100,
        0
    )
    
    # Volume to Open Interest ratio (unusual activity indicator)
    df['vol_oi_ratio'] = np.where(
        df['open_interest'] > 0,
        df['volume'] / df['open_interest'],
        0
    )
    
    # ITM/OTM classification
    df['itm_otm'] = df.apply(
        lambda row: 'ITM' if (
            (row['option_type'] == 'CALL' and underlying_price > row['strike']) or
            (row['option_type'] == 'PUT' and underlying_price < row['strike'])
        ) else 'OTM', axis=1
    )
    
    # Distance from underlying
    df['distance_from_underlying'] = abs(df['strike'] - underlying_price)
    df['distance_pct'] = (df['distance_from_underlying'] / underlying_price) * 100
    
    return df

def detect_unusual_activity(df: pd.DataFrame, volume_threshold: int = 100, 
                          oi_threshold: int = 50, ratio_threshold: float = 2.0) -> pd.DataFrame:
    """
    Detect options with unusual trading activity.
    
    Args:
        df: Options DataFrame
        volume_threshold: Minimum volume threshold
        oi_threshold: Minimum open interest threshold
        ratio_threshold: Minimum volume/OI ratio threshold
        
    Returns:
        Filtered DataFrame with unusual activity
    """
    if df.empty:
        return df
    
    unusual = df[
        (df['volume'] >= volume_threshold) &
        (df['open_interest'] >= oi_threshold) &
        (df['vol_oi_ratio'] >= ratio_threshold)
    ].copy()
    
    # Sort by volume/OI ratio descending
    unusual = unusual.sort_values('vol_oi_ratio', ascending=False)
    
    return unusual

def calculate_option_metrics_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics for option chain data.
    
    Args:
        df: Options DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {}
    
    calls = df[df['option_type'] == 'CALL']
    puts = df[df['option_type'] == 'PUT']
    
    summary = {
        'total_contracts': len(df),
        'total_calls': len(calls),
        'total_puts': len(puts),
        'total_volume': df['volume'].sum(),
        'call_volume': calls['volume'].sum() if not calls.empty else 0,
        'put_volume': puts['volume'].sum() if not puts.empty else 0,
        'total_open_interest': df['open_interest'].sum(),
        'call_open_interest': calls['open_interest'].sum() if not calls.empty else 0,
        'put_open_interest': puts['open_interest'].sum() if not puts.empty else 0,
        'avg_implied_vol': df['implied_volatility'].mean() if not df.empty else 0,
        'max_volume_contract': df.loc[df['volume'].idxmax()].to_dict() if not df.empty else {},
        'unusual_activity_count': len(detect_unusual_activity(df))
    }
    
    # Put/Call ratio
    if summary['call_volume'] > 0:
        summary['put_call_volume_ratio'] = summary['put_volume'] / summary['call_volume']
    else:
        summary['put_call_volume_ratio'] = float('inf') if summary['put_volume'] > 0 else 0
    
    if summary['call_open_interest'] > 0:
        summary['put_call_oi_ratio'] = summary['put_open_interest'] / summary['call_open_interest']
    else:
        summary['put_call_oi_ratio'] = float('inf') if summary['put_open_interest'] > 0 else 0
    
    return summary

def format_currency(value: float) -> str:
    """Format a number as currency."""
    return f"${value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as percentage."""
    return f"{value:.{decimals}f}%"

def format_large_number(value: int) -> str:
    """Format large numbers with K, M, B suffixes."""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(value)