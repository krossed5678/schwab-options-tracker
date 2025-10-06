# 📊 OptiFlow Backtesting System

Complete guide for using OptiFlow's dual-app backtesting and live trading system.

## 🚀 Quick Start

### Option 1: Launch Both Apps Together (Recommended)
```bash
# Double-click this file to start both apps:
start_dual_apps.bat
```
- **Main OptiFlow**: http://localhost:8503 (live trading alerts)
- **Backtester**: http://localhost:8504 (strategy testing)

### Option 2: Launch Apps Separately
```bash
# Start main OptiFlow app
start_app.bat

# Start backtester (in separate terminal)
start_backtester.bat
```

### Option 3: Manual Launch
```bash
# Terminal 1: Main app
streamlit run main.py --server.port=8503

# Terminal 2: Backtester  
streamlit run backtest_app.py --server.port=8504
```

## 🎯 How It Works

### 🔄 **Data Synchronization**
The apps automatically sync data so you can:
- **Test strategies** on historical data in the backtester
- **Run live alerts** in the main OptiFlow app
- **Compare performance** between backtested and live results
- **Optimize strategies** based on real trading outcomes

### 📊 **Backtesting Features**

#### **Strategy Types**
- **Volume Spike**: Detect unusual volume (e.g., 3x average)
- **Price Change**: Significant price movements (e.g., >5%)
- **RSI Extreme**: Oversold/overbought conditions
- **Bollinger Breakout**: Price breaks above/below bands

#### **Performance Metrics**
- **Win Rate**: Percentage of profitable trades
- **Total Return**: Cumulative P&L percentage
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest loss from peak

#### **Exit Strategies**
- **Time-based**: Exit after X days
- **Price Target**: Exit at profit percentage
- **Stop Loss**: Exit at loss percentage

## 📈 **Using the Backtester**

### 1️⃣ **Strategy Tester Tab**
Build and test individual strategies:

```
Strategy Configuration:
├── Name: "My Volume Strategy"
├── Alert Type: "volume_spike" 
├── Threshold: 3.0 (3x average volume)
├── Condition: "above"
├── Exit Condition: "price_target"
└── Exit Value: 5.0 (5% profit target)
```

**Example Results:**
- 📊 Total Signals: 15
- ✅ Win Rate: 73.3% 
- 💰 Total Return: +24.5%
- 📈 Sharpe Ratio: 1.45

### 2️⃣ **Multi-Strategy Comparison**
Compare different approaches side-by-side (coming soon)

### 3️⃣ **Live Strategy Monitor**
See how backtested strategies perform with live OptiFlow alerts:

- View recent alerts from main app
- Track real-time performance vs backtested predictions
- Identify which strategies work best in current market conditions

### 4️⃣ **Strategy Library**
Pre-built strategies ready to test:

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Volume Surge** | 3x+ volume spikes | Momentum plays |
| **Momentum Breakout** | >5% price moves | Trend following |
| **Oversold RSI** | RSI < 30 | Mean reversion |
| **Bollinger Breakout** | Price > upper band | Volatility expansion |

## 🔧 **Advanced Features**

### **Data Integration**
Both apps share data automatically:

```
data/
├── optiflow_sync.db     # SQLite database for sync
├── alerts.json          # Live alerts from main app
└── performance_report.json  # Combined performance data
```

### **Sync System**
- **Live Alerts**: Logged to database when triggered
- **Backtest Results**: Stored for comparison
- **Performance Tracking**: Historical win rates and returns
- **Real-time Updates**: 30-second sync interval

### **Database Schema**
```sql
-- Live alerts from main OptiFlow app
live_alerts (timestamp, symbol, alert_type, threshold, current_value, message)

-- Backtest results for comparison  
backtest_alerts (timestamp, symbol, alert_type, threshold, simulated_value, actual_outcome)

-- Strategy performance history
strategy_performance (strategy_name, symbol, win_rate, total_return, sharpe_ratio, config)
```

## 💡 **Best Practices**

### **Strategy Development Workflow**

1. **📊 Backtest First**
   - Test strategy on 6-12 months of historical data
   - Aim for 60%+ win rate and 1.0+ Sharpe ratio
   - Test on multiple symbols (AAPL, TSLA, SPY, QQQ)

2. **🚀 Deploy Live**  
   - Create matching alert in main OptiFlow app
   - Start with small position sizes
   - Monitor performance vs backtest predictions

3. **🔄 Optimize Continuously**
   - Compare live vs backtested performance weekly
   - Adjust thresholds based on market conditions
   - Disable underperforming strategies

### **Symbol Selection**
**Best for backtesting:**
- **High Volume**: AAPL, TSLA, SPY, QQQ, NVDA
- **Consistent Patterns**: Large cap stocks and ETFs
- **Good Options Activity**: Liquid underlyings

### **Market Conditions**
- **Trending Markets**: Momentum strategies work better
- **Sideways Markets**: Mean reversion strategies excel  
- **High Volatility**: Shorter exit timeframes
- **Low Volatility**: Longer hold periods

## 🐛 **Troubleshooting**

### **Common Issues**

**"Sync not available" error:**
```bash
# Make sure data_sync.py is in src/ folder
# Restart both apps after adding the file
```

**No historical data:**
```bash
# yfinance connection issue - check internet
# Try a different symbol (e.g., AAPL instead of penny stock)
```

**Apps won't start on ports:**
```bash
# Port already in use
netstat -ano | findstr :8503
netstat -ano | findstr :8504

# Kill process or use different ports
streamlit run main.py --server.port=8505
```

**Sync database locked:**
```bash
# Close both apps completely
# Delete data/optiflow_sync.db
# Restart apps (database will be recreated)
```

### **Performance Tips**

- **Use fewer symbols** for faster backtests
- **Shorter date ranges** for quick testing
- **Cache data** by keeping apps running
- **Close browser tabs** for better performance

## 📊 **Example Workflows**

### **Workflow 1: Test New Strategy**
```
1. Open backtester (http://localhost:8504)
2. Build strategy in "Strategy Tester" tab
3. Test on AAPL, 1-year lookback
4. If win rate >60%, deploy in main app
5. Monitor "Live Strategy Monitor" tab for real performance
```

### **Workflow 2: Optimize Existing Alert**
```  
1. Check live alert performance in main app "Alerts" tab
2. Copy settings to backtester
3. Test different thresholds (2.0x, 3.0x, 4.0x volume)
4. Update main app with best performing threshold
```

### **Workflow 3: Market Regime Analysis**
```
1. Backtest multiple strategies on same symbol
2. Compare performance in different date ranges  
3. Identify which strategies work in current conditions
4. Rotate active strategies based on market regime
```

## 🎯 **Strategy Examples**

### **Volume Surge Scalping**
```
Alert Type: volume_spike
Threshold: 4.0 (4x average)
Condition: above
Exit: price_target, 3.0% (quick scalp)

Best for: Day trading momentum
Expected: 65% win rate, higher frequency
```

### **Momentum Swing Trading** 
```
Alert Type: price_change  
Threshold: 7.0 (7% move)
Condition: above
Exit: time, 3.0 days (swing hold)

Best for: Multi-day trends
Expected: 55% win rate, higher returns
```

### **Mean Reversion**
```
Alert Type: rsi_extreme
Threshold: 25.0 (oversold)  
Condition: below
Exit: price_target, 5.0% (rebound target)

Best for: Range-bound markets
Expected: 70% win rate, consistent gains
```

## 📈 **Performance Benchmarks**

### **Good Strategy Metrics**
- **Win Rate**: 60%+ 
- **Sharpe Ratio**: 1.0+
- **Max Drawdown**: <15%
- **Total Signals**: 20+ (sufficient data)

### **Excellent Strategy Metrics**  
- **Win Rate**: 70%+
- **Sharpe Ratio**: 1.5+
- **Max Drawdown**: <10%
- **Consistent**: Works across multiple symbols

---

## 🚀 **Ready to Start?**

1. **Launch both apps**: `start_dual_apps.bat`
2. **Test a strategy**: Go to backtester Strategy Tester tab
3. **Deploy live**: Add alert in main app Alerts tab  
4. **Monitor performance**: Check Live Strategy Monitor tab

**Happy backtesting and profitable trading!** 📊✨