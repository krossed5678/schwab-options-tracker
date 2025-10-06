import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

def create_portfolio_tracker():
    """Create portfolio tracking functionality."""
    st.header("📊 Portfolio & Watchlist Tracker")
    st.markdown("Track your options positions and create watchlists")
    
    # Initialize session state for portfolio data
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    
    # Portfolio tabs
    portfolio_tab1, portfolio_tab2, portfolio_tab3 = st.tabs(["💼 Current Positions", "👁️ Watchlist", "📈 Performance"])
    
    with portfolio_tab1:
        st.subheader("💼 Current Options Positions")
        
        # Add new position form
        with st.expander("➕ Add New Position", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                symbol = st.text_input("Symbol", key="pos_symbol")
                option_type = st.selectbox("Type", ["CALL", "PUT"], key="pos_type")
            with col2:
                strike = st.number_input("Strike Price", min_value=0.0, step=0.5, key="pos_strike")
                quantity = st.number_input("Quantity", min_value=1, step=1, key="pos_qty")
            with col3:
                expiration = st.date_input("Expiration Date", key="pos_exp")
                entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01, key="pos_entry")
            
            if st.button("Add Position"):
                if symbol and strike > 0 and entry_price > 0:
                    position = {
                        'id': len(st.session_state.portfolio) + 1,
                        'symbol': symbol.upper(),
                        'type': option_type,
                        'strike': strike,
                        'quantity': quantity,
                        'expiration': expiration.strftime('%Y-%m-%d'),
                        'entry_price': entry_price,
                        'entry_date': datetime.now().strftime('%Y-%m-%d'),
                        'current_price': entry_price,  # Will be updated with real data
                        'pnl': 0.0
                    }
                    st.session_state.portfolio.append(position)
                    st.success(f"Added {option_type} position for {symbol}")
                    st.rerun()
        
        # Display current positions
        if st.session_state.portfolio:
            df = pd.DataFrame(st.session_state.portfolio)
            
            # Calculate P&L (simplified - would use real market data)
            df['total_cost'] = df['quantity'] * df['entry_price'] * 100  # Options are per 100 shares
            df['current_value'] = df['quantity'] * df['current_price'] * 100
            df['pnl'] = df['current_value'] - df['total_cost']
            df['pnl_pct'] = (df['pnl'] / df['total_cost'] * 100).round(2)
            
            # Format for display
            display_df = df[['symbol', 'type', 'strike', 'quantity', 'expiration', 'entry_price', 'current_price', 'pnl', 'pnl_pct']].copy()
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.2f}")
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
            display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}")
            display_df['pnl_pct'] = display_df['pnl_pct'].apply(lambda x: f"{x:+.1f}%")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Portfolio summary
            total_cost = df['total_cost'].sum()
            total_value = df['current_value'].sum()
            total_pnl = df['pnl'].sum()
            total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cost", f"${total_cost:,.2f}")
            with col2:
                st.metric("Current Value", f"${total_value:,.2f}")
            with col3:
                st.metric("Total P&L", f"${total_pnl:,.2f}", f"{total_pnl_pct:+.1f}%")
            with col4:
                winning_positions = len(df[df['pnl'] > 0])
                win_rate = (winning_positions / len(df) * 100) if len(df) > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%", f"{winning_positions}/{len(df)}")
        else:
            st.info("No positions yet. Add your first options position above!")
    
    with portfolio_tab2:
        st.subheader("👁️ Watchlist")
        
        # Add to watchlist
        col1, col2 = st.columns([2, 1])
        with col1:
            watch_symbol = st.text_input("Add Symbol to Watchlist", placeholder="e.g., AAPL, TSLA")
        with col2:
            if st.button("Add to Watchlist") and watch_symbol:
                if watch_symbol.upper() not in st.session_state.watchlist:
                    st.session_state.watchlist.append(watch_symbol.upper())
                    st.success(f"Added {watch_symbol.upper()} to watchlist")
                    st.rerun()
        
        # Display watchlist
        if st.session_state.watchlist:
            st.write("**Your Watchlist:**")
            
            # Create sample watchlist data
            watchlist_data = []
            for symbol in st.session_state.watchlist:
                # This would be replaced with real market data
                watchlist_data.append({
                    'Symbol': symbol,
                    'Price': f"${150 + hash(symbol) % 100:.2f}",  # Sample price
                    'Change': f"{(hash(symbol) % 10) - 5:.2f}%",  # Sample change
                    'Volume': f"{(hash(symbol) % 1000 + 100):,}",  # Sample volume
                    'Options Volume': f"{(hash(symbol) % 500 + 50):,}",  # Sample options volume
                })
            
            watchlist_df = pd.DataFrame(watchlist_data)
            st.dataframe(watchlist_df, use_container_width=True)
            
            # Remove from watchlist
            if st.session_state.watchlist:
                symbol_to_remove = st.selectbox("Remove from watchlist:", [""] + st.session_state.watchlist)
                if st.button("Remove") and symbol_to_remove:
                    st.session_state.watchlist.remove(symbol_to_remove)
                    st.success(f"Removed {symbol_to_remove} from watchlist")
                    st.rerun()
        else:
            st.info("No symbols in watchlist yet. Add some above!")
    
    with portfolio_tab3:
        st.subheader("📈 Portfolio Performance")
        
        if st.session_state.portfolio:
            # Create performance chart
            df = pd.DataFrame(st.session_state.portfolio)
            
            # Group by symbol
            symbol_performance = df.groupby('symbol').agg({
                'pnl': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            # Create pie chart of positions by symbol
            fig = go.Figure(data=[go.Pie(
                labels=symbol_performance['symbol'],
                values=symbol_performance['quantity'],
                title="Positions by Symbol"
            )])
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance over time (sample data)
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            portfolio_values = [10000 + i*100 + (hash(str(date)) % 500 - 250) for i, date in enumerate(dates)]
            
            performance_fig = go.Figure()
            performance_fig.add_trace(go.Scatter(
                x=dates,
                y=portfolio_values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=2)
            ))
            performance_fig.update_layout(
                title="Portfolio Performance (Last 30 Days)",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                height=400
            )
            st.plotly_chart(performance_fig, use_container_width=True)
        else:
            st.info("Add some positions to see portfolio performance!")

def save_portfolio_data():
    """Save portfolio data to file."""
    try:
        data = {
            'portfolio': st.session_state.get('portfolio', []),
            'watchlist': st.session_state.get('watchlist', []),
            'last_updated': datetime.now().isoformat()
        }
        
        os.makedirs('data', exist_ok=True)
        with open('data/portfolio.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return True
    except Exception as e:
        st.error(f"Failed to save portfolio data: {str(e)}")
        return False

def load_portfolio_data():
    """Load portfolio data from file."""
    try:
        if os.path.exists('data/portfolio.json'):
            with open('data/portfolio.json', 'r') as f:
                data = json.load(f)
            
            st.session_state.portfolio = data.get('portfolio', [])
            st.session_state.watchlist = data.get('watchlist', [])
            return True
    except Exception as e:
        st.error(f"Failed to load portfolio data: {str(e)}")
        return False