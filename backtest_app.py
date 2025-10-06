#!/usr/bin/env python3
"""
OptiFlow Backtesting Web Application
Backtest alert strategies and analyze historical performance while OptiFlow runs live alerts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import yfinance as yf
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from dataclasses import dataclass

try:
    from src.data_sync import DataSyncManager, log_backtest_from_backtester, get_recent_live_performance
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False

# Configure Streamlit page
st.set_page_config(
    page_title="OptiFlow Backtester",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-metric {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
    }
    .warning-metric {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .backtest-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class AlertStrategy:
    """Define an alert strategy for backtesting."""
    name: str
    alert_type: str  # 'price_change', 'volume_spike', 'iv_change', etc.
    threshold: float
    condition: str  # 'above', 'below'
    timeframe: str  # '1m', '5m', '1h', '1d'
    exit_condition: str  # 'time', 'price_target', 'stop_loss'
    exit_value: float  # hours, percentage, etc.

@dataclass
class BacktestResult:
    """Store backtesting results."""
    strategy: AlertStrategy
    total_signals: int
    profitable_signals: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    trades: List[Dict[str, Any]]

class OptionsBacktester:
    """Core backtesting engine for alert strategies."""
    
    def __init__(self):
        self.data_cache = {}
        
    def fetch_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical price and volume data."""
        try:
            if symbol in self.data_cache:
                return self.data_cache[symbol]
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval="1d")
            
            if df.empty:
                return pd.DataFrame()
            
            # Calculate technical indicators
            df['Returns'] = df['Close'].pct_change()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
            df['Price_MA'] = df['Close'].rolling(window=20).mean()
            df['Price_Std'] = df['Close'].rolling(window=20).std()
            df['Bollinger_Upper'] = df['Price_MA'] + (2 * df['Price_Std'])
            df['Bollinger_Lower'] = df['Price_MA'] - (2 * df['Price_Std'])
            df['RSI'] = self.calculate_rsi(df['Close'])
            
            self.data_cache[symbol] = df
            return df
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def simulate_alert_strategy(self, symbol: str, strategy: AlertStrategy, 
                              start_date: date, end_date: date) -> BacktestResult:
        """Simulate an alert strategy on historical data."""
        
        df = self.fetch_historical_data(symbol, "2y")
        if df.empty:
            return self._empty_result(strategy)
        
        # Filter data by date range
        df = df[start_date:end_date].copy()
        if len(df) < 10:
            return self._empty_result(strategy)
        
        signals = self._generate_signals(df, strategy)
        trades = self._simulate_trades(df, signals, strategy)
        
        return self._calculate_performance(strategy, trades, df)
    
    def _generate_signals(self, df: pd.DataFrame, strategy: AlertStrategy) -> pd.Series:
        """Generate buy/sell signals based on strategy."""
        signals = pd.Series(False, index=df.index)
        
        if strategy.alert_type == 'volume_spike':
            if strategy.condition == 'above':
                signals = df['Volume_Ratio'] > strategy.threshold
        
        elif strategy.alert_type == 'price_change':
            if strategy.condition == 'above':
                signals = df['Returns'] > (strategy.threshold / 100)
            elif strategy.condition == 'below':
                signals = df['Returns'] < -(strategy.threshold / 100)
        
        elif strategy.alert_type == 'rsi_extreme':
            if strategy.condition == 'above':
                signals = df['RSI'] > strategy.threshold
            elif strategy.condition == 'below':
                signals = df['RSI'] < strategy.threshold
        
        elif strategy.alert_type == 'bollinger_breakout':
            if strategy.condition == 'above':
                signals = df['Close'] > df['Bollinger_Upper']
            elif strategy.condition == 'below':
                signals = df['Close'] < df['Bollinger_Lower']
        
        return signals
    
    def _simulate_trades(self, df: pd.DataFrame, signals: pd.Series, 
                        strategy: AlertStrategy) -> List[Dict[str, Any]]:
        """Simulate actual trades based on signals."""
        trades = []
        position = None
        
        for date, signal in signals.items():
            if signal and position is None:
                # Enter position
                entry_price = df.loc[date, 'Close']
                position = {
                    'entry_date': date,
                    'entry_price': entry_price,
                    'type': 'long' if strategy.condition == 'above' else 'short'
                }
            
            elif position and self._should_exit(df, date, position, strategy):
                # Exit position
                exit_price = df.loc[date, 'Close']
                
                if position['type'] == 'long':
                    pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                else:
                    pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
                
                trade = {
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'duration_days': (date - position['entry_date']).days,
                    'type': position['type']
                }
                
                trades.append(trade)
                position = None
        
        return trades
    
    def _should_exit(self, df: pd.DataFrame, current_date: pd.Timestamp, 
                    position: Dict[str, Any], strategy: AlertStrategy) -> bool:
        """Determine if position should be exited."""
        
        if strategy.exit_condition == 'time':
            # Exit after X days
            days_held = (current_date - position['entry_date']).days
            return days_held >= strategy.exit_value
        
        elif strategy.exit_condition == 'price_target':
            # Exit at profit target
            current_price = df.loc[current_date, 'Close']
            if position['type'] == 'long':
                return (current_price - position['entry_price']) / position['entry_price'] * 100 >= strategy.exit_value
            else:
                return (position['entry_price'] - current_price) / position['entry_price'] * 100 >= strategy.exit_value
        
        elif strategy.exit_condition == 'stop_loss':
            # Exit at stop loss
            current_price = df.loc[current_date, 'Close']
            if position['type'] == 'long':
                return (current_price - position['entry_price']) / position['entry_price'] * 100 <= -strategy.exit_value
            else:
                return (position['entry_price'] - current_price) / position['entry_price'] * 100 <= -strategy.exit_value
        
        return False
    
    def _calculate_performance(self, strategy: AlertStrategy, 
                             trades: List[Dict[str, Any]], df: pd.DataFrame) -> BacktestResult:
        """Calculate performance metrics."""
        
        if not trades:
            return self._empty_result(strategy)
        
        total_signals = len(trades)
        profitable_trades = [t for t in trades if t['pnl_pct'] > 0]
        profitable_signals = len(profitable_trades)
        win_rate = profitable_signals / total_signals * 100
        
        total_return = sum(t['pnl_pct'] for t in trades)
        
        # Calculate Sharpe ratio (simplified)
        returns = [t['pnl_pct'] for t in trades]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        result = BacktestResult(
            strategy=strategy,
            total_signals=total_signals,
            profitable_signals=profitable_signals,
            win_rate=win_rate,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            trades=trades
        )
        
        # Log to sync system if available
        if SYNC_AVAILABLE:
            try:
                results_dict = {
                    'win_rate': win_rate,
                    'total_return': total_return, 
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'total_signals': total_signals,
                    'config': {
                        'alert_type': strategy.alert_type,
                        'threshold': strategy.threshold,
                        'condition': strategy.condition,
                        'exit_condition': strategy.exit_condition,
                        'exit_value': strategy.exit_value
                    }
                }
                # We'll get the symbol from the calling function
                # log_backtest_from_backtester(strategy.name, symbol, results_dict)
            except Exception:
                pass  # Don't break backtester if sync fails
        
        return result
    
    def _empty_result(self, strategy: AlertStrategy) -> BacktestResult:
        """Return empty result when no data or trades."""
        return BacktestResult(
            strategy=strategy,
            total_signals=0,
            profitable_signals=0,
            win_rate=0.0,
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            trades=[]
        )

def create_strategy_builder() -> AlertStrategy:
    """Create UI for building alert strategies."""
    
    st.subheader("🎯 Strategy Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Strategy Name", value="My Alert Strategy")
        alert_type = st.selectbox("Alert Type", [
            "volume_spike", "price_change", "rsi_extreme", "bollinger_breakout"
        ])
        threshold = st.number_input("Threshold", value=2.0, step=0.1)
    
    with col2:
        condition = st.selectbox("Condition", ["above", "below"])
        exit_condition = st.selectbox("Exit Condition", ["time", "price_target", "stop_loss"])
        exit_value = st.number_input("Exit Value", value=5.0, step=0.5)
    
    return AlertStrategy(
        name=name,
        alert_type=alert_type,
        threshold=threshold,
        condition=condition,
        timeframe="1d",
        exit_condition=exit_condition,
        exit_value=exit_value
    )

def display_backtest_results(result: BacktestResult):
    """Display backtesting results with metrics and charts."""
    
    st.subheader(f"📊 Results: {result.strategy.name}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Signals", result.total_signals)
    
    with col2:
        st.metric("Win Rate", f"{result.win_rate:.1f}%", 
                 delta=f"{result.win_rate-50:.1f}%" if result.win_rate > 0 else None)
    
    with col3:
        st.metric("Total Return", f"{result.total_return:.2f}%",
                 delta=f"{result.total_return:.2f}%" if result.total_return != 0 else None)
    
    with col4:
        st.metric("Sharpe Ratio", f"{result.sharpe_ratio:.2f}",
                 delta="Good" if result.sharpe_ratio > 1 else "Poor")
    
    if result.trades:
        # Trade history table
        st.subheader("📋 Trade History")
        trades_df = pd.DataFrame(result.trades)
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.date
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.date
        
        # Color code profitable vs losing trades
        def color_pnl(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'
        
        styled_df = trades_df.style.applymap(color_pnl, subset=['pnl_pct'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Performance chart
        st.subheader("📈 Cumulative Performance")
        trades_df['cumulative_pnl'] = trades_df['pnl_pct'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trades_df['exit_date'],
            y=trades_df['cumulative_pnl'],
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#1f77b4', width=3)
        ))
        
        fig.update_layout(
            title="Cumulative P&L Over Time",
            xaxis_title="Date",
            yaxis_title="Cumulative P&L (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application entry point."""
    
    # Header
    st.markdown("""
    <div class="backtest-header">
        <h1>📊 OptiFlow Backtester</h1>
        <p>Test and optimize your alert strategies with historical data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Configuration")
        
        # Symbol input
        symbol = st.text_input("Symbol to Test", value="AAPL", help="Enter stock symbol (e.g., AAPL, TSLA)").upper()
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=365))
        with col2:
            end_date = st.date_input("End Date", value=date.today())
        
        st.markdown("---")
        
        # Live OptiFlow status
        st.header("🤖 OptiFlow Status")
        
        # Check if main app is running (simplified check)
        if os.path.exists("data/alerts.json"):
            st.success("✅ OptiFlow is running")
            
            try:
                with open("data/alerts.json", 'r') as f:
                    alerts_data = json.load(f)
                active_alerts = len(alerts_data.get('active_alerts', []))
                st.metric("Active Alerts", active_alerts)
            except:
                st.metric("Active Alerts", "Unknown")
        else:
            st.warning("⚠️ OptiFlow not detected")
            st.info("Start main app: `streamlit run main.py --server.port=8503`")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Strategy Tester", "📊 Multi-Strategy Comparison", "📈 Live Strategy Monitor", "📚 Strategy Library"
    ])
    
    with tab1:
        st.header("🎯 Single Strategy Backtesting")
        
        # Strategy builder
        strategy = create_strategy_builder()
        
        if st.button("🚀 Run Backtest", type="primary"):
            if symbol:
                with st.spinner(f"Backtesting {strategy.name} on {symbol}..."):
                    backtester = OptionsBacktester()
                    result = backtester.simulate_alert_strategy(symbol, strategy, start_date, end_date)
                    
                    # Log backtest results to sync system
                    if SYNC_AVAILABLE and result.total_signals > 0:
                        try:
                            results_dict = {
                                'win_rate': result.win_rate,
                                'total_return': result.total_return,
                                'sharpe_ratio': result.sharpe_ratio,
                                'max_drawdown': result.max_drawdown,
                                'total_signals': result.total_signals,
                                'config': {
                                    'alert_type': strategy.alert_type,
                                    'threshold': strategy.threshold,
                                    'condition': strategy.condition,
                                    'exit_condition': strategy.exit_condition,
                                    'exit_value': strategy.exit_value
                                }
                            }
                            log_backtest_from_backtester(strategy.name, symbol, results_dict)
                            st.success("✅ Backtest results logged for comparison with live alerts")
                        except Exception as e:
                            st.warning(f"⚠️ Could not sync results: {str(e)}")
                    
                    display_backtest_results(result)
            else:
                st.error("Please enter a symbol to test")
    
    with tab2:
        st.header("📊 Strategy Comparison")
        st.info("Compare multiple strategies side-by-side (coming soon)")
        
        # Placeholder for multi-strategy comparison
        if st.button("Add Strategy for Comparison"):
            st.session_state.strategies = getattr(st.session_state, 'strategies', [])
            st.session_state.strategies.append(create_strategy_builder())
    
    with tab3:
        st.header("📈 Live Strategy Performance")
        st.info("Monitor how your backtested strategies would perform with live OptiFlow alerts")
        
        if os.path.exists("data/alerts.json"):
            try:
                with open("data/alerts.json", 'r') as f:
                    alerts_data = json.load(f)
                
                st.subheader("Recent Alert History")
                history = alerts_data.get('alert_history', [])
                
                if history:
                    df = pd.DataFrame(history[-10:])  # Last 10 alerts
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No alert history found")
                    
            except Exception as e:
                st.error(f"Error reading alerts data: {str(e)}")
        else:
            st.warning("OptiFlow alerts data not found. Make sure the main app is running.")
    
    with tab4:
        st.header("📚 Pre-built Strategy Templates")
        
        strategies_library = {
            "Volume Surge": {
                "description": "Detect unusual volume spikes (3x+ average)",
                "alert_type": "volume_spike",
                "threshold": 3.0,
                "condition": "above"
            },
            "Momentum Breakout": {
                "description": "Price moves >5% in a day", 
                "alert_type": "price_change",
                "threshold": 5.0,
                "condition": "above"
            },
            "Oversold RSI": {
                "description": "RSI below 30 (potential reversal)",
                "alert_type": "rsi_extreme", 
                "threshold": 30.0,
                "condition": "below"
            },
            "Bollinger Breakout": {
                "description": "Price breaks above upper Bollinger Band",
                "alert_type": "bollinger_breakout",
                "threshold": 0.0,
                "condition": "above"
            }
        }
        
        for name, config in strategies_library.items():
            with st.expander(f"📋 {name}"):
                st.write(config["description"])
                
                if st.button(f"Load {name}", key=f"load_{name}"):
                    st.session_state.loaded_strategy = config
                    st.success(f"Loaded {name} strategy!")

if __name__ == "__main__":
    main()