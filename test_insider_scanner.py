#!/usr/bin/env python3
"""
Test script for the insider options scanner
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.insider_scanner import InsiderOptionsScanner, get_insider_options_alerts

def test_insider_scanner():
    """Test the insider options scanner functionality."""
    print("🔍 Testing Insider Options Scanner...")
    print("=" * 50)
    
    try:
        # Initialize scanner
        scanner = InsiderOptionsScanner()
        print(f"✅ Scanner initialized successfully")
        print(f"📊 Monitoring {len(scanner.scan_symbols)} symbols")
        print(f"🔍 Symbols include: {scanner.scan_symbols[:10]}...")
        
        # Test getting alerts
        print("\n🚨 Getting insider options alerts...")
        alerts = get_insider_options_alerts()
        
        if alerts:
            print(f"✅ Found {len(alerts)} suspicious trades")
            print("\n🔥 Top 3 suspicious activities:")
            
            for i, alert in enumerate(alerts[:3]):
                print(f"\n{i+1}. {alert['symbol']} - Score: {alert['unusual_score']}/10")
                print(f"   � Alert Keys: {list(alert.keys())}")
                print(f"   �💰 Trade Value: ${alert.get('notional_value', alert.get('trade_value', 'N/A'))}")
                print(f"   📊 Strike: ${alert.get('strike', 'N/A')}")
                print(f"   📅 DTE: {alert.get('dte', 'N/A')} days")
                print(f"   🔍 Type: {alert.get('option_type', alert.get('type', 'N/A')).upper()}")
                print(f"   📈 Volume: {alert.get('volume', 'N/A')}")
                print(f"   💡 Reason: {alert.get('reasoning', alert.get('reason', 'N/A'))[:100]}...")
        else:
            print("📊 No suspicious activity detected at this time")
        
        print("\n✅ Insider scanner test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing insider scanner: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_insider_scanner()