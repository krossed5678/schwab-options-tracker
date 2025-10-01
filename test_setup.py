#!/usr/bin/env python3
"""
Quick test script for Schwab Options Tracker
Tests API authentication and basic functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all required packages can be imported."""
    try:
        import streamlit
        import pandas
        import numpy
        import plotly
        import requests
        import scipy
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_environment():
    """Test environment configuration."""
    load_dotenv()
    
    required_vars = ['SCHWAB_APP_KEY', 'SCHWAB_APP_SECRET']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    else:
        print("✅ Environment variables configured")
        return True

def test_auth():
    """Test Schwab authentication setup."""
    try:
        from src.auth import SchwabAuth
        
        app_key = os.getenv('SCHWAB_APP_KEY')
        app_secret = os.getenv('SCHWAB_APP_SECRET')
        redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1')
        
        auth = SchwabAuth(app_key, app_secret, redirect_uri)
        
        if auth.is_authenticated():
            print("✅ Already authenticated with valid tokens")
        else:
            print("⚠️ Not authenticated - will need to complete OAuth flow")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_client():
    """Test API client initialization."""
    try:
        from src.auth import SchwabAuth
        from src.schwab_client import SchwabClient
        
        app_key = os.getenv('SCHWAB_APP_KEY')
        app_secret = os.getenv('SCHWAB_APP_SECRET')
        redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1')
        
        auth = SchwabAuth(app_key, app_secret, redirect_uri)
        client = SchwabClient(auth)
        
        print("✅ API client initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False

def test_utilities():
    """Test utility functions."""
    try:
        from src.utils import calculate_greeks, format_currency, format_percentage
        
        # Test Greeks calculation
        greeks = calculate_greeks(100, 105, 0.25, 0.05, 0.2, "call")
        assert isinstance(greeks, dict)
        assert 'delta' in greeks
        
        # Test formatting functions
        assert format_currency(123.456) == "$123.46"
        assert format_percentage(0.1234) == "12.34%"
        
        print("✅ Utility functions working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Utilities test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Schwab Options Tracker Setup\n")
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Config", test_environment),
        ("Authentication Setup", test_auth),
        ("API Client", test_client),
        ("Utility Functions", test_utilities)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to run the application.")
        print("Run: streamlit run main.py")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix issues before running.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)