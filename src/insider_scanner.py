#!/usr/bin/env python3
"""
OptiFlow Insider Options Scanner
Detects high-value, long-DTE options trades across all stocks for potential insider activity.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
import json
import os

logger = logging.getLogger(__name__)

# Import Schwab client
try:
    from .schwab_client import SchwabClient
    from .auth import SchwabAuth
    SCHWAB_AVAILABLE = True
except ImportError:
    SCHWAB_AVAILABLE = False
    logger.warning("Schwab API not available for insider scanner")

class InsiderOptionsScanner:
    """Scans for potential insider options activity across all stocks."""
    
    def __init__(self):
        self.scan_symbols = self._get_scannable_symbols()
        self.min_trade_value = 100000  # $100K minimum trade value
        self.min_dte = 30  # Minimum 30 days to expiration
        self.volume_threshold = 100  # Minimum 100 contracts
        self.detected_trades = []
        
        # Initialize Schwab client
        self.schwab_client = None
        if SCHWAB_AVAILABLE:
            try:
                import os
                app_key = os.getenv('SCHWAB_APP_KEY')
                app_secret = os.getenv('SCHWAB_APP_SECRET')
                
                if app_key and app_secret:
                    auth = SchwabAuth(app_key, app_secret)
                    self.schwab_client = SchwabClient(auth)
                    logger.info("✅ Insider scanner using Schwab API")
                else:
                    logger.warning("Schwab credentials not found for insider scanner")
            except Exception as e:
                logger.error(f"Failed to initialize Schwab client for scanner: {e}")
                self.schwab_client = None
        
    def _get_scannable_symbols(self) -> List[str]:
        """Get list of symbols to scan for insider activity."""
        # Focus on liquid, optionable stocks most likely to have insider activity
        symbols = [
            # Mega Cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'CRM',
            # Large Cap Tech
            'AMD', 'INTC', 'ORCL', 'ADBE', 'NOW', 'SNOW', 'PLTR', 'UBER', 'LYFT', 'SHOP',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP', 'BRK.B',
            # Healthcare & Biotech (high insider activity)
            'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'DHR', 'BMY', 'GILD', 'REGN',
            'BIIB', 'VRTX', 'ILMN', 'MRNA', 'BNTX', 'NVAX',
            # Consumer & Retail
            'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'COST', 'PG', 'KO',
            # Energy (M&A activity)
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO', 'OXY', 'HAL', 'BKR',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'LMT', 'RTX', 'DE', 'EMR',
            # ETFs (for market-wide bets)
            'SPY', 'QQQ', 'IWM', 'VIX', 'GLD', 'SLV'
        ]
        return symbols
    
    def scan_for_insider_activity(self) -> List[Dict[str, Any]]:
        """Scan all symbols for potential insider options activity."""
        insider_alerts = []
        
        for symbol in self.scan_symbols:
            try:
                alerts = self._analyze_symbol_options(symbol)
                insider_alerts.extend(alerts)
            except Exception as e:
                logger.debug(f"Error scanning {symbol}: {str(e)}")
                continue
        
        # Sort by trade value (highest first)
        insider_alerts.sort(key=lambda x: x['estimated_value'], reverse=True)
        return insider_alerts[:20]  # Top 20 most valuable trades
    
    def _analyze_symbol_options(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze options for a specific symbol using Schwab API."""
        alerts = []
        
        if not self.schwab_client:
            return alerts
        
        try:
            # Get current stock price
            quote_data = self.schwab_client.get_quote(symbol)
            if not quote_data:
                return alerts
                
            stock_price = quote_data.get('lastPrice', 0)
            if stock_price <= 0:
                return alerts
            
            # Get options chain (30-90 days out for insider activity)
            options_data = self.schwab_client.get_option_chain(symbol, days_to_expiration=90)
            if not options_data:
                return alerts
            
            # Process both calls and puts
            for option_type in ['callExpDateMap', 'putExpDateMap']:
                if option_type not in options_data:
                    continue
                    
                exp_date_map = options_data[option_type]
                
                for exp_date_str, strikes in exp_date_map.items():
                    try:
                        # Parse expiration date and calculate DTE
                        exp_date = datetime.strptime(exp_date_str.split(':')[0], '%Y-%m-%d')
                        dte = (exp_date - datetime.now()).days
                        
                        if dte < self.min_dte:
                            continue  # Skip short-term options
                        
                        # Analyze each strike price
                        for strike_price, options_list in strikes.items():
                            for option_data in options_list:
                                option_type_name = 'CALL' if option_type == 'callExpDateMap' else 'PUT'
                                
                                # Check for unusual activity
                                alert = self._check_option_for_insider_activity(
                                    option_data, symbol, exp_date_str, dte, stock_price, option_type_name, float(strike_price)
                                )
                                
                                if alert:
                                    alerts.append(alert)
                    
                    except Exception as e:
                        logger.debug(f"Error analyzing {symbol} {exp_date_str}: {str(e)}")
                        continue
        
        except Exception as e:
            logger.debug(f"Error getting options for {symbol}: {str(e)}")
        
        return alerts
    
    def _check_option_for_insider_activity(self, option_data: Dict, symbol: str, 
                                          exp_date: str, dte: int, stock_price: float, 
                                          option_type: str, strike: float) -> Optional[Dict[str, Any]]:
        """Check individual option for potential insider activity."""
        try:
            volume = option_data.get('totalVolume', 0)
            open_interest = option_data.get('openInterest', 0)
            last_price = option_data.get('last', 0)
            bid = option_data.get('bid', 0)
            ask = option_data.get('ask', 0)
            
            # Skip if no meaningful volume or price
            if volume < self.volume_threshold or last_price <= 0:
                return None
            
            # Calculate trade characteristics
            estimated_value = volume * last_price * 100  # Options are per 100 shares
            
            # Skip if trade value too small
            if estimated_value < self.min_trade_value:
                return None
            
            # Calculate moneyness
            if option_type == 'CALL':
                moneyness = strike / stock_price
                itm_otm = "ITM" if strike < stock_price else "OTM"
            else:  # PUT
                moneyness = stock_price / strike  
                itm_otm = "ITM" if strike > stock_price else "OTM"
                
            # Detect unusual characteristics (potential insider signals)
            unusual_score = self._calculate_unusual_score(
                volume, open_interest, estimated_value, dte, moneyness, itm_otm
            )
            
            if unusual_score >= 7:  # High threshold for insider alerts
                alert = {
                    'symbol': symbol,
                    'option_type': option_type,
                    'strike': strike,
                    'expiration': exp_date,
                    'dte': dte,
                    'volume': volume,
                    'open_interest': open_interest,
                    'last_price': last_price,
                    'estimated_value': estimated_value,
                    'stock_price': stock_price,
                    'moneyness': moneyness,
                    'itm_otm': itm_otm,
                    'unusual_score': unusual_score,
                    'detected_at': datetime.now().isoformat(),
                    'alert_reasons': self._get_alert_reasons(unusual_score, volume, open_interest, estimated_value, dte)
                }
                return alert
                
        except Exception as e:
            logger.debug(f"Error analyzing option: {str(e)}")
            
        return None
    
    def _calculate_unusual_score(self, volume: int, open_interest: int, 
                               estimated_value: float, dte: int, 
                               moneyness: float, itm_otm: str) -> int:
        """Calculate how unusual/suspicious this trade is (1-10 scale)."""
        score = 0
        
        # High volume score
        if volume >= 1000:
            score += 3
        elif volume >= 500:
            score += 2
        elif volume >= 250:
            score += 1
        
        # High dollar value score
        if estimated_value >= 1000000:  # $1M+
            score += 3
        elif estimated_value >= 500000:  # $500K+
            score += 2
        elif estimated_value >= 250000:  # $250K+
            score += 1
        
        # Volume vs Open Interest ratio (new positions)
        if open_interest > 0:
            vol_oi_ratio = volume / open_interest
            if vol_oi_ratio >= 0.5:  # 50%+ of OI traded today
                score += 2
            elif vol_oi_ratio >= 0.25:  # 25%+ of OI traded
                score += 1
        
        # Long DTE premium (more time = higher conviction)
        if dte >= 90:  # 3+ months
            score += 2
        elif dte >= 60:  # 2+ months
            score += 1
        
        # Moneyness analysis (slightly OTM = speculation/insider info)
        if itm_otm == "OTM":
            if 0.95 <= moneyness <= 1.1:  # Slightly OTM
                score += 2
            elif 0.9 <= moneyness <= 1.2:  # Moderately OTM
                score += 1
        
        return min(score, 10)  # Cap at 10
    
    def _get_alert_reasons(self, score: int, volume: int, open_interest: int, 
                          value: float, dte: int) -> List[str]:
        """Get human-readable reasons for the alert."""
        reasons = []
        
        if volume >= 1000:
            reasons.append(f"🔥 Extremely high volume: {volume:,} contracts")
        elif volume >= 500:
            reasons.append(f"📊 High volume: {volume:,} contracts")
        
        if value >= 1000000:
            reasons.append(f"💰 Massive trade value: ${value:,.0f}")
        elif value >= 500000:
            reasons.append(f"💸 Large trade value: ${value:,.0f}")
        
        if dte >= 90:
            reasons.append(f"⏰ Long-term position: {dte} days to expiry")
        elif dte >= 60:
            reasons.append(f"📅 Medium-term position: {dte} days to expiry")
        
        if open_interest > 0 and volume / open_interest >= 0.5:
            reasons.append(f"🆕 New positions: {(volume/open_interest)*100:.0f}% of open interest")
        
        return reasons

# Integration with Discord bot
def get_insider_options_alerts() -> List[Dict[str, Any]]:
    """Get current insider options alerts for Discord bot."""
    scanner = InsiderOptionsScanner()
    return scanner.scan_for_insider_activity()

if __name__ == "__main__":
    # Test the scanner
    scanner = InsiderOptionsScanner()
    alerts = scanner.scan_for_insider_activity()
    
    print(f"Found {len(alerts)} potential insider trades:")
    for alert in alerts[:5]:
        print(f"\n{alert['symbol']} {alert['option_type']} ${alert['strike']} {alert['expiration']}")
        print(f"Value: ${alert['estimated_value']:,.0f} | Volume: {alert['volume']:,} | Score: {alert['unusual_score']}")
        for reason in alert['alert_reasons']:
            print(f"  - {reason}")