# 📱 Mobile Notifications Guide for OptiFlow

## 🚀 **Quick Setup Options**

### **Option 1: Browser Push Notifications (Easiest)**
✅ **Works immediately** - No additional setup required!

1. **Enable in your browser:**
   - Open the app in Chrome/Edge on your phone
   - When prompted "Allow notifications?" → Click **Allow**
   - Notifications will appear even when browser is closed

2. **Test it:**
   - Go to "🚨 Alerts" tab
   - Click "Send Test Alert"
   - You should see notification on your phone!

### **Option 2: Email Notifications (Most Reliable)**
📧 **Get alerts via email** - Works on any device!

1. **Setup email in the app:**
   - Go to "🚨 Alerts" tab → "⚙️ Settings"
   - Check "Enable Email Notifications"
   - Enter your email address

2. **Configure email server** (see detailed setup below)

### **Option 3: Telegram Bot (Recommended)**
🤖 **Instant messaging notifications** - Very reliable!

1. **Create Telegram bot** (see setup below)
2. **Add bot token to .env file**
3. **Get instant alerts on Telegram**

### **Option 4: Discord Webhooks**
💬 **Send alerts to Discord channel**

1. **Create Discord webhook** (see setup below)
2. **Get notifications in your Discord server**

---

## 🔧 **Detailed Setup Instructions**

### **📧 Email Notifications Setup**

#### Step 1: Add to `.env` file:
```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL=your.phone.number@sms.gateway.com  # For SMS via email
```

#### Step 2: Gmail App Password:
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Use this password in EMAIL_PASSWORD

#### Step 3: SMS via Email (Bonus!):
Send texts to your phone via email:
- **Verizon**: yourphonenumber@vtext.com
- **AT&T**: yourphonenumber@txt.att.net
- **T-Mobile**: yourphonenumber@tmomail.net
- **Sprint**: yourphonenumber@messaging.sprintpcs.com

### **🤖 Telegram Bot Setup**

#### Step 1: Create Bot:
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Choose bot name and username
4. Copy the bot token

#### Step 2: Get Chat ID:
1. Start your bot
2. Send it a message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

#### Step 3: Add to `.env`:
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### **💬 Discord Webhook Setup**

#### Step 1: Create Webhook:
1. Go to your Discord server
2. Right-click channel → Edit Channel → Integrations → Webhooks
3. Create New Webhook
4. Copy webhook URL

#### Step 2: Add to `.env`:
```env
# Discord Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url

# Discord @everyone Settings (Optional)
DISCORD_TAG_EVERYONE=true
DISCORD_TAG_EVERYONE_TYPES=unusual_volume,price_change,ipo_update,options_flow
```

#### 🏷️ **@everyone Tagging**
OptiFlow can automatically tag `@everyone` in Discord for important alerts:

**Alert Types that trigger @everyone:**
- 📊 `unusual_volume` - High volume spikes
- 📈 `price_change` - Significant price moves  
- 🚀 `ipo_update` - IPO launches and updates
- 💰 `options_flow` - Large options trades
- ⚡ `iv_spike` - Implied volatility spikes

**Customize @everyone behavior:**
- Set `DISCORD_TAG_EVERYONE=false` to disable completely
- Modify `DISCORD_TAG_EVERYONE_TYPES` to choose which alerts tag everyone
- Example: `DISCORD_TAG_EVERYONE_TYPES=unusual_volume,ipo_update` (only these will tag @everyone)

---

## 📋 **Complete .env Configuration Example**

```env
# Schwab API (Required)
SCHWAB_APP_KEY=your_schwab_app_key_here
SCHWAB_APP_SECRET=your_schwab_app_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1

# Mobile Notifications (Choose what you want)
# Email/SMS
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
ALERT_EMAIL=yourphone@vtext.com

# Telegram  
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIjKlMnOpQrStUvWxYz
TELEGRAM_CHAT_ID=123456789

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc
DISCORD_TAG_EVERYONE=true
DISCORD_TAG_EVERYONE_TYPES=unusual_volume,price_change,ipo_update,options_flow

# Notification Settings
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_TELEGRAM_NOTIFICATIONS=true
ENABLE_DISCORD_NOTIFICATIONS=false
```

---

## 📱 **Mobile Browser Setup**

### **Android (Chrome):**
1. Open app in Chrome
2. Menu → Add to Home Screen
3. Enable notifications when prompted
4. App works like native app!

### **iPhone (Safari):**
1. Open app in Safari  
2. Share → Add to Home Screen
3. Enable notifications
4. Acts like iOS app!

---

## 🧪 **Test Your Setup**

After configuration:
1. **Restart the app**: `streamlit run main.py`
2. **Go to Alerts tab** → Settings
3. **Click "Send Test Alert"**
4. **Check all your devices** for notifications!

---

## 🎯 **Best Practices**

### **For Day Trading:**
- ✅ **Telegram** (instant, reliable)
- ✅ **Browser push** (when app is open)
- ✅ **SMS via email** (backup)

### **For Swing Trading:**
- ✅ **Email** (detailed alerts)
- ✅ **Discord** (community sharing)
- ✅ **Browser push** (when available)

### **For Portfolio Monitoring:**
- ✅ **Email daily summaries**
- ✅ **Telegram for urgent alerts**
- ✅ **Browser push for quick checks**

---

## 🚨 **Alert Types You Can Get**

Once configured, you'll receive mobile notifications for:

- 📈 **Unusual Options Volume** (e.g., AAPL calls volume spike)
- 💰 **Large Options Trades** (e.g., $1M+ sweep detected)
- 🚀 **IPO Updates** (e.g., "New IPO filing: TechCorp")
- 📊 **Price Movements** (e.g., "TSLA up 5%+ today")
- ⚡ **IV Spikes** (e.g., "NVDA IV jumped to 60%")
- 💼 **Portfolio Alerts** (e.g., "Position up 20%")

---

## 💡 **Pro Tips**

1. **Use Multiple Methods**: Telegram for urgent + Email for detailed
2. **Set Smart Thresholds**: Avoid notification spam
3. **Test Regularly**: Ensure notifications are working
4. **Mobile Bookmarks**: Save app to phone home screen
5. **Weekend Prep**: Set alerts for Monday market open

**Ready to never miss a trading opportunity again!** 📱🚀