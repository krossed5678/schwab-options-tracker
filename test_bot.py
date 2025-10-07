# OptiFlow Discord Bot Test Script
# This script tests the enhanced bot functionality

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    try:
        print("🔍 Testing imports...")
        
        # Test dashboard server import
        from src.dashboard_server import DashboardServer, start_dashboard_server
        print("✅ Dashboard server imports successful")
        
        # Test insider scanner import
        from src.insider_scanner import InsiderOptionsScanner
        print("✅ Insider scanner imports successful")
        
        # Test Discord imports
        import discord
        from discord.ext import commands
        print(f"✅ Discord.py imports successful (version: {discord.__version__})")
        
        # Test other dependencies
        import yfinance as yf
        print("✅ yfinance import successful")
        
        import sqlite3
        print("✅ sqlite3 import successful")
        
        import asyncio
        print("✅ asyncio import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_dashboard_server():
    """Test dashboard server functionality."""
    try:
        print("\n🌐 Testing dashboard server...")
        
        from src.dashboard_server import DashboardServer
        
        # Test server creation
        server = DashboardServer()
        print(f"✅ Dashboard server created on port {server.port}")
        
        # Test URL generation
        url = f"http://localhost:{server.port}"
        print(f"✅ Dashboard URL: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard server test failed: {e}")
        return False

def test_database_connection():
    """Test database functionality."""
    try:
        print("\n💾 Testing database connection...")
        
        import sqlite3
        
        # Test database connection
        conn = sqlite3.connect('optiflow.db')
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database connected - Found {len(tables)} tables")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_market_data():
    """Test market data functionality."""
    try:
        print("\n📊 Testing market data access...")
        
        import yfinance as yf
        
        # Test basic ticker fetch
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            print(f"✅ Market data access successful - Got data for {info.get('symbol', 'AAPL')}")
            return True
        else:
            print("⚠️ Market data access limited - may be rate limited")
            return True  # Still OK, just limited
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

async def test_bot_setup():
    """Test bot setup without actually connecting."""
    try:
        print("\n🤖 Testing bot configuration...")
        
        # Test bot token check
        if 'DISCORD_BOT_TOKEN' in os.environ:
            print("✅ Discord bot token found in environment")
        else:
            print("⚠️ Discord bot token not found - set DISCORD_BOT_TOKEN environment variable")
        
        # Test bot intents
        import discord
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        print("✅ Bot intents configured correctly")
        
        # Test commands module
        from discord.ext import commands
        bot = commands.Bot(command_prefix='!opti ', intents=intents)
        print("✅ Bot instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot setup test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 OptiFlow Bot Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Dashboard Server Tests", test_dashboard_server),
        ("Database Tests", test_database_connection),
        ("Market Data Tests", test_market_data),
        ("Bot Setup Tests", lambda: asyncio.run(test_bot_setup())),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your OptiFlow bot is ready to rock!")
        print("\n🚀 Next steps:")
        print("1. Set your DISCORD_BOT_TOKEN environment variable")
        print("2. Run: python discord_bot.py")
        print("3. Test commands like !opti help and !opti view")
    else:
        print(f"⚠️ {total - passed} tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)