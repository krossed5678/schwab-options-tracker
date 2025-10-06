#!/usr/bin/env python3
"""
Quick test for IPO tracking functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_ipo_functionality():
    """Test IPO tracking components."""
    print("🧪 Testing IPO Tracking Functionality\n")
    
    try:
        # Test IPO tracker import
        from src.ipo_tracker import IPOTracker
        print("✅ IPOTracker import successful")
        
        # Initialize tracker
        tracker = IPOTracker()
        print("✅ IPOTracker initialization successful")
        
        # Test upcoming IPOs
        upcoming = tracker.get_upcoming_ipos(30)
        print(f"✅ Upcoming IPOs: {len(upcoming)} found")
        
        # Test recent IPOs
        recent = tracker.get_recent_ipos(30)
        print(f"✅ Recent IPOs: {len(recent)} found")
        
        # Test IPO calendar
        calendar = tracker.get_ipo_calendar()
        print(f"✅ IPO Calendar: {len(calendar)} entries found")
        
        print(f"\n📊 Sample Upcoming IPO Data:")
        if not upcoming.empty:
            print(f"   • {upcoming.iloc[0]['company']} ({upcoming.iloc[0]['symbol']})")
            print(f"   • Expected: {upcoming.iloc[0]['expected_date']}")
            print(f"   • Sector: {upcoming.iloc[0]['sector']}")
            print(f"   • Price Range: {upcoming.iloc[0]['price_range']}")
        
        print(f"\n📈 Sample Recent IPO Data:")
        if not recent.empty:
            print(f"   • {recent.iloc[0]['company']} ({recent.iloc[0]['symbol']})")
            print(f"   • IPO Date: {recent.iloc[0]['ipo_date']}")
            print(f"   • Current Return: {recent.iloc[0]['current_return']:.1f}%")
            print(f"   • First Day Return: {recent.iloc[0]['first_day_return']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ IPO functionality test failed: {e}")
        return False

def test_complete_app():
    """Test complete application functionality."""
    print(f"\n🚀 Testing Complete Application\n")
    
    try:
        # Test main imports
        import streamlit as st
        import pandas as pd
        import plotly.graph_objects as go
        import yfinance as yf
        
        print("✅ All main imports successful")
        
        # Test custom modules
        from src.auth import SchwabAuth
        from src.schwab_client import SchwabClient
        from src.ipo_tracker import IPOTracker
        from src.utils import format_currency, format_percentage
        
        print("✅ All custom module imports successful")
        
        # Test utility functions
        assert format_currency(123.45) == "$123.45"
        assert format_percentage(0.1234) == "12.34%"
        print("✅ Utility functions working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete app test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Schwab Options & IPO Tracker\n")
    
    ipo_success = test_ipo_functionality()
    app_success = test_complete_app()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    print(f"IPO Functionality:     {'✅ PASS' if ipo_success else '❌ FAIL'}")
    print(f"Complete Application:  {'✅ PASS' if app_success else '❌ FAIL'}")
    
    if ipo_success and app_success:
        print(f"\n🎉 All tests passed!")
        print(f"\n🚀 Ready to run the application:")
        print(f"   streamlit run main.py")
        print(f"\n🌐 Access the app at: http://localhost:8501")
        print(f"\n📊 Features Available:")
        print(f"   • Options Analysis for ANY stock (AAPL, TSLA, etc.)")
        print(f"   • IPO Tracking with upcoming and recent IPO data")
        print(f"   • Interactive charts and data export")
        print(f"   • Unusual activity detection")
        print(f"   • Complete Greeks calculations")
    else:
        print(f"\n⚠️ Some tests failed. Please fix issues before running.")
    
    print("\n" + "="*50)