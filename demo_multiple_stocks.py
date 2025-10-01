#!/usr/bin/env python3
"""
Multi-Stock Options Analysis Demo
Demonstrates analyzing options for multiple stocks programmatically
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_multiple_stocks():
    """Demo: Analyze options for multiple popular stocks."""
    load_dotenv()
    
    from src.auth import SchwabAuth
    from src.schwab_client import SchwabClient
    from src.utils import format_option_data, calculate_option_metrics_summary
    
    # Initialize client
    app_key = os.getenv('SCHWAB_APP_KEY')
    app_secret = os.getenv('SCHWAB_APP_SECRET')
    redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1')
    
    if not app_key or not app_secret:
        print("❌ Please configure SCHWAB_APP_KEY and SCHWAB_APP_SECRET in .env")
        return
    
    auth = SchwabAuth(app_key, app_secret, redirect_uri)
    
    if not auth.authenticate():
        print("❌ Authentication failed")
        return
    
    client = SchwabClient(auth)
    
    # List of stocks to analyze
    stocks_to_analyze = [
        "AAPL",  # Apple
        "TSLA",  # Tesla
        "NVDA",  # NVIDIA
        "MSFT",  # Microsoft
        "META",  # Meta
        "SPY",   # S&P 500 ETF
        "QQQ"    # NASDAQ ETF
    ]
    
    print("🚀 Analyzing Options for Multiple Stocks")
    print("=" * 50)
    
    results = {}
    
    for symbol in stocks_to_analyze:
        print(f"\n📊 Analyzing {symbol}...")
        
        try:
            # Get option chain
            option_data = client.get_option_chain(
                symbol=symbol,
                contract_type="ALL",
                strike_count=10,
                include_quotes=True
            )
            
            if option_data:
                # Format and analyze data
                df = format_option_data(option_data)
                summary = calculate_option_metrics_summary(df)
                underlying = option_data.get('underlying', {})
                
                results[symbol] = {
                    'underlying_price': underlying.get('last', 0),
                    'company': underlying.get('description', symbol),
                    'total_volume': summary.get('total_volume', 0),
                    'total_oi': summary.get('total_open_interest', 0),
                    'avg_iv': summary.get('avg_implied_vol', 0),
                    'put_call_ratio': summary.get('put_call_volume_ratio', 0)
                }
                
                print(f"✅ {symbol}: ${underlying.get('last', 0):.2f}")
                print(f"   Volume: {summary.get('total_volume', 0):,}")
                print(f"   Avg IV: {summary.get('avg_implied_vol', 0)*100:.1f}%")
                
            else:
                print(f"❌ Failed to get data for {symbol}")
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {str(e)}")
    
    # Summary comparison
    print(f"\n📈 MULTI-STOCK COMPARISON")
    print("=" * 50)
    print(f"{'Symbol':<8} {'Price':<10} {'Volume':<12} {'Avg IV':<8} {'P/C Ratio':<10}")
    print("-" * 50)
    
    for symbol, data in results.items():
        price = f"${data['underlying_price']:.2f}"
        volume = f"{data['total_volume']:,}"
        iv = f"{data['avg_iv']*100:.1f}%"
        pcr = f"{data['put_call_ratio']:.2f}" if data['put_call_ratio'] != float('inf') else "∞"
        
        print(f"{symbol:<8} {price:<10} {volume:<12} {iv:<8} {pcr:<10}")
    
    print(f"\n🎉 Analysis complete! Analyzed {len(results)} stocks successfully.")
    print("\n💡 To analyze any other stock, simply:")
    print("   1. Run: streamlit run main.py")
    print("   2. Enter any ticker symbol (e.g., AMD, CRM, NFLX, etc.)")
    print("   3. Click 'Fetch Options Data'")

if __name__ == "__main__":
    analyze_multiple_stocks()