# 🚀 OptiFlow Discord Bot Setup Guide

## Overview

The OptiFlow Discord Bot provides real-time insider options activity monitoring directly in your Discord server. Get personalized alerts for high-value, long-DTE options trades that may indicate insider activity.

## 🎯 Key Features

### 🕵️ Insider Intelligence
- **Live Scanning**: Monitors 82+ liquid stocks for suspicious options activity
- **Smart Scoring**: Uses proprietary algorithm to score trades 1-10 based on unusual activity
- **Personalized Alerts**: Customizable thresholds for trade value, DTE, and unusual score
- **Real-time Notifications**: Background monitoring with instant Discord DMs and channel alerts

### 📊 Trading Commands
- `!opti insider_scan` - Full market scan for suspicious activity
- `!opti big_trades` - High-value long-DTE trades (customizable minimum)
- `!opti insider_alerts` - Configure personal insider notification preferences
- `!opti price SYMBOL` - Stock price and basic info
- `!opti ipos` - Upcoming IPO calendar
- Plus 15+ other trading intelligence commands

### 🔔 Personalized Notifications
- Individual user preferences for insider alerts
- Customizable minimum trade value (default: $250K)
- Customizable minimum DTE (default: 30 days)
- Customizable unusual score threshold (default: 7/10)
- Background monitoring every 30 minutes

## 🛠️ Setup Instructions

### Step 1: Create Discord Bot

1. **Go to Discord Developer Portal**: https://discord.com/developers/applications/
2. **Create New Application**: Click "New Application" and name it "OptiFlow"
3. **Create Bot**: Go to "Bot" section → "Add Bot"
4. **Get Bot Token**: Copy the bot token (keep this secret!)
5. **Enable Intents**: 
   - ✅ Message Content Intent
   - ✅ Server Members Intent (optional)

### Step 2: Invite Bot to Server

1. **Go to OAuth2 → URL Generator**
2. **Select Scopes**: ✅ `bot`
3. **Select Permissions**:
   - ✅ Send Messages
   - ✅ Send Messages in Threads
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Use Slash Commands
4. **Copy & Use Invite URL**: Paste in browser and add to your server

### Step 3: Configure Environment Variables

Add these to your `.env` file:

```bash
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
DISCORD_ALERTS_CHANNEL_ID=your_alerts_channel_id_here
```

#### How to Get IDs:
- **Server ID**: Right-click your server → "Copy Server ID"
- **Channel ID**: Right-click your alerts channel → "Copy Channel ID"

*Note: You need to enable "Developer Mode" in Discord Settings → Advanced → Developer Mode*

### Step 4: Run the Bot

```bash
# Make sure you're in the project directory
cd schwab-options-tracker

# Activate virtual environment (if using one)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install required packages (if not already installed)
pip install discord.py yfinance pandas python-dotenv

# Run the bot
python discord_bot.py
```

## 🎮 Usage Examples

### Basic Commands
```
!opti help                    # Show all commands
!opti insider_scan           # Scan for suspicious activity
!opti big_trades             # High-value trades (default $500K+)
!opti big_trades 1000000     # High-value trades $1M+
!opti price AAPL            # Get AAPL stock info
```

### Configure Personal Alerts
```
!opti insider_alerts         # View current settings
!opti setnotify insider_min_value 500000    # $500K minimum
!opti setnotify insider_min_dte 45          # 45+ days to expiration
!opti setnotify insider_min_score 8         # Score 8/10 or higher
!opti setnotify insider_alerts on           # Enable notifications
```

### Advanced Usage
```
!opti watch NVDA             # Add NVDA to watchlist
!opti ipos                   # Upcoming IPOs
!opti notify                 # View all notification settings
!opti sectors Technology     # Focus on tech sector
```

## 🚨 Real-Time Monitoring

Once configured, the bot will:

1. **Scan Every 30 Minutes**: Automatically monitor 82+ stocks for insider activity
2. **Score Trades**: Calculate unusual score (1-10) based on:
   - Volume vs Average Volume
   - Trade Value (volume × option price)
   - Moneyness (how close to strike price)
   - Volume vs Open Interest ratio
3. **Send Alerts**: 
   - High priority alerts (score 8+) to main channel
   - Personalized DMs based on user preferences
   - Background notifications without spam

## 📊 Insider Scoring Algorithm

**Score 9-10**: 🔥 Extremely suspicious (massive volume, deep ITM/OTM, huge value)
**Score 7-8**: ⚠️ Very unusual (high volume, significant value, long DTE)  
**Score 5-6**: 📊 Moderately unusual (above average activity)
**Score 1-4**: 📈 Normal activity

## 🔧 Troubleshooting

### Bot Not Responding
- Check bot token in `.env` file
- Verify bot has permissions in your server
- Make sure bot is online (green status)

### No Insider Alerts
- Check `DISCORD_ALERTS_CHANNEL_ID` is correct
- Verify yfinance and pandas are installed
- Market may be closed (alerts only during market hours)

### Permission Errors
- Bot needs "Send Messages" and "Embed Links" permissions
- Check channel-specific permissions

## 📱 Example Alert Output

```
🚨 High Priority Insider Activity
Detected 3 suspicious trades

🔥 AAPL - Score: 9/10
Strike: $150.00
Type: CALL
Value: $2,850,000
DTE: 45 days
```

## 🎯 Advanced Configuration

### Custom Symbols List
Modify `src/insider_scanner.py` to add/remove symbols from monitoring.

### Alert Frequency
Change monitoring interval in `discord_bot.py`:
```python
@tasks.loop(minutes=30)  # Change to desired frequency
async def insider_monitor():
```

### Notification Channels
Set up multiple alert channels for different types of notifications.

## 🔐 Security Notes

- **Never share your bot token** - treat it like a password
- Keep `.env` file private and don't commit to version control
- Use environment variables for all sensitive data
- Bot tokens can be regenerated if compromised

## 🆘 Support

For issues or questions:
1. Check this setup guide thoroughly
2. Verify all environment variables are set correctly  
3. Ensure all required packages are installed
4. Test with basic commands first (`!opti help`)

## 🎉 Ready to Trade!

Once set up, you'll have a powerful insider options intelligence system running 24/7 in your Discord server. The bot will help you spot potential insider activity before it becomes public news!

**Happy Trading! 🚀📈**