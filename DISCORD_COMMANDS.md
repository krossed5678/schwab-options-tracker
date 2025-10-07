# 🤖 OptiFlow Discord Bot - Complete Command Reference

Your personal trading assistant with customizable notifications and comprehensive market analysis.

## 📋 **All Available Commands**

### 📊 **Market Data & Analysis**

| Command | Description | Example | Output |
|---------|-------------|---------|--------|
| `!opti price AAPL` | Current stock price & basic info | Real-time price, change %, volume | Live market data |
| `!opti insider TSLA` | Insider options activity analysis | High-volume calls/puts, sentiment | Options flow analysis |
| `!opti volume SPY` | Volume analysis vs historical | Current vs average, ratio, trend | Volume spike detection |
| `!opti summary` | Major market indices overview | SPY, QQQ, IWM, VIX performance | Market health check |
| `!opti top large` | Top movers by market cap | Biggest % moves (large/mid/small) | Daily winners/losers |
| `!opti flow NVDA` | Options flow analysis | Large trades, bullish/bearish flow | Institutional activity |
| `!opti news MSFT` | Latest market-moving news | Recent headlines and updates | News sentiment |

### 🚀 **IPO Tracking & Calendar**

| Command | Description | What You Get |
|---------|-------------|--------------|
| `!opti ipos` | Upcoming IPO calendar | Company, date, price range, sector |
| `!opti recent` | Recent IPO performance | Post-IPO returns, current vs IPO price |
| `!opti earnings` | Upcoming earnings calendar | Major earnings dates and estimates |

### 🔔 **Personal Alerts & Watchlist**

| Command | Description | Functionality |
|---------|-------------|---------------|
| `!opti alerts` | Recent OptiFlow alerts | Last 10 alerts from main app |
| `!opti watch NVDA` | Add to personal watchlist | Get alerts for this symbol |
| `!opti unwatch AAPL` | Remove from watchlist | Stop alerts for this symbol |
| `!opti watchlist` | View your watchlist | All symbols you're monitoring |

### ⚙️ **Personalized Notification Settings**

| Command | Description | Customization Options |
|---------|-------------|----------------------|
| `!opti notify` | View your current preferences | See all your alert settings |
| `!opti setnotify` | Configure alert preferences | Detailed customization menu |
| `!opti setnotify volume on/off` | Toggle volume spike alerts | Enable/disable volume notifications |
| `!opti setnotify volume_threshold 3.5` | Set volume spike threshold | Minimum 3.5x average volume |
| `!opti setnotify price on/off` | Toggle price change alerts | Enable/disable price notifications |
| `!opti setnotify price_threshold 5.0` | Set price change threshold | Minimum 5% price move |
| `!opti setnotify ipos on/off` | Toggle IPO notifications | Enable/disable IPO alerts |
| `!opti setnotify sectors Tech,Healthcare` | Set sector interests | Only get alerts for these sectors |
| `!opti setnotify marketcap large` | Filter by market cap | large/mid/small/all cap stocks |

### ❓ **Help & Information**

| Command | Description |
|---------|-------------|
| `!opti help` | Show all available commands |

---

## 🔔 **Personalized Notification System**

### **How It Works**
Each user gets **personalized notifications** based on their individual preferences:

1. **Personal Watchlists** - Get alerts only for stocks you care about
2. **Custom Thresholds** - Set your own volume/price change minimums  
3. **Sector Filtering** - Focus on specific industry sectors
4. **Market Cap Filtering** - Large cap, mid cap, small cap, or all
5. **Alert Type Selection** - Choose which types of alerts you want

### **Notification Delivery**
- **📢 Public Channel** - All alerts posted to main alerts channel
- **📱 Personal DMs** - Custom alerts sent directly to you based on preferences
- **🎯 Smart Filtering** - Only get notifications that match your settings

### **Example Personalization Setup**

```discord
# Configure your personal preferences
!opti setnotify volume on                    # Enable volume alerts
!opti setnotify volume_threshold 4.0         # Only 4x+ volume spikes
!opti setnotify price on                     # Enable price alerts  
!opti setnotify price_threshold 7.5          # Only 7.5%+ price moves
!opti setnotify sectors Technology,AI        # Focus on tech sectors
!opti setnotify marketcap large              # Only large cap stocks

# Add personal watchlist
!opti watch AAPL
!opti watch TSLA  
!opti watch NVDA

# View your settings
!opti notify
```

**Result:** You'll only get DM alerts for:
- AAPL, TSLA, NVDA (your watchlist) with ANY activity
- Technology/AI sector stocks with 4x+ volume OR 7.5%+ price moves
- Large cap stocks only

---

## 📊 **Real-World Usage Examples**

### **🌅 Morning Routine**
```discord
!opti summary              # Check overnight market moves
!opti ipos                 # Any IPOs today?
!opti earnings             # Earnings announcements
!opti top large            # What's moving pre-market?
```

### **📈 During Trading Hours**
```discord
!opti price TSLA          # Quick price check
!opti insider AAPL        # Any unusual options activity?
!opti volume NVDA         # Volume spike confirmation
!opti flow SPY            # Market-wide options flow
```

### **🎯 Alert Investigation**
```discord
# You get a DM: "TSLA volume spike detected"
!opti price TSLA          # Check current price
!opti insider TSLA        # Options activity analysis
!opti news TSLA           # Any breaking news?
!opti flow TSLA           # Institutional money flow
```

### **⚙️ Preference Tuning**
```discord
# Getting too many alerts?
!opti setnotify volume_threshold 5.0    # Raise threshold

# Missing important moves?  
!opti setnotify price_threshold 3.0     # Lower threshold

# Want IPO focus?
!opti watch GREN           # Add upcoming IPO to watchlist
!opti setnotify ipos on    # Enable IPO notifications
```

---

## 🔧 **Advanced Features**

### **Multi-User Support**
- **Individual Preferences** - Each Discord user has separate settings
- **Team Watchlists** - Share insights while keeping personal alerts
- **Role-Based Alerts** - Different notification levels for different users

### **Smart Filtering**
- **Minimum Thresholds** - Avoid notification spam
- **Sector Focus** - Only get alerts for industries you trade
- **Market Cap Filtering** - Match your trading style (large cap vs penny stocks)
- **Watchlist Priority** - Always get alerts for your personal picks

### **Real-Time Integration**
- **Live OptiFlow Sync** - Connects with main trading app
- **Market Hours Awareness** - Different alert behavior during/after hours
- **Background Monitoring** - Continuous scanning every 5 minutes

---

## 📱 **Mobile Experience**

### **Discord Mobile Notifications**
1. **Enable Discord Push** on your phone
2. **Set Custom Sounds** for OptiFlow alerts channel
3. **Use Do Not Disturb** to only get DMs during market hours
4. **Pin Important Alerts** for quick reference

### **Quick Mobile Commands**
Perfect for phone trading:
```discord
!opti price AAPL     # Fast price check
!opti alerts         # Recent activity  
!opti summary        # Market health
!opti watchlist      # Your positions
```

---

## 🎯 **Best Practices**

### **Smart Threshold Setting**
- **Start Conservative** - High thresholds (5x volume, 10% price)
- **Tune Gradually** - Lower thresholds as you get comfortable
- **Market Conditions** - Higher thresholds in volatile markets

### **Effective Watchlist Management**
- **Focus on Liquids** - Stick to high-volume, optionable stocks
- **Sector Diversification** - Mix of tech, finance, healthcare, etc.
- **Position Size** - Only watch stocks you're actually trading

### **Team Coordination**
- **Shared Analysis** - Use public channel for group discussion
- **Personal Research** - Use DMs for individual alerts
- **Alert Validation** - Cross-check bot alerts with manual analysis

---

## 🚀 **Getting Started Checklist**

### **Day 1: Basic Setup**
- [ ] Set up Discord bot token
- [ ] Test basic commands (`!opti help`, `!opti summary`)
- [ ] Add 3-5 stocks to watchlist

### **Day 2: Personalization**
- [ ] Configure notification preferences
- [ ] Set volume/price thresholds
- [ ] Choose sector focus

### **Day 3: Advanced Features**
- [ ] Test insider options analysis
- [ ] Use IPO tracking
- [ ] Explore options flow analysis

### **Week 1: Optimization**
- [ ] Tune alert thresholds based on experience
- [ ] Expand watchlist strategically
- [ ] Develop daily routine with bot commands

---

**Your Discord server is now a professional trading command center!** 🚀📊

Use `!opti help` to get started, then `!opti setnotify` to customize your experience.