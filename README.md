# Schwab Options Viewer

A comprehensive Python-based dashboard for analyzing options markets in real-time using the Schwab Trader API. This tool provides traders and investors with powerful options analysis capabilities including real-time quotes, Greeks calculations, implied volatility analysis, and unusual activity detection.

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)

## 🚀 Features

### Core Functionality
- **Real-Time Option Chains**: Fetch live options data for any ticker symbol
- **Interactive Dashboard**: Built with Streamlit for intuitive filtering and visualization
- **Greeks Analysis**: Complete options Greeks (Delta, Gamma, Theta, Vega, Rho) calculations
- **Implied Volatility**: Real-time IV data and volatility smile visualization
- **Unusual Activity Detection**: Identify contracts with high volume relative to open interest
- **Multiple Visualizations**: Volume charts, open interest analysis, and volatility curves

### Advanced Features
- **OAuth2 Authentication**: Secure integration with Schwab Trader API
- **Token Management**: Automatic token refresh and persistent storage
- **Rate Limiting**: Built-in API rate limiting and retry logic
- **Data Export**: Export options data to CSV and JSON formats
- **Flexible Filtering**: Filter by expiration, strike range, contract type, and moneyness
- **Real-Time Quotes**: Live bid/ask spreads and last trade information

## 📋 Prerequisites

### Schwab Developer Account
1. **Create a Schwab Developer Account**
   - Visit [Schwab Developer Portal](https://developer.schwab.com/)
   - Sign up for a developer account
   - Create a new application

2. **Get API Credentials**
   - Note your `App Key` (Client ID)
   - Note your `App Secret` (Client Secret)
   - Set redirect URI to `https://127.0.0.1` (or your preferred localhost)

### System Requirements
- Python 3.9 or higher
- Windows, macOS, or Linux
- Internet connection for API access

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/schwab-options-tracker.git
cd schwab-options-tracker
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit `.env` file with your credentials:
```env
# Schwab API Configuration
SCHWAB_APP_KEY=your_schwab_app_key_here
SCHWAB_APP_SECRET=your_schwab_app_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1

# Optional: Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Dashboard Configuration
DEFAULT_TICKER=SPY
DEFAULT_EXPIRATION_DAYS=30
```

## 🚀 Usage

### Starting the Application
```bash
streamlit run main.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

### First-Time Authentication

1. **Launch the Application**: Start the Streamlit app
2. **Authentication Flow**: On first run, you'll see an authentication section
3. **Get Authorization URL**: Click "Get Authorization URL" 
4. **Authorize Application**: Visit the provided URL and log in to your Schwab account
5. **Get Authorization Code**: After authorization, copy the `code` parameter from the redirect URL
6. **Complete Setup**: Paste the authorization code and click "Complete Authentication"

The application will automatically handle token refresh for future sessions.

### Using the Dashboard

#### 1. **Basic Options Analysis**
- Enter a stock symbol (e.g., AAPL, SPY, TSLA)
- Select expiration timeframe
- Choose contract type (Calls, Puts, or All)
- Click "Fetch Options Data"

#### 2. **Viewing Results**
- **Summary Metrics**: Overview of total contracts, volume, open interest
- **Visualizations**: Interactive charts showing volume, OI, and implied volatility
- **Options Chain**: Complete filterable table of all contracts

#### 3. **Unusual Activity Detection**
- Set volume and open interest thresholds
- Configure volume/OI ratio threshold
- View contracts with unusual trading activity

#### 4. **Advanced Filtering**
- Filter by expiration date
- Filter by contract type (Calls/Puts)
- Filter by moneyness (ITM/OTM)
- Sort by various metrics

#### 5. **Data Export**
- Download complete options chain as CSV
- Export unusual activity data
- Save summary metrics as JSON

## 📊 Dashboard Sections

### 1. **Options Parameters** (Sidebar)
- Stock symbol input
- Expiration filtering
- Contract type selection
- Strike range configuration
- Advanced options (ITM/OTM filtering)

### 2. **Unusual Activity Settings** (Sidebar)
- Volume threshold
- Open interest threshold
- Volume/OI ratio threshold

### 3. **Summary Dashboard**
- Underlying stock price
- Total contracts and volume
- Put/Call ratios
- Average implied volatility

### 4. **Visualizations**
- Volume and Open Interest charts
- Implied Volatility Smile
- Interactive plotting with Plotly

### 5. **Data Tables**
- Unusual activity contracts
- Complete options chain
- Sortable and filterable columns

## ⚙️ Configuration

### API Configuration (`config/config.json`)
```json
{
  "api": {
    "base_url": "https://api.schwabapi.com",
    "timeout": 30,
    "max_retries": 3
  },
  "dashboard": {
    "page_title": "Schwab Options Viewer",
    "page_icon": "📈",
    "layout": "wide"
  },
  "options": {
    "default_days_to_expiration": [7, 14, 30, 60, 90],
    "volume_threshold": 100,
    "open_interest_threshold": 50,
    "unusual_activity_ratio": 2.0
  }
}
```

### Environment Variables
- `SCHWAB_APP_KEY`: Your Schwab API application key
- `SCHWAB_APP_SECRET`: Your Schwab API application secret  
- `SCHWAB_REDIRECT_URI`: OAuth redirect URI (must match your app registration)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEFAULT_TICKER`: Default stock symbol to display
- `DEFAULT_EXPIRATION_DAYS`: Default expiration filter

## 🧪 Testing the Installation

### 1. **Test API Connection**
```python
from src.auth import SchwabAuth
from src.schwab_client import SchwabClient

# Initialize authentication
auth = SchwabAuth("your_app_key", "your_app_secret")

# Test connection (will prompt for authentication if needed)
if auth.authenticate():
    client = SchwabClient(auth)
    if client.test_connection():
        print("✅ API connection successful!")
    else:
        print("❌ API connection failed")
```

### 2. **Test Options Data Retrieval**
```python
# Get option chain for SPY
option_data = client.get_option_chain("SPY", contract_type="ALL", strike_count=10)
if option_data:
    print("✅ Options data retrieved successfully!")
else:
    print("❌ Failed to retrieve options data")
```

## 📁 Project Structure

```
schwab-options-tracker/
├── main.py                    # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env.template             # Environment variables template
├── .gitignore               # Git ignore file
├── README.md                # This file
├── config/
│   └── config.json          # Application configuration
├── src/
│   ├── __init__.py          # Package initialization
│   ├── auth.py              # Schwab OAuth2 authentication
│   ├── schwab_client.py     # API client for Schwab data
│   └── utils.py             # Utility functions and calculations
└── tokens/                  # Token storage (auto-created)
    └── schwab_tokens.json   # Stored authentication tokens
```

## 🔧 Troubleshooting

### Common Issues

#### 1. **Authentication Failures**
- Verify your API credentials in `.env`
- Ensure redirect URI matches your Schwab app configuration
- Check that your Schwab developer account is active

#### 2. **API Rate Limiting**
- The client includes built-in rate limiting
- If you encounter 429 errors, the app will automatically retry
- Consider reducing request frequency for large datasets

#### 3. **Token Expiration**
- Tokens are automatically refreshed
- If refresh fails, you'll need to re-authenticate
- Check token file permissions in `tokens/` directory

#### 4. **Missing Dependencies**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# If Streamlit issues:
pip install --upgrade streamlit

# If plotting issues:
pip install --upgrade plotly
```

#### 5. **Data Loading Issues**
- Verify symbol is valid and tradable
- Check if options are available for the symbol
- Ensure market is open for real-time data

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## 🔐 Security Considerations

- **Never commit API credentials** to version control
- Store tokens securely in the `tokens/` directory
- Use environment variables for all sensitive configuration
- The `.gitignore` file excludes sensitive files by default
- Consider using a secure credential manager for production use

## 📈 Advanced Usage

### Custom Greeks Calculations
```python
from src.utils import calculate_greeks

# Calculate Greeks for a specific option
greeks = calculate_greeks(
    S=100,      # Stock price
    K=105,      # Strike price
    T=0.25,     # Time to expiration (years)
    r=0.05,     # Risk-free rate
    sigma=0.2,  # Volatility
    option_type="call"
)
print(greeks)
```

### Unusual Activity Detection
```python
from src.utils import detect_unusual_activity

# Detect unusual activity with custom thresholds
unusual = detect_unusual_activity(
    df,
    volume_threshold=500,
    oi_threshold=100,
    ratio_threshold=3.0
)
```

### Export Data Programmatically
```python
# Export options data
df.to_csv(f"{symbol}_options_{datetime.now().strftime('%Y%m%d')}.csv")

# Export summary metrics
with open(f"{symbol}_summary.json", 'w') as f:
    json.dump(summary_metrics, f, indent=2)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It is not intended as financial advice. Trading options involves significant risk and may not be suitable for all investors. Always consult with a qualified financial advisor before making investment decisions.

## 🙋 Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Check this README for detailed setup instructions
- **Schwab API**: Refer to [Schwab Developer Documentation](https://developer.schwab.com/)

## 🔄 Updates and Maintenance

- Check for updates regularly via `git pull`
- Monitor Schwab API changes and deprecations
- Update dependencies periodically: `pip install --upgrade -r requirements.txt`

---

**Built with ❤️ for the options trading community**