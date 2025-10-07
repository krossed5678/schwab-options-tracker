# 🤖 OptiFlow Discord Bot Setup Guide

Transform your Discord server into a real-time trading command center with OptiFlow's Discord bot integration!

## 🚀 Quick Setup

### Step 1: Create Discord Bot

1. **Go to Discord Developer Portal**
   - Visit: https://discord.com/developers/applications
   - Click "New Application" → Name it "OptiFlow"

2. **Create Bot**
   - Go to "Bot" section → Click "Add Bot"
   - Copy the **Bot Token** (keep this secret!)
   - Enable these permissions:
     - ✅ Send Messages
     - ✅ Read Message History  
     - ✅ Use Slash Commands
     - ✅ Embed Links

3. **Invite Bot to Server**
   - Go to "OAuth2" → "URL Generator"
   - Select "bot" scope and permissions above
   - Copy generated URL and open in browser
   - Select your Discord server and authorize

### Step 2: Configure OptiFlow

1. **Update .env file:**
```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_discord_server_id_here  
DISCORD_ALERTS_CHANNEL_ID=your_alerts_channel_id_here
```

2. **Get Server ID:**
   - Right-click your Discord server → "Copy Server ID"

3. **Get Channel ID:**
   - Right-click your alerts channel → "Copy Channel ID"

### Step 3: Install Dependencies & Start

```bash
# Install Discord.py
pip install discord.py>=2.3.0

# Start the bot
start_discord_bot.bat
```

## 🎯 Bot Commands

### 📊 **Market Data Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `!opti price AAPL` | Get current stock price and info | Real-time price, change %, volume |
| `!opti insider TSLA` | Insider options activity analysis | High volume calls/puts, sentiment |
| `!opti summary` | Major market indices overview | SPY, QQQ, IWM, VIX performance |

### 🚀 **IPO Tracking Commands**

| Command | Description | What You Get |
|---------|-------------|--------------|
| `!opti ipos` | Upcoming IPOs calendar | Company, date, price range, sector |
| `!opti recent` | Recent IPO performance | Post-IPO returns, current vs IPO price |

### 🔔 **Alerts & Watchlist**

| Command | Description | Example |
|---------|-------------|---------|
| `!opti alerts` | Recent OptiFlow alerts | Last 5 triggered alerts from main app |
| `!opti watch NVDA` | Add stock to watchlist | Bot monitors for alerts |
| `!opti watchlist` | View current watchlist | All monitored symbols |

### ❓ **Help & Info**

| Command | Description |
|---------|-------------|
| `!opti help` | Show all available commands |

## 🔄 **Automatic Features**

### **Real-time Alert Forwarding**
- 🚨 **New alerts** from OptiFlow main app automatically posted to Discord
- ⏰ **Market open/close** notifications 
- 📊 **High-volume options** activity alerts

### **Background Monitoring**
- 🔍 **Checks for new alerts** every 5 minutes
- 📈 **Market status** updates every hour
- 🤖 **Auto-sync** with main OptiFlow app data

## 📱 **Discord Integration Examples**

### **Insider Options Alert**
```
🕵️ Insider Options Activity - AAPL
Expiry: 2025-10-20

📞 Calls Activity          📉 Puts Activity
High Vol: 15               High Vol: 8  
Total Vol: 125,430         Total Vol: 89,220

⚖️ Call/Put Ratio: 1.41   💭 Sentiment: 📈 Bullish
```

### **Live Alert Notification**
```
🚨 NEW OPTIFLOW ALERT
TSLA - unusual_volume

📝 Details: Volume spike detected - 5.2x average volume
⏰ Time: 10/07 14:23:15
```

### **IPO Update**
```
🚀 Upcoming IPOs

🏢 TechFlow Inc (TFLW)
📅 Date: 2025-10-15
💰 Price: $18-22
📊 Shares: 15M
🏷️ Sector: Technology
```

## ⚙️ **Advanced Configuration**

### **Custom Alert Channels**
Set different channels for different alert types:

```env
# Multiple channel setup
DISCORD_ALERTS_CHANNEL_ID=123456789  # General alerts
DISCORD_IPO_CHANNEL_ID=987654321     # IPO updates  
DISCORD_OPTIONS_CHANNEL_ID=456789123 # Options alerts
```

### **Alert Filtering**
Configure which alerts get sent to Discord:

```python
# In discord_bot.py - customize alert_monitor function
ALERT_FILTERS = {
    'min_volume_ratio': 3.0,    # Only 3x+ volume spikes
    'min_price_change': 5.0,    # Only 5%+ price moves
    'symbols_only': ['AAPL', 'TSLA', 'NVDA']  # Filter by symbols
}
```

### **Market Hours Setup**
Customize market notifications:

```python
# Market open notification - 9:30 AM EST
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30

# Market close notification - 4:00 PM EST  
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0
```

## 🔧 **Troubleshooting**

### **Common Issues**

**Bot won't start:**
```bash
# Check bot token
echo %DISCORD_BOT_TOKEN%

# Reinstall discord.py
pip uninstall discord.py
pip install discord.py>=2.3.0
```

**No commands working:**
```bash
# Check bot permissions in Discord server:
- Read Messages ✅
- Send Messages ✅  
- Use Slash Commands ✅
- Embed Links ✅
```

**Alerts not forwarding:**
```bash
# Check channel ID is correct
# Make sure main OptiFlow app is running
# Verify data/alerts.json exists
```

**"Application did not respond" error:**
```bash
# Bot may be offline - restart bot
start_discord_bot.bat

# Check bot status in Discord server member list
```

### **Debug Mode**
Enable debug logging:

```python
# In discord_bot.py
logging.basicConfig(level=logging.DEBUG)
```

## 💡 **Pro Tips**

### **Server Organization**
Create dedicated channels:
- `#optiflow-alerts` - Live trading alerts
- `#ipo-updates` - IPO tracking and performance
- `#market-data` - Price checks and analysis
- `#bot-commands` - Command testing area

### **Mobile Setup**
- 📱 **Enable Discord notifications** on your phone
- 🔔 **Set custom notification sounds** for OptiFlow channels  
- 📍 **Pin important alert messages** for quick reference

### **Team Trading**
- 👥 **Share watchlists** with trading team
- 💬 **Discuss alerts** in real-time
- 📊 **Collaborate on analysis** using bot commands

## 🚀 **Getting Started Workflow**

1. **Setup Bot** (5 minutes)
   ```bash
   # Create bot on Discord Developer Portal
   # Add token to .env file
   # Invite bot to server
   ```

2. **Test Commands** (2 minutes)
   ```bash
   !opti help
   !opti price AAPL  
   !opti summary
   ```

3. **Configure Alerts** (3 minutes)
   ```bash
   # Set DISCORD_ALERTS_CHANNEL_ID in .env
   # Start both OptiFlow app and Discord bot
   # Test with !opti alerts
   ```

4. **Go Live** (start trading!)
   ```bash
   # Create alerts in main OptiFlow app
   # They'll automatically appear in Discord
   # Use bot commands for quick market checks
   ```

## 📈 **Example Daily Workflow**

### **Market Open (9:30 AM)**
```bash
!opti summary              # Check overall market
!opti watchlist           # Review your positions  
!opti ipos                # Check today's IPO activity
```

### **During Trading Hours**
```bash
!opti price TSLA          # Quick price checks
!opti insider NVDA        # Check unusual options activity
# Automatic alerts stream in from main app
```

### **Market Close (4:00 PM)**
```bash
!opti alerts              # Review day's alerts
!opti recent              # Check IPO performance
```

---

## 🎯 **Ready to Launch?**

1. **Create Discord bot** using Developer Portal
2. **Add credentials** to `.env` file  
3. **Start bot**: `start_discord_bot.bat`
4. **Test commands**: `!opti help`
5. **Start trading** with real-time Discord alerts!

**Your Discord server is now a trading command center!** 🚀📊