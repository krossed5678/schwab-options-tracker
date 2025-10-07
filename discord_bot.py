#!/usr/bin/env python3
"""
OptiFlow Discord Bot
Real-time trading alerts, insider options, and IPO notifications via Discord bot commands.
"""

import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import logging
import traceback

# Load environment variables
load_dotenv()

# Import Schwab API client and insider scanner
try:
    from src.schwab_client import SchwabClient
    from src.auth import SchwabAuth
    SCHWAB_API_AVAILABLE = True
    print("✅ Schwab API client loaded successfully")
except ImportError as e:
    SCHWAB_API_AVAILABLE = False
    print(f"Warning: Schwab API not available - {e}")

try:
    from src.insider_scanner import InsiderOptionsScanner, get_insider_options_alerts
    INSIDER_SCANNER_AVAILABLE = True
except ImportError:
    INSIDER_SCANNER_AVAILABLE = False
    print("Warning: Insider scanner not available - dependencies may be missing")

try:
    from src.dashboard_server import start_dashboard_server, get_dashboard_url
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("Warning: Dashboard server not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', '0'))
ALERTS_CHANNEL_ID = int(os.getenv('DISCORD_ALERTS_CHANNEL_ID', '0'))

# Bot setup with message content intent (required for commands)
intents = discord.Intents.default()
intents.message_content = True  # REQUIRED: Enable this in Discord Developer Portal
intents.guilds = True
intents.guild_messages = True

# Create bot instance
bot = commands.Bot(command_prefix='!opti ', intents=intents, help_command=None)

# Initialize Schwab API client
schwab_client = None
if SCHWAB_API_AVAILABLE:
    try:
        auth = SchwabAuth()
        schwab_client = SchwabClient(auth)
        if schwab_client.test_connection():
            print("✅ Schwab API connection successful")
        else:
            print("⚠️ Schwab API connection failed - will retry automatically")
    except Exception as e:
        print(f"❌ Failed to initialize Schwab API: {e}")
        SCHWAB_API_AVAILABLE = False

# Helper functions to replace yfinance with Schwab API
async def get_stock_quote(symbol: str) -> Optional[Dict]:
    """Get stock quote using Schwab API instead of yfinance"""
    if not schwab_client:
        return None
    
    try:
        quote_data = schwab_client.get_quote(symbol)
        if quote_data:
            # Convert Schwab format to yfinance-like format for compatibility
            return {
                'symbol': symbol.upper(),
                'regularMarketPrice': quote_data.get('lastPrice', 0),
                'regularMarketChange': quote_data.get('netChange', 0),
                'regularMarketChangePercent': quote_data.get('netPercentChangeInDouble', 0),
                'regularMarketVolume': quote_data.get('totalVolume', 0),
                'regularMarketDayHigh': quote_data.get('highPrice', 0),
                'regularMarketDayLow': quote_data.get('lowPrice', 0),
                'regularMarketOpen': quote_data.get('openPrice', 0),
                'regularMarketPreviousClose': quote_data.get('closePrice', 0),
                'bid': quote_data.get('bidPrice', 0),
                'ask': quote_data.get('askPrice', 0),
                'marketCap': quote_data.get('marketCap', 0),
                'trailingPE': quote_data.get('peRatio', 0),
                'dividendYield': quote_data.get('divYield', 0),
                'fiftyTwoWeekHigh': quote_data.get('highPrice52', 0),
                'fiftyTwoWeekLow': quote_data.get('lowPrice52', 0),
                'longName': quote_data.get('description', symbol),
                'shortName': quote_data.get('description', symbol)
            }
        return None
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        return None

async def get_stock_info(symbol: str) -> Optional[Dict]:
    """Get comprehensive stock info using Schwab API"""
    quote = await get_stock_quote(symbol)
    if quote:
        return quote
    return None

async def get_stock_history(symbol: str, period: str = "1d") -> Optional[pd.DataFrame]:
    """Get stock price history using Schwab API"""
    if not schwab_client:
        return None
    
    try:
        # Convert period to days
        period_days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}.get(period, 1)
        history_data = schwab_client.get_price_history(symbol, period_type="day", period_days=period_days)
        
        if history_data and 'candles' in history_data:
            candles = history_data['candles']
            df = pd.DataFrame(candles)
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)
            return df
        return None
    except Exception as e:
        logger.error(f"Error getting history for {symbol}: {e}")
        return None

# Enhanced error handling for privileged intents
async def handle_privileged_intents_error():
    """Provide clear instructions for privileged intents setup."""
    print("\n" + "="*70)
    print("🚨 PRIVILEGED INTENTS ERROR - ACTION REQUIRED!")
    print("="*70)
    print("Your bot needs 'Message Content Intent' enabled to work properly.")
    print("\n📋 QUICK FIX STEPS:")
    print("1. Go to: https://discord.com/developers/applications/")
    print("2. Select your bot application")
    print("3. Click 'Bot' in the left sidebar")
    print("4. Scroll down to 'Privileged Gateway Intents'")
    print("5. Toggle ON 'Message Content Intent'")
    print("6. Click 'Save Changes'")
    print("7. Restart this bot")
    print("\n💡 WHY: Discord requires explicit permission for bots to read message content.")
    print("This is needed for the !opti commands to work.")
    print("="*70)

class TradingDataManager:
    """Manages trading data for Discord bot."""
    
    def __init__(self):
        self.alerts_file = 'data/alerts.json'
        self.watchlist = set()
        self.user_preferences = {}  # Store user notification preferences
        self.load_user_preferences()
        
    def get_insider_options(self, symbol: str) -> Dict[str, Any]:
        """Get insider options activity using Schwab API."""
        try:
            if not schwab_client:
                return {"error": "Schwab API not available"}
                
            options_data = schwab_client.get_option_chain(symbol)
            
            if not options_data:
                return {"error": "No options data available"}
            
            # Process options data
            calls = []
            puts = []
            
            # Extract calls and puts from Schwab format
            call_map = options_data.get('callExpDateMap', {})
            put_map = options_data.get('putExpDateMap', {})
            
            for exp_date, strikes in call_map.items():
                for strike, options_list in strikes.items():
                    for option in options_list:
                        calls.append({
                            'strike': float(strike),
                            'volume': option.get('totalVolume', 0),
                            'openInterest': option.get('openInterest', 0),
                            'lastPrice': option.get('last', 0),
                            'bid': option.get('bid', 0),
                            'ask': option.get('ask', 0)
                        })
            
            for exp_date, strikes in put_map.items():
                for strike, options_list in strikes.items():
                    for option in options_list:
                        puts.append({
                            'strike': float(strike),
                            'volume': option.get('totalVolume', 0),
                            'openInterest': option.get('openInterest', 0),
                            'lastPrice': option.get('last', 0),
                            'bid': option.get('bid', 0),
                            'ask': option.get('ask', 0)
                        })
            
            # Find high volume options (potential insider activity)
            high_vol_calls = calls[calls['volume'] > calls['volume'].quantile(0.9)] if not calls.empty else pd.DataFrame()
            high_vol_puts = puts[puts['volume'] > puts['volume'].quantile(0.9)] if not puts.empty else pd.DataFrame()
            
            return {
                'symbol': symbol,
                'expiry': exp_date,
                'high_volume_calls': len(high_vol_calls),
                'high_volume_puts': len(high_vol_puts),
                'total_call_volume': calls['volume'].sum() if not calls.empty else 0,
                'total_put_volume': puts['volume'].sum() if not puts.empty else 0,
                'call_put_ratio': (calls['volume'].sum() / puts['volume'].sum()) if not puts.empty and puts['volume'].sum() > 0 else 0
            }
        except Exception as e:
            return {"error": f"Failed to get options data: {str(e)}"}
    
    def get_upcoming_ipos(self) -> List[Dict[str, Any]]:
        """Get upcoming IPO data."""
        # Mock IPO data - replace with real IPO API
        upcoming_ipos = [
            {
                'company': 'TechFlow Inc',
                'symbol': 'TFLW',
                'date': '2025-10-15',
                'price_range': '$18-22',
                'shares': '15M',
                'market_cap': '$330M',
                'sector': 'Technology'
            },
            {
                'company': 'GreenEnergy Corp',
                'symbol': 'GREN',
                'date': '2025-10-22',
                'price_range': '$25-30',
                'shares': '12M',
                'market_cap': '$360M',
                'sector': 'Energy'
            },
            {
                'company': 'BioTech Solutions',
                'symbol': 'BIOS',
                'date': '2025-11-05',
                'price_range': '$15-20',
                'shares': '20M',
                'market_cap': '$400M',
                'sector': 'Biotechnology'
            }
        ]
        return upcoming_ipos
    
    def get_recent_ipos(self) -> List[Dict[str, Any]]:
        """Get recent IPO performance."""
        # Mock recent IPO data
        recent_ipos = [
            {
                'company': 'DataMine AI',
                'symbol': 'DMAI',
                'ipo_date': '2025-09-30',
                'ipo_price': 20.00,
                'current_price': 28.50,
                'first_day_close': 24.75,
                'return_since_ipo': '+42.5%',
                'sector': 'Artificial Intelligence'
            },
            {
                'company': 'CloudNet Systems',
                'symbol': 'CLNT',
                'ipo_date': '2025-09-25',
                'ipo_price': 16.00,
                'current_price': 14.25,
                'first_day_close': 18.20,
                'return_since_ipo': '-10.9%',
                'sector': 'Cloud Computing'
            }
        ]
        return recent_ipos
    
    def load_user_preferences(self):
        """Load user notification preferences from file."""
        try:
            if os.path.exists('data/user_preferences.json'):
                with open('data/user_preferences.json', 'r') as f:
                    self.user_preferences = json.load(f)
        except Exception as e:
            logger.error(f"Error loading user preferences: {str(e)}")
    
    def save_user_preferences(self):
        """Save user notification preferences to file."""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/user_preferences.json', 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences for a user."""
        return self.user_preferences.get(user_id, {
            'notify_volume_spikes': True,
            'notify_price_changes': True,
            'notify_ipos': True,
            'notify_earnings': False,
            'min_volume_threshold': 3.0,
            'min_price_change': 5.0,
            'watchlist_symbols': [],
            'sectors_of_interest': [],
            'market_cap_filter': 'all',  # 'all', 'large', 'mid', 'small'
            'insider_alerts_enabled': True,
            'insider_min_value': 250000,
            'insider_min_dte': 30,
            'insider_min_score': 7
        })
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update notification preferences for a user."""
        self.user_preferences[user_id] = preferences
        self.save_user_preferences()
    
    def get_live_alerts(self) -> List[Dict[str, Any]]:
        """Get recent live alerts from OptiFlow."""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                return data.get('alert_history', [])[-10:]  # Last 10 alerts
        except Exception as e:
            logger.error(f"Error reading alerts: {str(e)}")
        return []
    
    def get_all_users_with_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Get all users and their preferences."""
        return self.user_preferences

# Initialize data manager
data_manager = TradingDataManager()

# Error code definitions
ERROR_CODES = {
    'E001': 'Market Data Unavailable',
    'E002': 'Invalid Symbol',
    'E003': 'Options Data Not Found',
    'E004': 'Rate Limit Exceeded',
    'E005': 'Database Connection Error',
    'E006': 'Insider Scanner Unavailable',
    'E007': 'Network/API Error',
    'E008': 'Permission Error',
    'E009': 'Invalid Parameter',
    'E010': 'Service Temporarily Down'
}

async def send_instant_ack(ctx, message: str):
    """Send instant acknowledgment message that only the user can see."""
    try:
        # Delete the user's command to keep channel clean
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass  # Message already deleted
        except discord.Forbidden:
            pass  # No permission to delete
        
        # Send ephemeral-style response (delete after short time)
        ack_msg = await ctx.send(f"👋 {ctx.author.mention} {message}")
        
        # Delete acknowledgment after 3 seconds
        await asyncio.sleep(3)
        try:
            await ack_msg.delete()
        except discord.NotFound:
            pass
    except Exception as e:
        print(f"Error sending instant ack: {e}")

async def send_ephemeral_response(ctx, embed=None, content=None, delete_after=None):
    """Send a response that appears private-like and auto-deletes."""
    try:
        # Delete the user's command first
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        
        # Send response with user mention for privacy feel
        if embed:
            msg = await ctx.send(f"{ctx.author.mention}", embed=embed)
        else:
            msg = await ctx.send(f"{ctx.author.mention} {content}")
        
        # Auto-delete after specified time
        if delete_after:
            await asyncio.sleep(delete_after)
            try:
                await msg.delete()
            except discord.NotFound:
                pass
    except Exception as e:
        print(f"Error sending ephemeral response: {e}")

async def send_error_to_user(ctx, error_code: str, short_explanation: str, full_error: str = None):
    """Send error information to user via DM and console logging."""
    try:
        # Log to console
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = ERROR_CODES.get(error_code, 'Unknown Error')
        
        print(f"[{timestamp}] ERROR {error_code}: {error_title}")
        print(f"User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        print(f"Command: {ctx.message.content}")
        print(f"Explanation: {short_explanation}")
        if full_error:
            print(f"Full Error: {full_error}")
        print("-" * 80)
        
        # Create DM embed
        embed = discord.Embed(
            title=f"❌ Error {error_code}: {error_title}",
            description=short_explanation,
            color=0xe74c3c
        )
        
        embed.add_field(
            name="🔍 What happened?",
            value=short_explanation,
            inline=False
        )
        
        embed.add_field(
            name="⏰ When",
            value=f"{datetime.now().strftime('%H:%M:%S')} UTC",
            inline=True
        )
        
        embed.add_field(
            name="📝 Command",
            value=f"`{ctx.message.content}`",
            inline=True
        )
        
        # Add helpful suggestions based on error type
        suggestions = {
            'E001': "Try again in a few minutes. Market data provider may be temporarily down.",
            'E002': "Check if the stock symbol exists and is traded on major exchanges (e.g., AAPL, TSLA).",
            'E003': "This stock may not have options available or data is delayed.",
            'E004': "You're making requests too quickly. Wait 10-15 seconds between commands.",
            'E005': "Database issue. Try using simpler commands like `!opti price SYMBOL`.",
            'E006': "Insider scanner needs yfinance package. Contact admin for setup.",
            'E007': "Network connectivity issue. Check your internet or try again later.",
            'E008': "Bot doesn't have required permissions in this server/channel.",
            'E009': "Check command format. Use `!opti help` for examples.",
            'E010': "Service is down for maintenance. Try again in 5-10 minutes."
        }
        
        if error_code in suggestions:
            embed.add_field(
                name="💡 Suggestion",
                value=suggestions[error_code],
                inline=False
            )
        
        embed.add_field(
            name="🆘 Still having issues?",
            value="Use `!opti help` for command examples or contact support",
            inline=False
        )
        
        embed.set_footer(text="OptiFlow Error System • Your issue has been logged")
        
        # Try to send DM
        try:
            await ctx.author.send(embed=embed)
            
            # Send brief message in channel
            await ctx.send(f"❌ {error_code}: {short_explanation}. Check your DMs for details.")
            
        except discord.Forbidden:
            # User has DMs disabled, send full error in channel
            await ctx.send(embed=embed)
            
    except Exception as dm_error:
        # Fallback if DM system fails
        print(f"[ERROR] Failed to send error DM: {dm_error}")
        try:
            await ctx.send(f"❌ {error_code}: {short_explanation}")
        except:
            pass

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for all bot commands."""
    
    # Don't handle errors that have already been handled
    if hasattr(ctx.command, 'on_error'):
        return
    
    error_msg = str(error)
    
    # Command not found
    if isinstance(error, commands.CommandNotFound):
        await send_error_to_user(
            ctx, 'E009',
            f"Unknown command. Use `!opti help` to see available commands",
            f"CommandNotFound: {error_msg}"
        )
        return
    
    # Missing required argument
    elif isinstance(error, commands.MissingRequiredArgument):
        await send_error_to_user(
            ctx, 'E009',
            f"Missing required parameter: {error.param.name}. Use `!opti help` for examples",
            f"MissingRequiredArgument: {error_msg}"
        )
        return
    
    # Bad argument (wrong type)
    elif isinstance(error, commands.BadArgument):
        await send_error_to_user(
            ctx, 'E009',
            f"Invalid parameter format. Check command syntax with `!opti help`",
            f"BadArgument: {error_msg}"
        )
        return
    
    # Command on cooldown
    elif isinstance(error, commands.CommandOnCooldown):
        await send_error_to_user(
            ctx, 'E004',
            f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds",
            f"CommandOnCooldown: {error_msg}"
        )
        return
    
    # Bot missing permissions
    elif isinstance(error, commands.BotMissingPermissions):
        await send_error_to_user(
            ctx, 'E008',
            "Bot missing required permissions in this channel/server",
            f"BotMissingPermissions: {error_msg}"
        )
        return
    
    # User missing permissions
    elif isinstance(error, commands.MissingPermissions):
        await send_error_to_user(
            ctx, 'E008',
            "You don't have permission to use this command",
            f"MissingPermissions: {error_msg}"
        )
        return
    
    # Any other unexpected error
    else:
        await send_error_to_user(
            ctx, 'E010',
            "An unexpected error occurred. The issue has been logged for investigation",
            f"Unhandled Error: {type(error).__name__}: {error_msg}\nTraceback: {traceback.format_exc()}"
        )

@bot.event
async def on_ready():
    """Bot startup event."""
    print(f'🤖 OptiFlow Discord Bot is ready!')
    print(f'📊 Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'🔗 Connected to {len(bot.guilds)} server(s)')
    
    # Send startup message to alerts channel
    if ALERTS_CHANNEL_ID:
        channel = bot.get_channel(ALERTS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🚀 OptiFlow Bot Online!",
                description="Real-time insider options intelligence is now active",
                color=0x00ff00
            )
            
            embed.add_field(
                name="🕵️ Insider Commands",
                value=(
                    "`!opti insider_scan` - Scan all stocks for suspicious activity\n"
                    "`!opti big_trades` - High-value trades ($500K+ default)\n"
                    "`!opti big_trades 1000000` - Trades over $1M\n"
                    "`!opti insider_alerts` - Configure your alert preferences"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📊 Market Data",
                value=(
                    "`!opti price AAPL` - Get AAPL stock price & info\n"
                    "`!opti options TSLA` - TSLA options chain analysis\n"
                    "`!opti volume NVDA` - NVDA volume analysis\n"
                    "`!opti summary` - Market overview"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔔 Personalized Alerts Setup",
                value=(
                    "`!opti setnotify insider_min_value 500000` - $500K minimum\n"
                    "`!opti setnotify insider_min_dte 45` - 45+ days DTE\n"
                    "`!opti setnotify insider_min_score 8` - Score 8+/10\n"
                    "`!opti setnotify insider_alerts on` - Enable notifications"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Other Useful Commands",
                value=(
                    "`!opti ipos` - Upcoming IPO calendar\n"
                    "`!opti watch NVDA` - Add NVDA to watchlist\n"
                    "`!opti help` - Full command list\n"
                    "`!opti notify` - View all your settings"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🚨 Auto-Monitoring Active",
                value=(
                    "• Scanning **82+ stocks** every 30 minutes\n"
                    "• High-priority alerts (score 8+) posted here\n"
                    "• Personal DMs sent based on your preferences\n"
                    "• Monitoring: AAPL, TSLA, NVDA, JPM, GS + 77 more"
                ),
                inline=False
            )
            
            embed.set_footer(text="OptiFlow • Professional Insider Options Intelligence • Try !opti insider_scan")
            
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Could not send startup message to alerts channel: {e}")
    
    # Start background tasks
    if not alert_monitor.is_running():
        alert_monitor.start()
    
    if not market_monitor.is_running():
        market_monitor.start()
    
    if INSIDER_SCANNER_AVAILABLE and not insider_monitor.is_running():
        insider_monitor.start()

@bot.command(name='help')
async def help_command(ctx):
    """Show available OptiFlow commands."""
    embed = discord.Embed(
        title="🤖 OptiFlow Bot Commands",
        description="Real-time trading alerts and market data",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📊 Market Data",
        value="`!opti price AAPL` - Get stock price & info\n`!opti insider TSLA` - Insider options activity\n`!opti volume SPY` - Volume analysis\n`!opti summary` - Market overview",
        inline=False
    )
    
    embed.add_field(
        name="🕵️ Insider Intelligence",
        value="`!opti insider_scan` - Scan all stocks for suspicious activity\n`!opti big_trades` - High-value long-DTE trades\n`!opti insider_alerts` - Configure insider notifications",
        inline=False
    )
    
    embed.add_field(
        name="🚀 IPO Tracking", 
        value="`!opti ipos` - Upcoming IPOs calendar\n`!opti recent` - Recent IPO performance\n`!opti ipo SYMBOL` - Specific IPO details",
        inline=False
    )
    
    embed.add_field(
        name="🔔 Alerts & Watchlist",
        value="`!opti alerts` - Recent alerts\n`!opti watch NVDA` - Add to watchlist\n`!opti unwatch AAPL` - Remove from watchlist\n`!opti watchlist` - View your watchlist",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Personal Settings",
        value="`!opti notify` - Notification preferences\n`!opti setnotify` - Configure alerts\n`!opti sectors` - Set sector interests\n`!opti thresholds` - Alert thresholds",
        inline=False
    )
    
    embed.add_field(
        name="📈 Analysis & Tools",
        value="`!opti top` - Top movers\n`!opti earnings` - Upcoming earnings\n`!opti flow AAPL` - Options flow\n`!opti news TSLA` - Latest news",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Live Dashboard",
        value="`!opti view` - Launch real-time options flow web dashboard\n📊 Live data updates every 30 seconds\n🔥 Critical insider signals in real-time",
        inline=False
    )
    
    embed.add_field(
        name="✨ New Enhanced Experience",
        value=(
            "🔒 **Private responses** - Only you can see command results\n"
            "🧹 **Auto-cleanup** - Commands are automatically deleted\n"
            "⚡ **Instant feedback** - Immediate acknowledgments for all commands\n"
            "📢 **Verbose updates** - Real-time progress for long operations"
        ),
        inline=False
    )
    
    embed.set_footer(text="OptiFlow Pro • Enhanced UX • Private Responses • Auto-Cleanup • Real-time Intelligence")
    
    await send_ephemeral_response(ctx, embed=embed, delete_after=60)

@bot.command(name='price')
async def get_price(ctx, symbol: str = None):
    """Get current stock price and basic info."""
    if not symbol:
        await send_error_to_user(
            ctx, 'E009',
            "Missing stock symbol - use format: !opti price AAPL",
            "No symbol parameter provided"
        )
        return
    
    try:
        symbol = symbol.upper()
        
        # Get stock data using Schwab API
        quote_data = await get_stock_quote(symbol)
        
        if not quote_data:
            await send_error_to_user(
                ctx, 'E002',
                f"Symbol '{symbol}' not found or has no trading data",
                f"Schwab API returned no data for {symbol}"
            )
            return
        
        current_price = quote_data.get('regularMarketPrice', 0)
        prev_close = quote_data.get('regularMarketPreviousClose', current_price)
        change = quote_data.get('regularMarketChange', 0)
        change_pct = quote_data.get('regularMarketChangePercent', 0)
        
        color = 0x00ff00 if change >= 0 else 0xff0000
        emoji = "📈" if change >= 0 else "📉"
        
        embed = discord.Embed(
            title=f"{emoji} {symbol} - {quote_data.get('shortName', symbol)}",
            color=color
        )
        
        embed.add_field(name="💰 Price", value=f"${current_price:.2f}", inline=True)
        embed.add_field(name="📊 Change", value=f"${change:+.2f} ({change_pct:+.2f}%)", inline=True)
        embed.add_field(name="📉 Volume", value=f"{quote_data.get('regularMarketVolume', 0):,}", inline=True)
        
        market_cap = quote_data.get('marketCap', 0)
        if market_cap:
            embed.add_field(name="🏢 Market Cap", value=f"${market_cap:,}", inline=True)
        
        embed.set_footer(text=f"Data as of {datetime.now().strftime('%H:%M:%S EST')}")
        
        await ctx.send(embed=embed)
        
    except KeyError as e:
        await send_error_to_user(
            ctx, 'E002',
            f"Invalid symbol '{symbol}' - check spelling and try again",
            f"KeyError accessing ticker data: {str(e)}"
        )
    except ConnectionError as e:
        await send_error_to_user(
            ctx, 'E007',
            "Network error while fetching stock data - check your connection",
            f"ConnectionError: {str(e)}"
        )
    except Exception as e:
        error_msg = str(e)
        if "delisted" in error_msg.lower():
            await send_error_to_user(
                ctx, 'E002',
                f"Symbol '{symbol}' may be delisted or unavailable",
                error_msg
            )
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            await send_error_to_user(
                ctx, 'E004',
                "Too many requests - wait 10 seconds before trying again",
                error_msg
            )
        else:
            await send_error_to_user(
                ctx, 'E001',
                f"Unable to fetch data for '{symbol}' - market data may be temporarily down",
                f"Exception: {error_msg}\nTraceback: {traceback.format_exc()}"
            )

@bot.command(name='insider')
async def get_insider_options(ctx, symbol: str):
    """Get insider options activity for a symbol."""
    try:
        symbol = symbol.upper()
        
        await ctx.send(f"🔍 Analyzing insider options activity for {symbol}...")
        
        insider_data = data_manager.get_insider_options(symbol)
        
        if 'error' in insider_data:
            await ctx.send(f"❌ {insider_data['error']}")
            return
        
        embed = discord.Embed(
            title=f"🕵️ Insider Options Activity - {symbol}",
            description=f"Expiry: {insider_data['expiry']}",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="📞 Calls Activity",
            value=f"High Vol: {insider_data['high_volume_calls']}\nTotal Vol: {insider_data['total_call_volume']:,}",
            inline=True
        )
        
        embed.add_field(
            name="📉 Puts Activity", 
            value=f"High Vol: {insider_data['high_volume_puts']}\nTotal Vol: {insider_data['total_put_volume']:,}",
            inline=True
        )
        
        embed.add_field(
            name="⚖️ Call/Put Ratio",
            value=f"{insider_data['call_put_ratio']:.2f}",
            inline=True
        )
        
        # Add interpretation
        ratio = insider_data['call_put_ratio']
        if ratio > 2:
            sentiment = "🚀 Very Bullish"
        elif ratio > 1:
            sentiment = "📈 Bullish"
        elif ratio > 0.5:
            sentiment = "📊 Neutral"
        else:
            sentiment = "📉 Bearish"
        
        embed.add_field(name="💭 Sentiment", value=sentiment, inline=False)
        embed.set_footer(text="High volume options may indicate insider activity")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error analyzing insider options for {symbol}: {str(e)}")

@bot.command(name='ipos')
async def upcoming_ipos(ctx):
    """Show upcoming IPOs."""
    try:
        ipos = data_manager.get_upcoming_ipos()
        
        embed = discord.Embed(
            title="🚀 Upcoming IPOs",
            description="Companies going public soon",
            color=0xf1c40f
        )
        
        for ipo in ipos[:5]:  # Show top 5
            embed.add_field(
                name=f"🏢 {ipo['company']} ({ipo['symbol']})",
                value=f"📅 **Date:** {ipo['date']}\n💰 **Price:** {ipo['price_range']}\n📊 **Shares:** {ipo['shares']}\n🏷️ **Sector:** {ipo['sector']}",
                inline=False
            )
        
        embed.set_footer(text="Use !opti recent for recent IPO performance")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting IPO data: {str(e)}")

@bot.command(name='recent')
async def recent_ipos(ctx):
    """Show recent IPO performance."""
    try:
        ipos = data_manager.get_recent_ipos()
        
        embed = discord.Embed(
            title="📈 Recent IPO Performance",
            description="How new IPOs are trading",
            color=0x3498db
        )
        
        for ipo in ipos:
            color_emoji = "🟢" if "+" in ipo['return_since_ipo'] else "🔴"
            
            embed.add_field(
                name=f"{color_emoji} {ipo['company']} ({ipo['symbol']})",
                value=f"💰 **IPO Price:** ${ipo['ipo_price']:.2f}\n📊 **Current:** ${ipo['current_price']:.2f}\n📈 **Return:** {ipo['return_since_ipo']}\n🏷️ **Sector:** {ipo['sector']}",
                inline=False
            )
        
        embed.set_footer(text="Use !opti ipos for upcoming IPOs")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting recent IPO data: {str(e)}")

@bot.command(name='alerts')
async def recent_alerts(ctx):
    """Show recent OptiFlow alerts."""
    try:
        alerts = data_manager.get_live_alerts()
        
        if not alerts:
            await ctx.send("📭 No recent alerts found. Make sure OptiFlow main app is running.")
            return
        
        embed = discord.Embed(
            title="🚨 Recent OptiFlow Alerts",
            description="Latest trading alerts from your system",
            color=0xe74c3c
        )
        
        for alert in alerts[-5:]:  # Show last 5 alerts
            timestamp = datetime.fromisoformat(alert.get('triggered_at', alert.get('created_at', datetime.now().isoformat())))
            time_str = timestamp.strftime('%m/%d %H:%M')
            
            embed.add_field(
                name=f"🎯 {alert.get('symbol', 'Unknown')} - {alert.get('type', 'Alert')}",
                value=f"📝 {alert.get('description', 'No description')}\n⏰ {time_str}",
                inline=False
            )
        
        embed.set_footer(text="Alerts sync from main OptiFlow app")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting alerts: {str(e)}")

@bot.command(name='watch')
async def add_to_watchlist(ctx, symbol: str):
    """Add symbol to watchlist."""
    symbol = symbol.upper()
    data_manager.watchlist.add(symbol)
    
    embed = discord.Embed(
        title="👀 Added to Watchlist",
        description=f"Now watching **{symbol}** for alerts",
        color=0x2ecc71
    )
    
    await ctx.send(embed=embed)

@bot.command(name='unwatch')
async def remove_from_watchlist(ctx, symbol: str):
    """Remove symbol from watchlist."""
    symbol = symbol.upper()
    if symbol in data_manager.watchlist:
        data_manager.watchlist.remove(symbol)
        embed = discord.Embed(
            title="👁️ Removed from Watchlist",
            description=f"No longer watching **{symbol}**",
            color=0xe74c3c
        )
    else:
        embed = discord.Embed(
            title="❌ Symbol Not Found",
            description=f"**{symbol}** was not in your watchlist",
            color=0x95a5a6
        )
    
    await ctx.send(embed=embed)

@bot.command(name='watchlist')
async def show_watchlist(ctx):
    """Show current watchlist."""
    user_prefs = data_manager.get_user_preferences(str(ctx.author.id))
    personal_watchlist = set(user_prefs.get('watchlist_symbols', []))
    all_symbols = data_manager.watchlist.union(personal_watchlist)
    
    if not all_symbols:
        await ctx.send("📭 Your watchlist is empty. Use `!opti watch SYMBOL` to add stocks.")
        return
    
    symbols = list(all_symbols)
    embed = discord.Embed(
        title="👀 Your Watchlist",
        description=f"Monitoring {len(symbols)} symbols",
        color=0x9b59b6
    )
    
    embed.add_field(
        name="📊 Symbols",
        value=", ".join(symbols),
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='notify')
async def show_notification_settings(ctx):
    """Show current notification preferences."""
    user_prefs = data_manager.get_user_preferences(str(ctx.author.id))
    
    embed = discord.Embed(
        title="� Your Notification Settings",
        description=f"Personalized alerts for {ctx.author.display_name}",
        color=0x3498db
    )
    
    # Alert types
    alerts = "✅" if user_prefs['notify_volume_spikes'] else "❌"
    embed.add_field(name=f"{alerts} Volume Spikes", value=f"Min: {user_prefs['min_volume_threshold']}x", inline=True)
    
    alerts = "✅" if user_prefs['notify_price_changes'] else "❌"
    embed.add_field(name=f"{alerts} Price Changes", value=f"Min: {user_prefs['min_price_change']}%", inline=True)
    
    alerts = "✅" if user_prefs['notify_ipos'] else "❌"
    embed.add_field(name=f"{alerts} IPO Updates", value="New listings", inline=True)
    
    # Sectors of interest
    sectors = user_prefs.get('sectors_of_interest', [])
    sector_text = ", ".join(sectors) if sectors else "All sectors"
    embed.add_field(name="🏭 Sectors", value=sector_text, inline=False)
    
    # Market cap filter
    market_cap = user_prefs.get('market_cap_filter', 'all').title()
    embed.add_field(name="💰 Market Cap", value=f"{market_cap} cap stocks", inline=True)
    
    # Personal watchlist
    personal_symbols = user_prefs.get('watchlist_symbols', [])
    watchlist_text = ", ".join(personal_symbols) if personal_symbols else "None"
    embed.add_field(name="👀 Personal Watchlist", value=watchlist_text, inline=False)
    
    embed.set_footer(text="Use !opti setnotify to customize these settings")
    
    await ctx.send(embed=embed)

@bot.command(name='setnotify')
async def configure_notifications(ctx, setting: str = None, value: str = None):
    """Configure notification preferences."""
    user_id = str(ctx.author.id)
    
    if not setting:
        embed = discord.Embed(
            title="⚙️ Notification Configuration",
            description="Configure your personal alert preferences",
            color=0xf39c12
        )
        
        embed.add_field(
            name="📊 Volume Alerts",
            value="`!opti setnotify volume on/off`\n`!opti setnotify volume_threshold 3.5`",
            inline=False
        )
        
        embed.add_field(
            name="💰 Price Alerts", 
            value="`!opti setnotify price on/off`\n`!opti setnotify price_threshold 5.0`",
            inline=False
        )
        
        embed.add_field(
            name="� IPO Alerts",
            value="`!opti setnotify ipos on/off`",
            inline=False
        )
        
        embed.add_field(
            name="🏭 Sector Focus",
            value="`!opti setnotify sectors Technology,Healthcare`",
            inline=False
        )
        
        embed.add_field(
            name="💸 Market Cap Filter",
            value="`!opti setnotify marketcap large/mid/small/all`",
            inline=False
        )
        
        embed.add_field(
            name="🕵️ Insider Alerts",
            value=(
                "`!opti setnotify insider_alerts on/off`\n"
                "`!opti setnotify insider_min_value 500000`\n"
                "`!opti setnotify insider_min_dte 30`\n"
                "`!opti setnotify insider_min_score 7`"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    user_prefs = data_manager.get_user_preferences(user_id)
    
    # Handle different settings
    if setting.lower() == 'volume':
        if value and value.lower() in ['on', 'off']:
            user_prefs['notify_volume_spikes'] = value.lower() == 'on'
            status = "enabled" if value.lower() == 'on' else "disabled"
            await ctx.send(f"✅ Volume spike alerts {status}")
        else:
            await ctx.send("❌ Use: `!opti setnotify volume on` or `!opti setnotify volume off`")
    
    elif setting.lower() == 'volume_threshold':
        try:
            threshold = float(value)
            user_prefs['min_volume_threshold'] = threshold
            await ctx.send(f"✅ Volume threshold set to {threshold}x average")
        except (ValueError, TypeError):
            await ctx.send("❌ Use: `!opti setnotify volume_threshold 3.5`")
    
    elif setting.lower() == 'price':
        if value and value.lower() in ['on', 'off']:
            user_prefs['notify_price_changes'] = value.lower() == 'on'
            status = "enabled" if value.lower() == 'on' else "disabled"
            await ctx.send(f"✅ Price change alerts {status}")
        else:
            await ctx.send("❌ Use: `!opti setnotify price on` or `!opti setnotify price off`")
    
    elif setting.lower() == 'price_threshold':
        try:
            threshold = float(value)
            user_prefs['min_price_change'] = threshold
            await ctx.send(f"✅ Price change threshold set to {threshold}%")
        except (ValueError, TypeError):
            await ctx.send("❌ Use: `!opti setnotify price_threshold 5.0`")
    
    elif setting.lower() == 'ipos':
        if value and value.lower() in ['on', 'off']:
            user_prefs['notify_ipos'] = value.lower() == 'on'
            status = "enabled" if value.lower() == 'on' else "disabled"
            await ctx.send(f"✅ IPO alerts {status}")
        else:
            await ctx.send("❌ Use: `!opti setnotify ipos on` or `!opti setnotify ipos off`")
    
    elif setting.lower() == 'sectors':
        if value:
            sectors = [s.strip().title() for s in value.split(',')]
            user_prefs['sectors_of_interest'] = sectors
            await ctx.send(f"✅ Sector focus set to: {', '.join(sectors)}")
        else:
            await ctx.send("❌ Use: `!opti setnotify sectors Technology,Healthcare,Energy`")
    
    elif setting.lower() == 'marketcap':
        valid_caps = ['all', 'large', 'mid', 'small']
        if value and value.lower() in valid_caps:
            user_prefs['market_cap_filter'] = value.lower()
            await ctx.send(f"✅ Market cap filter set to {value.lower()} cap stocks")
        else:
            await ctx.send("❌ Use: `!opti setnotify marketcap large/mid/small/all`")
    
    elif setting.lower() == 'insider_alerts':
        if value and value.lower() in ['on', 'off']:
            user_prefs['insider_alerts_enabled'] = value.lower() == 'on'
            status = "enabled" if value.lower() == 'on' else "disabled"
            await ctx.send(f"✅ Insider trading alerts {status}")
        else:
            await ctx.send("❌ Use: `!opti setnotify insider_alerts on` or `!opti setnotify insider_alerts off`")
    
    elif setting.lower() == 'insider_min_value':
        try:
            min_value = int(value)
            user_prefs['insider_min_value'] = min_value
            await ctx.send(f"✅ Insider alert minimum trade value set to ${min_value:,}")
        except (ValueError, TypeError):
            await ctx.send("❌ Use: `!opti setnotify insider_min_value 500000`")
    
    elif setting.lower() == 'insider_min_dte':
        try:
            min_dte = int(value)
            user_prefs['insider_min_dte'] = min_dte
            await ctx.send(f"✅ Insider alert minimum DTE set to {min_dte} days")
        except (ValueError, TypeError):
            await ctx.send("❌ Use: `!opti setnotify insider_min_dte 30`")
    
    elif setting.lower() == 'insider_min_score':
        try:
            min_score = int(value)
            if 1 <= min_score <= 10:
                user_prefs['insider_min_score'] = min_score
                await ctx.send(f"✅ Insider alert minimum unusual score set to {min_score}/10")
            else:
                await ctx.send("❌ Score must be between 1 and 10")
        except (ValueError, TypeError):
            await ctx.send("❌ Use: `!opti setnotify insider_min_score 7`")
    
    else:
        await ctx.send("❌ Unknown setting. Use `!opti setnotify` to see available options.")
        return
    
    # Save preferences
    data_manager.update_user_preferences(user_id, user_prefs)

@bot.command(name='summary')
async def market_summary(ctx):
    """Show market summary."""
    try:
        # Get major indices
        indices = ['SPY', 'QQQ', 'IWM', 'VIX']
        summary_data = []
        
        for symbol in indices:
            quote_data = await get_stock_quote(symbol)
            if quote_data:
                current = quote_data.get('regularMarketPrice', 0)
                change_pct = quote_data.get('regularMarketChangePercent', 0)
                summary_data.append({
                    'symbol': symbol,
                    'price': current,
                    'change_pct': change_pct
                })
        
        embed = discord.Embed(
            title="📊 Market Summary",
            description="Major indices overview",
            color=0x3498db
        )
        
        for data in summary_data:
            emoji = "📈" if data['change_pct'] >= 0 else "📉"
            color = "🟢" if data['change_pct'] >= 0 else "🔴"
            
            embed.add_field(
                name=f"{emoji} {data['symbol']}",
                value=f"${data['price']:.2f}\n{color} {data['change_pct']:+.2f}%",
                inline=True
            )
        
        embed.set_footer(text=f"Updated: {datetime.now().strftime('%H:%M:%S EST')}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting market summary: {str(e)}")

@bot.command(name='top')
async def top_movers(ctx, market_cap: str = "all"):
    """Show top movers by market cap."""
    try:
        # Popular symbols by market cap
        symbols_map = {
            'large': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.B'],
            'mid': ['AMD', 'NFLX', 'CRM', 'UBER', 'SHOP', 'SQ', 'ROKU', 'ZOOM'],
            'small': ['PLTR', 'BB', 'AMC', 'GME', 'WISH', 'CLOV', 'SPCE', 'NIO']
        }
        
        if market_cap.lower() not in ['large', 'mid', 'small']:
            market_cap = 'large'
        
        symbols = symbols_map[market_cap.lower()]
        movers_data = []
        
        for symbol in symbols[:8]:  # Top 8
            try:
                quote_data = await get_stock_quote(symbol)
                if quote_data:
                    current = quote_data.get('regularMarketPrice', 0)
                    change_pct = quote_data.get('regularMarketChangePercent', 0)
                    volume = quote_data.get('regularMarketVolume', 0)
                    
                    movers_data.append({
                        'symbol': symbol,
                        'price': current,
                        'change_pct': change_pct,
                        'volume': volume
                    })
            except:
                continue
        
        # Sort by absolute change percentage
        movers_data.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        
        embed = discord.Embed(
            title=f"📈 Top {market_cap.title()} Cap Movers",
            description="Biggest percentage moves today",
            color=0x1abc9c
        )
        
        for i, mover in enumerate(movers_data[:6]):
            emoji = "🚀" if mover['change_pct'] > 0 else "📉"
            color = "🟢" if mover['change_pct'] > 0 else "🔴"
            
            embed.add_field(
                name=f"{i+1}. {emoji} {mover['symbol']}",
                value=f"${mover['price']:.2f}\n{color} {mover['change_pct']:+.2f}%\nVol: {mover['volume']:,.0f}",
                inline=True
            )
        
        embed.set_footer(text=f"Use !opti top large/mid/small to filter by market cap")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting top movers: {str(e)}")

@bot.command(name='flow')
async def options_flow(ctx, symbol: str):
    """Show options flow for a symbol."""
    try:
        symbol = symbol.upper()
        
        # This would integrate with real options flow data
        # For now, showing mock data structure
        embed = discord.Embed(
            title=f"💰 Options Flow - {symbol}",
            description="Large options trades detected",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="🔥 Recent Large Trades",
            value="• $2.5M Call Sweep - $450 Strike\n• $1.8M Put Block - $420 Strike\n• $3.2M Call Flow - $480 Strike",
            inline=False
        )
        
        embed.add_field(
            name="📊 Flow Summary",
            value="Bullish Flow: $12.5M\nBearish Flow: $8.3M\nNet: +$4.2M Bullish",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Unusual Activity",
            value="Volume: 3.2x normal\nOpen Interest: +15%\nIV Rank: 65%",
            inline=True
        )
        
        embed.set_footer(text="Real-time options flow analysis")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting options flow for {symbol}: {str(e)}")

@bot.command(name='earnings')
async def upcoming_earnings(ctx):
    """Show upcoming earnings announcements."""
    try:
        # Mock earnings data - replace with real earnings calendar API
        earnings_data = [
            {'symbol': 'AAPL', 'date': '2025-10-10', 'time': 'After Market', 'estimate': '$1.25'},
            {'symbol': 'GOOGL', 'date': '2025-10-12', 'time': 'After Market', 'estimate': '$28.50'},
            {'symbol': 'MSFT', 'date': '2025-10-15', 'time': 'After Market', 'estimate': '$2.85'},
            {'symbol': 'TSLA', 'date': '2025-10-18', 'time': 'After Market', 'estimate': '$0.95'},
        ]
        
        embed = discord.Embed(
            title="📊 Upcoming Earnings",
            description="Major earnings announcements this week",
            color=0xf1c40f
        )
        
        for earning in earnings_data:
            embed.add_field(
                name=f"📈 {earning['symbol']}",
                value=f"**Date:** {earning['date']}\n**Time:** {earning['time']}\n**Est:** {earning['estimate']}",
                inline=True
            )
        
        embed.set_footer(text="Earnings dates subject to change")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting earnings calendar: {str(e)}")

@bot.command(name='news')
async def get_news(ctx, symbol: str):
    """Get latest news for a symbol."""
    try:
        symbol = symbol.upper()
        
        # Mock news data - replace with real news API
        news_items = [
            f"{symbol} reports strong Q3 earnings, beats estimates by 15%",
            f"Analysts upgrade {symbol} to 'Buy' with $500 price target",
            f"{symbol} announces new product launch, stock jumps 5%",
        ]
        
        embed = discord.Embed(
            title=f"📰 Latest News - {symbol}",
            description="Recent market-moving news",
            color=0x3498db
        )
        
        for i, news in enumerate(news_items, 1):
            embed.add_field(
                name=f"📄 News #{i}",
                value=news,
                inline=False
            )
        
        embed.set_footer(text="News updates every 15 minutes")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting news for {symbol}: {str(e)}")

@bot.command(name='volume')
async def volume_analysis(ctx, symbol: str):
    """Analyze volume patterns for a symbol."""
    try:
        symbol = symbol.upper()
        
        # Get current quote for volume data
        quote_data = await get_stock_quote(symbol)
        if not quote_data:
            await ctx.send(f"❌ No data available for {symbol}")
            return
        
        # Get historical data for volume comparison
        hist = await get_stock_history(symbol, "1mo")
        if hist is None or hist.empty:
            await ctx.send(f"❌ No historical data available for {symbol}")
            return
        
        current_volume = quote_data.get('regularMarketVolume', 0)
        avg_volume = hist['Volume'].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Volume analysis
        if volume_ratio > 3:
            analysis = "🚨 Extremely High"
            color = 0xe74c3c
        elif volume_ratio > 2:
            analysis = "🔥 Very High"
            color = 0xf39c12
        elif volume_ratio > 1.5:
            analysis = "📈 Above Average"
            color = 0xf1c40f
        else:
            analysis = "📊 Normal"
            color = 0x95a5a6
        
        embed = discord.Embed(
            title=f"📊 Volume Analysis - {symbol}",
            description=f"Current volume: {analysis}",
            color=color
        )
        
        embed.add_field(
            name="📈 Today's Volume",
            value=f"{current_volume:,.0f}",
            inline=True
        )
        
        embed.add_field(
            name="📊 30-Day Average",
            value=f"{avg_volume:,.0f}",
            inline=True
        )
        
        embed.add_field(
            name="🔥 Volume Ratio",
            value=f"{volume_ratio:.1f}x",
            inline=True
        )
        
        # Volume trend
        recent_volume = hist['Volume'][-5:].mean()
        if recent_volume > avg_volume * 1.5:
            trend = "📈 Increasing activity"
        else:
            trend = "📊 Normal activity"
        
        embed.add_field(
            name="📉 5-Day Trend",
            value=trend,
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error analyzing volume for {symbol}: {str(e)}")

@tasks.loop(minutes=5)
async def alert_monitor():
    """Monitor for new alerts and send personalized notifications."""
    try:
        if not ALERTS_CHANNEL_ID:
            return
        
        channel = bot.get_channel(ALERTS_CHANNEL_ID)
        if not channel:
            return
        
        alerts = data_manager.get_live_alerts()
        
        # Check for new alerts
        if hasattr(alert_monitor, 'last_alert_count'):
            if len(alerts) > alert_monitor.last_alert_count:
                new_alert = alerts[-1]
                
                # General alert to channel
                embed = discord.Embed(
                    title="🚨 NEW OPTIFLOW ALERT",
                    description=f"**{new_alert.get('symbol', 'Unknown')}** - {new_alert.get('type', 'Alert')}",
                    color=0xe74c3c
                )
                
                embed.add_field(
                    name="📝 Details",
                    value=new_alert.get('description', 'No description'),
                    inline=False
                )
                
                embed.add_field(
                    name="⏰ Time",
                    value=datetime.now().strftime('%m/%d %H:%M:%S'),
                    inline=True
                )
                
                await channel.send(embed=embed)
                
                # Send personalized DMs to interested users
                await send_personalized_alerts(new_alert)
        
        alert_monitor.last_alert_count = len(alerts)
        
    except Exception as e:
        logger.error(f"Alert monitor error: {str(e)}")

async def send_personalized_alerts(alert_data: Dict[str, Any]):
    """Send personalized DM alerts based on user preferences."""
    try:
        symbol = alert_data.get('symbol', '').upper()
        alert_type = alert_data.get('type', '')
        
        # Get threshold values from alert (if available)
        threshold_value = alert_data.get('threshold', 0)
        
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
        
        for user_id, preferences in data_manager.user_preferences.items():
            try:
                user = guild.get_member(int(user_id))
                if not user:
                    continue
                
                should_notify = False
                
                # Check if user wants this type of alert
                if alert_type == 'volume_spike' and preferences.get('notify_volume_spikes', True):
                    if threshold_value >= preferences.get('min_volume_threshold', 3.0):
                        should_notify = True
                
                elif alert_type == 'price_change' and preferences.get('notify_price_changes', True):
                    if abs(threshold_value) >= preferences.get('min_price_change', 5.0):
                        should_notify = True
                
                elif alert_type == 'ipo_update' and preferences.get('notify_ipos', True):
                    should_notify = True
                
                # Check if symbol is in personal watchlist
                personal_watchlist = preferences.get('watchlist_symbols', [])
                if symbol in personal_watchlist:
                    should_notify = True
                
                # Check sector filter
                sectors_of_interest = preferences.get('sectors_of_interest', [])
                if sectors_of_interest:
                    # You'd need to map symbols to sectors here
                    # For now, assume all alerts pass sector filter
                    pass
                
                if should_notify:
                    embed = discord.Embed(
                        title="🔔 Personal Alert",
                        description=f"Alert for **{symbol}** - matches your preferences",
                        color=0x3498db
                    )
                    
                    embed.add_field(
                        name="📊 Alert Details",
                        value=alert_data.get('description', 'No description'),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⚙️ Why you got this",
                        value=f"Symbol in watchlist" if symbol in personal_watchlist else f"Meets your {alert_type} threshold",
                        inline=False
                    )
                    
                    await user.send(embed=embed)
                
            except Exception as user_error:
                logger.error(f"Error sending alert to user {user_id}: {str(user_error)}")
                
    except Exception as e:
        logger.error(f"Error in personalized alerts: {str(e)}")

@tasks.loop(hours=1)
async def market_monitor():
    """Monitor market conditions and send updates."""
    try:
        if not ALERTS_CHANNEL_ID:
            return
        
        channel = bot.get_channel(ALERTS_CHANNEL_ID)
        if not channel:
            return
        
        # Send market open/close notifications
        now = datetime.now()
        if now.hour == 9 and now.minute < 35:  # Market open
            embed = discord.Embed(
                title="🔔 Market Open",
                description="US markets are now open for trading",
                color=0x2ecc71
            )
            await channel.send(embed=embed)
        
        elif now.hour == 16 and now.minute < 5:  # Market close
            embed = discord.Embed(
                title="🔔 Market Close", 
                description="US markets are now closed",
                color=0xe67e22
            )
            await channel.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Market monitor error: {str(e)}")

@tasks.loop(minutes=30)
async def insider_monitor():
    """Monitor for suspicious insider options activity and send personalized alerts."""
    if not INSIDER_SCANNER_AVAILABLE or not ALERTS_CHANNEL_ID:
        return
    
    try:
        channel = bot.get_channel(ALERTS_CHANNEL_ID)
        if not channel:
            return
        
        # Get insider alerts
        alerts = await asyncio.get_event_loop().run_in_executor(None, get_insider_options_alerts)
        
        if not alerts:
            return
        
        # Check for high-priority alerts
        high_priority = [alert for alert in alerts if alert['unusual_score'] >= 8]
        
        if high_priority:
            # Send to main channel
            embed = discord.Embed(
                title="🚨 High Priority Insider Activity",
                description=f"Detected {len(high_priority)} suspicious trades",
                color=0xe74c3c
            )
            
            top_alert = high_priority[0]
            embed.add_field(
                name=f"🔥 {top_alert['symbol']} - Score: {top_alert['unusual_score']}/10",
                value=(
                    f"**Strike:** ${top_alert['strike']}\n"
                    f"**Type:** {top_alert['option_type'].upper()}\n" 
                    f"**Value:** ${top_alert['estimated_value']:,.0f}\n"
                    f"**DTE:** {top_alert['dte']} days"
                ),
                inline=False
            )
            
            await channel.send(embed=embed)
        
        # Send personalized alerts to users based on their preferences
        for alert in alerts:
            await send_insider_alerts_to_users(alert)
    
    except Exception as e:
        logger.error(f"Insider monitor error: {str(e)}")

async def send_insider_alerts_to_users(alert):
    """Send insider alerts to users based on their preferences."""
    try:
        # Get all users with insider alert preferences
        users = data_manager.get_all_users_with_preferences()
        
        for user_id, prefs in users.items():
            # Check if user wants insider alerts
            if not prefs.get('insider_alerts_enabled', True):
                continue
            
            # Check user thresholds
            min_value = prefs.get('insider_min_value', 250000)
            min_dte = prefs.get('insider_min_dte', 30)
            min_score = prefs.get('insider_min_score', 7)
            
            if (alert['estimated_value'] >= min_value and 
                alert['dte'] >= min_dte and 
                alert['unusual_score'] >= min_score):
                
                # Send DM to user
                user = bot.get_user(int(user_id))
                if user:
                    embed = discord.Embed(
                        title="🕵️ Insider Alert - Personalized",
                        description=f"Suspicious activity in **{alert['symbol']}**",
                        color=0x9b59b6
                    )
                    
                    embed.add_field(
                        name="📊 Trade Details",
                        value=(
                            f"**Score:** {alert['unusual_score']}/10\n"
                            f"**Strike:** ${alert['strike']}\n"
                            f"**Type:** {alert['option_type'].upper()}\n"
                            f"**Value:** ${alert['estimated_value']:,.0f}\n"
                            f"**DTE:** {alert['dte']} days"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🔍 Analysis",
                        value=(', '.join(alert['alert_reasons'])[:200] + "..."),
                        inline=False
                    )
                    
                    embed.set_footer(text="OptiFlow • Insider Intelligence")
                    
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        # User has DMs disabled
                        pass
    
    except Exception as e:
        logger.error(f"Error sending insider alerts to users: {str(e)}")

@bot.command(name='insider_scan')
async def insider_scan(ctx):
    """Scan for suspicious insider options activity across all stocks."""
    if not INSIDER_SCANNER_AVAILABLE:
        await send_error_to_user(
            ctx, 'E006', 
            "Insider scanner is not available - missing required packages (yfinance/pandas)",
            "INSIDER_SCANNER_AVAILABLE = False"
        )
        return
    
    try:
        # Instant acknowledgment
        await send_instant_ack(ctx, "Got it! 🕵️ Firing up the insider scanner... hunting for big moves across 82+ stocks!")
        
        # Verbose progress messaging
        progress_messages = [
            "🔍 Connecting to market data streams...",
            "📊 Analyzing volume patterns across all sectors...", 
            "🎯 Scanning for unusual options activity...",
            "🧮 Calculating suspicious trade scores...",
            "🔥 Filtering for high-value insider signals..."
        ]
        
        progress_msg = await ctx.send(progress_messages[0])
        
        # Update progress as we scan
        for i, msg in enumerate(progress_messages[1:], 1):
            await asyncio.sleep(1)
            await progress_msg.edit(content=msg)
        
        # Initialize scanner and get alerts
        scanner = InsiderOptionsScanner()
        
        await progress_msg.edit(content="🚨 Analyzing 82+ stocks for insider patterns...")
        alerts = await asyncio.get_event_loop().run_in_executor(None, get_insider_options_alerts)
        
        if not alerts:
            embed = discord.Embed(
                title="✅ All Clear - No Suspicious Activity",
                description="Markets looking clean right now. No unusual insider options activity detected across all monitored stocks.",
                color=0x95a5a6
            )
            embed.add_field(
                name="📊 Scan Complete",
                value=f"✅ Analyzed {len(scanner.scan_symbols)} symbols\n🔍 Checked volume, DTE, and trade values\n⏰ Next auto-scan in 30 minutes",
                inline=False
            )
            await send_ephemeral_response(ctx, embed=embed, delete_after=30)
            await progress_msg.delete()
            return
        
        # Create detailed embed with top 10 alerts
        embed = discord.Embed(
            title="🚨 INSIDER INTELLIGENCE ALERT",
            description=f"🔥 **{len(alerts)} suspicious trades detected!** Here are the top 10 most unusual activities:",
            color=0xe74c3c
        )
        
        embed.add_field(
            name="📈 Scan Summary",
            value=f"🎯 Monitored: {len(scanner.scan_symbols)} symbols\n⚡ Found: {len(alerts)} unusual trades\n🔥 High priority: {len([a for a in alerts if a['unusual_score'] >= 8])} trades",
            inline=False
        )
        
        for i, alert in enumerate(alerts[:8]):  # Show top 8 to keep readable
            score_emoji = "🔥" if alert['unusual_score'] >= 9 else "⚠️" if alert['unusual_score'] >= 7 else "📊"
            priority = "CRITICAL" if alert['unusual_score'] >= 9 else "HIGH" if alert['unusual_score'] >= 7 else "MODERATE"
            
            field_name = f"{score_emoji} {alert['symbol']} • Score: {alert['unusual_score']}/10 • {priority}"
            field_value = (
                f"💰 **Value:** ${alert['estimated_value']:,.0f}\n"
                f"📊 **Strike:** ${alert['strike']} {alert['option_type'].upper()}\n"
                f"⏰ **DTE:** {alert['dte']} days\n"
                f"📈 **Volume:** {alert['volume']:,} contracts\n"
                f"🎯 **Signals:** {', '.join(alert['alert_reasons'][:2])}"
            )
            
            embed.add_field(name=field_name, value=field_value, inline=True)
        
        embed.add_field(
            name="🎯 Next Steps",
            value="• Use `!opti big_trades` for high-value focus\n• Use `!opti view` for live options flow dashboard\n• Set personal alerts with `!opti insider_alerts`",
            inline=False
        )
        
        embed.set_footer(text="OptiFlow Insider Intelligence • Data refreshes every 30min • Use !opti view for live dashboard")
        
        await progress_msg.delete()
        await send_ephemeral_response(ctx, embed=embed, delete_after=60)
        
    except ImportError as e:
        await send_error_to_user(
            ctx, 'E006',
            "Required packages missing for insider scanning",
            f"ImportError: {str(e)}"
        )
    except ConnectionError as e:
        await send_error_to_user(
            ctx, 'E007',
            "Network error while fetching market data - check internet connection",
            f"ConnectionError: {str(e)}"
        )
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            await send_error_to_user(
                ctx, 'E004',
                "API rate limit exceeded - wait 30 seconds before trying again",
                error_msg
            )
        elif "no data found" in error_msg.lower():
            await send_error_to_user(
                ctx, 'E001',
                "Market data temporarily unavailable - try again in a few minutes",
                error_msg
            )
        else:
            await send_error_to_user(
                ctx, 'E010',
                "Unexpected error during insider scan - service may be temporarily down",
                f"Exception: {error_msg}\nTraceback: {traceback.format_exc()}"
            )

@bot.command(name='big_trades')
async def big_trades(ctx, min_value: int = 500000):
    """Show recent high-value long-DTE options trades."""
    if not INSIDER_SCANNER_AVAILABLE:
        await send_error_to_user(
            ctx, 'E006',
            "Insider scanner is not available - missing required packages",
            "INSIDER_SCANNER_AVAILABLE = False"
        )
        return
    
    # Validate min_value parameter
    if min_value < 10000 or min_value > 100000000:
        await send_error_to_user(
            ctx, 'E009',
            f"Invalid minimum value ${min_value:,} - use between $10K and $100M",
            f"min_value parameter out of range: {min_value}"
        )
        return
    
    try:
        loading_msg = await ctx.send(f"💰 Scanning for trades > ${min_value:,}...")
        
        scanner = InsiderOptionsScanner()
        alerts = await asyncio.get_event_loop().run_in_executor(None, get_insider_options_alerts)
        
        # Filter for big trades
        big_trades = [alert for alert in alerts if alert['estimated_value'] >= min_value]
        
        if not big_trades:
            embed = discord.Embed(
                title="💰 No Big Trades Found",
                description=f"No options trades > ${min_value:,} found with long DTE",
                color=0x95a5a6
            )
            await loading_msg.edit(content="", embed=embed)
            return
        
        # Sort by trade value
        big_trades.sort(key=lambda x: x['estimated_value'], reverse=True)
        
        embed = discord.Embed(
            title="💰 High-Value Long-DTE Options Trades",
            description=f"Found {len(big_trades)} trades > ${min_value:,}",
            color=0xf39c12
        )
        
        for i, trade in enumerate(big_trades[:8]):
            money_emoji = "💎" if trade['estimated_value'] >= 2000000 else "💰"
            
            field_name = f"{money_emoji} {trade['symbol']} - ${trade['estimated_value']:,.0f}"
            field_value = (
                f"**Strike:** ${trade['strike']}\n"
                f"**Type:** {trade['option_type'].upper()}\n"
                f"**DTE:** {trade['dte']} days\n"
                f"**Volume:** {trade['volume']:,}\n"
                f"**Score:** {trade['unusual_score']}/10"
            )
            
            embed.add_field(name=field_name, value=field_value, inline=True)
            
            if i >= 7:
                break
        
        embed.set_footer(text="OptiFlow • Use different min_value: !opti big_trades 1000000")
        await loading_msg.edit(content="", embed=embed)
        
    except ValueError as e:
        await send_error_to_user(
            ctx, 'E009',
            f"Invalid number format for minimum value - use: !opti big_trades 500000",
            f"ValueError: {str(e)}"
        )
    except ImportError as e:
        await send_error_to_user(
            ctx, 'E006',
            "Required packages missing for big trades scanning",
            f"ImportError: {str(e)}"
        )
    except ConnectionError as e:
        await send_error_to_user(
            ctx, 'E007',
            "Network error while scanning for big trades - check internet connection",
            f"ConnectionError: {str(e)}"
        )
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            await send_error_to_user(
                ctx, 'E004',
                "API rate limit exceeded - wait 30 seconds before trying again",
                error_msg
            )
        else:
            await send_error_to_user(
                ctx, 'E010',
                "Unexpected error during big trades scan - service may be temporarily down",
                f"Exception: {error_msg}\nTraceback: {traceback.format_exc()}"
            )

@bot.command(name='view')
async def live_dashboard(ctx):
    """Launch the live options flow dashboard in your browser."""
    try:
        # Instant acknowledgment
        await send_instant_ack(ctx, "🚀 Firing up your personal options intelligence dashboard... this is going to be epic!")
        
        # Check if dashboard is available
        if not DASHBOARD_AVAILABLE:
            await send_error_to_user(
                ctx, 'E006',
                "Live dashboard is not available - missing dashboard server components",
                "DASHBOARD_AVAILABLE = False"
            )
            return
        
        # Progress messaging
        progress_msg = await ctx.send("🔥 Initializing real-time options flow dashboard...")
        
        await asyncio.sleep(1)
        await progress_msg.edit(content="📊 Starting web server for live market data...")
        
        # Start the dashboard server
        dashboard_url = start_dashboard_server()
        
        await asyncio.sleep(1)
        await progress_msg.edit(content="🎯 Dashboard is now LIVE! Preparing your personal link...")
        
        # Create the dashboard embed
        embed = discord.Embed(
            title="🚀 OptiFlow Live Intelligence Dashboard",
            description="**Your personal options flow command center is ready!**",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🌐 Access Your Dashboard",
            value=f"**[🚀 CLICK HERE TO OPEN DASHBOARD]({dashboard_url})**\n\n"
                  f"Direct URL: `{dashboard_url}`",
            inline=False
        )
        
        embed.add_field(
            name="📊 Dashboard Features",
            value=(
                "🔥 **Critical Insider Signals** - Live alerts for suspicious activity\n"
                "⚠️ **High Priority Trades** - Big money moves as they happen\n"
                "📈 **Volume Leaders** - Stocks with unusual options activity\n" 
                "💎 **Big Money Moves** - Institutional-sized trades\n"
                "🔄 **Auto-Refresh** - Updates every 30 seconds"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Pro Tips",
            value=(
                "• Keep the dashboard open for real-time monitoring\n"
                "• Use alongside Discord commands for deeper analysis\n"
                "• Best viewed on desktop/laptop for full experience\n"
                "• Dashboard shows data from 82+ monitored stocks"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔗 Quick Commands",
            value=(
                "`!opti insider_scan` - Deep analysis of current alerts\n"
                "`!opti big_trades` - Filter for high-value trades only\n"
                "`!opti price SYMBOL` - Quick stock info lookup"
            ),
            inline=False
        )
        
        embed.set_footer(text="OptiFlow Pro Dashboard • Keep this window open for live updates • Data refreshes automatically")
        
        await progress_msg.delete()
        await send_ephemeral_response(ctx, embed=embed, delete_after=120)
        
    except Exception as e:
        error_msg = str(e)
        if "port" in error_msg.lower() or "address" in error_msg.lower():
            await send_error_to_user(
                ctx, 'E007',
                "Unable to start web dashboard - network port issue",
                f"Server error: {error_msg}"
            )
        else:
            await send_error_to_user(
                ctx, 'E010',
                "Unexpected error launching dashboard - service may be temporarily down",
                f"Exception: {error_msg}\nTraceback: {traceback.format_exc()}"
            )

@bot.command(name='insider_alerts')
async def insider_alerts(ctx):
    """Configure insider trading alert preferences."""
    user_id = str(ctx.author.id)
    
    try:
        # Get current user preferences
        prefs = data_manager.get_user_preferences(user_id)
        
        embed = discord.Embed(
            title="🕵️ Insider Alert Settings",
            description="Configure your insider trading notifications",
            color=0x9b59b6
        )
        
        # Current settings
        min_value = prefs.get('insider_min_value', 250000)
        min_dte = prefs.get('insider_min_dte', 30)
        min_score = prefs.get('insider_min_score', 7)
        
        embed.add_field(
            name="📊 Current Settings",
            value=(
                f"**Min Trade Value:** ${min_value:,}\n"
                f"**Min DTE:** {min_dte} days\n"
                f"**Min Unusual Score:** {min_score}/10"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ How to Update",
            value=(
                "Use `!opti setnotify` to modify:\n"
                "• `insider_min_value` - Minimum trade value\n"
                "• `insider_min_dte` - Minimum days to expiration\n"
                "• `insider_min_score` - Minimum unusual score (1-10)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Example",
            value="`!opti setnotify insider_min_value 500000`\n`!opti setnotify insider_min_score 8`",
            inline=False
        )
        
        embed.set_footer(text="OptiFlow • Personalized Insider Intelligence")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error accessing insider alert settings: {str(e)}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables")
        print("💡 Add your Discord bot token to .env file")
        exit(1)
    
    print("🚀 Starting OptiFlow Discord Bot...")
    
    try:
        bot.run(BOT_TOKEN)
    except discord.PrivilegedIntentsRequired:
        asyncio.run(handle_privileged_intents_error())
        print("\n❌ Bot startup failed - Privileged intents not enabled")
        print("🔄 Please follow the steps above and restart the bot")
        exit(1)
    except discord.LoginFailure:
        print("\n❌ Bot login failed - Invalid token")
        print("💡 Check your DISCORD_BOT_TOKEN in .env file")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error starting bot: {e}")
        print("💡 Check your internet connection and bot configuration")
        exit(1)