#!/usr/bin/env python3
"""
OptiFlow Insider Options Scanner
Detects high-value, long-DTE options trades across all stocks for potential insider activity.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
import json
import os

logger = logging.getLogger(__name__)

class InsiderOptionsScanner:
    """Scans for potential insider options activity across all stocks."""
    
    def __init__(self):
        self.scan_symbols = self._get_scannable_symbols()
        self.min_trade_value = 100000  # $100K minimum trade value
        self.min_dte = 30  # Minimum 30 days to expiration
        self.volume_threshold = 100  # Minimum 100 contracts
        self.detected_trades = []
        
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
        """Analyze options for a specific symbol."""
        alerts = []
        
        try:
            ticker = yf.Ticker(symbol)
            stock_price = ticker.history(period="1d")['Close'][-1]
            
            # Get all available option expirations
            expirations = ticker.options
            if not expirations:
                return alerts
            
            # Check each expiration for long-DTE trades
            for exp_date in expirations:
                try:
                    # Calculate DTE
                    exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
                    dte = (exp_datetime - datetime.now()).days
                    
                    if dte < self.min_dte:
                        continue  # Skip short-term options
                    
                    # Get options chain
                    options_chain = ticker.option_chain(exp_date)
                    
                    # Analyze calls
                    call_alerts = self._analyze_options_data(
                        options_chain.calls, symbol, exp_date, dte, stock_price, 'CALL'
                    )
                    alerts.extend(call_alerts)
                    
                    # Analyze puts  
                    put_alerts = self._analyze_options_data(
                        options_chain.puts, symbol, exp_date, dte, stock_price, 'PUT'
                    )
                    alerts.extend(put_alerts)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing {symbol} {exp_date}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.debug(f"Error getting options for {symbol}: {str(e)}")
        
        return alerts
    
    def _analyze_options_data(self, options_df: pd.DataFrame, symbol: str, 
                            exp_date: str, dte: int, stock_price: float, 
                            option_type: str) -> List[Dict[str, Any]]:
        """Analyze individual options for insider activity."""
        alerts = []
        
        if options_df.empty:
            return alerts
        
        for _, option in options_df.iterrows():
            try:
                volume = option.get('volume', 0)
                open_interest = option.get('openInterest', 0)
                last_price = option.get('lastPrice', 0)
                strike = option.get('strike', 0)
                
                # Skip if no meaningful volume
                if volume < self.volume_threshold or last_price <= 0:
                    continue
                
                # Calculate trade characteristics
                estimated_value = volume * last_price * 100  # Options are per 100 shares
                
                # Skip if trade value too small
                if estimated_value < self.min_trade_value:
                    continue
                
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
                    alerts.append(alert)
            
            except Exception as e:
                logger.debug(f"Error analyzing option: {str(e)}")
                continue
        
        return alerts
    
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