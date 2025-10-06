# Schwab OptiFlow - Setup Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Schwab API Credentials
1. Visit [Schwab Developer Portal](https://developer.schwab.com/)
2. Create developer account (free)
3. Create new application
4. Note your **App Key** and **App Secret**
5. Set redirect URI to: `https://127.0.0.1`

### Step 2: Setup Environment
```bash
# Clone repository
git clone <your-repo-url>
cd schwab-options-tracker

# Run setup script (Windows)
setup.bat

# Or manual setup:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Credentials
```bash
# Copy environment template
copy .env.template .env

# Edit .env file with your credentials:
# SCHWAB_APP_KEY=your_app_key_here
# SCHWAB_APP_SECRET=your_app_secret_here
```

### Step 4: Run Application
```bash
streamlit run main.py
```

### Step 5: Complete Authentication
1. Click "Get Authorization URL" in the app
2. Visit the URL and log into Schwab
3. Copy authorization code from redirect URL
4. Paste code in app and click "Complete Authentication"

## 🎯 What You Can Do Now

### Options Analysis
- **Any Stock**: AAPL, TSLA, NVDA, SPY, QQQ, etc.
- **Real-time Data**: Live quotes, Greeks, IV
- **Unusual Activity**: High volume/OI detection
- **Visualizations**: Volume, OI, volatility smile

### IPO Tracking  
- **Upcoming IPOs**: See what's coming to market
- **Recent Performance**: Track post-IPO stock performance
- **Sector Analysis**: Compare IPO performance by sector
- **Calendar View**: Complete IPO timeline

## 🔧 Troubleshooting

### Common Issues
1. **"No module named streamlit"**
   - Solution: `pip install streamlit`

2. **Authentication fails**
   - Check API credentials in .env file
   - Verify redirect URI matches Schwab app settings

3. **No data returned**
   - Verify symbol is correct and tradable
   - Check if options are available for that symbol

### Getting Help
- Check README.md for detailed instructions
- Run `python test_setup.py` to verify installation
- Check terminal output for specific error messages

## 🚀 Ready to Analyze!
Once setup is complete, you can analyze options for any stock and track IPO opportunities in real-time!