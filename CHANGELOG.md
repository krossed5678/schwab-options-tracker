# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-10-01

### Added
- Initial release of Schwab Options Tracker
- OAuth2 authentication with Schwab Trader API
- Real-time options chain data retrieval
- Interactive Streamlit dashboard
- Options Greeks calculations (Delta, Gamma, Theta, Vega, Rho)
- Implied volatility analysis and volatility smile visualization
- Unusual activity detection based on volume/open interest ratios
- Data export functionality (CSV, JSON)
- Comprehensive filtering and sorting options
- Rate limiting and error handling for API requests
- Token management with automatic refresh
- Complete documentation and setup scripts

### Features
- **Authentication**: Secure OAuth2 flow with token persistence
- **Data Retrieval**: Real-time options chains, quotes, and market data
- **Analysis Tools**: Greeks calculations, IV analysis, unusual activity detection
- **Visualization**: Interactive charts for volume, OI, and volatility
- **User Interface**: Intuitive Streamlit dashboard with sidebar controls
- **Export**: Multiple data export formats for further analysis
- **Configuration**: Flexible configuration via environment variables and JSON

### Technical Implementation
- Python 3.9+ support
- Streamlit web framework
- Plotly for interactive visualizations
- Pandas for data manipulation
- NumPy and SciPy for mathematical calculations
- Requests for HTTP API calls
- Comprehensive error handling and logging

### Documentation
- Detailed README with setup instructions
- Configuration examples and troubleshooting guide
- Code documentation and type hints
- License and contributing guidelines