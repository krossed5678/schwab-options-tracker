import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.auth import SchwabAuth
from src.schwab_client import SchwabClient
from src.ipo_tracker import IPOTracker
from src.utils import (
    format_option_data, detect_unusual_activity, calculate_option_metrics_summary,
    format_currency, format_percentage, format_large_number
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Schwab Options Viewer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_config():
    """Load configuration from config file."""
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def initialize_api_client():
    """Initialize and authenticate the Schwab API client."""
    app_key = os.getenv('SCHWAB_APP_KEY')
    app_secret = os.getenv('SCHWAB_APP_SECRET')
    redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1')
    
    if not app_key or not app_secret:
        st.error("Missing Schwab API credentials. Please check your .env file.")
        st.stop()
    
    # Initialize authentication
    auth = SchwabAuth(app_key, app_secret, redirect_uri)
    
    # Check authentication status
    if not auth.is_authenticated():
        st.warning("API authentication required. Please follow the authentication flow.")
        
        with st.expander("🔐 API Authentication", expanded=True):
            st.write("**Step 1:** Click the button below to get your authorization URL")
            
            if st.button("Get Authorization URL"):
                auth_url = auth.get_authorization_url()
                st.write("**Step 2:** Visit this URL to authorize the application:")
                st.code(auth_url)
                st.write("**Step 3:** After authorization, copy the authorization code from the redirect URL")
            
            auth_code = st.text_input("Enter Authorization Code:", 
                                    placeholder="Paste the authorization code here")
            
            if st.button("Complete Authentication") and auth_code:
                with st.spinner("Exchanging code for tokens..."):
                    if auth.exchange_code_for_token(auth_code):
                        st.success("✅ Authentication successful!")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed. Please try again.")
        st.stop()
    
    # Create API client
    client = SchwabClient(auth)
    
    # Test connection
    with st.spinner("Testing API connection..."):
        if not client.test_connection():
            st.error("Failed to connect to Schwab API. Please check your authentication.")
            st.stop()
    
    return client

def create_options_chart(df, chart_type="volume"):
    """Create interactive charts for options data."""
    if df.empty:
        return None
    
    calls = df[df['option_type'] == 'CALL']
    puts = df[df['option_type'] == 'PUT']
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Calls', 'Puts'),
        vertical_spacing=0.1
    )
    
    if chart_type == "volume":
        y_col = 'volume'
        title = 'Options Volume by Strike'
        color_scale = 'Blues'
    elif chart_type == "open_interest":
        y_col = 'open_interest'
        title = 'Open Interest by Strike'
        color_scale = 'Greens'
    else:
        y_col = 'implied_volatility'
        title = 'Implied Volatility by Strike'
        color_scale = 'Reds'
    
    # Calls
    if not calls.empty:
        fig.add_trace(
            go.Bar(
                x=calls['strike'],
                y=calls[y_col],
                name='Calls',
                marker_color='green',
                opacity=0.7
            ),
            row=1, col=1
        )
    
    # Puts
    if not puts.empty:
        fig.add_trace(
            go.Bar(
                x=puts['strike'],
                y=puts[y_col],
                name='Puts',
                marker_color='red',
                opacity=0.7
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Strike Price")
    fig.update_yaxes(title_text=y_col.replace('_', ' ').title())
    
    return fig

def create_volatility_smile(df):
    """Create volatility smile chart."""
    if df.empty:
        return None
    
    calls = df[df['option_type'] == 'CALL']
    puts = df[df['option_type'] == 'PUT']
    
    fig = go.Figure()
    
    if not calls.empty:
        fig.add_trace(
            go.Scatter(
                x=calls['strike'],
                y=calls['implied_volatility'] * 100,
                mode='markers+lines',
                name='Calls',
                marker=dict(color='green', size=calls['volume']/10, 
                          sizemode='diameter', sizemin=3),
                line=dict(color='green')
            )
        )
    
    if not puts.empty:
        fig.add_trace(
            go.Scatter(
                x=puts['strike'],
                y=puts['implied_volatility'] * 100,
                mode='markers+lines',
                name='Puts',
                marker=dict(color='red', size=puts['volume']/10, 
                          sizemode='diameter', sizemin=3),
                line=dict(color='red')
            )
        )
    
    fig.update_layout(
        title='Implied Volatility Smile',
        xaxis_title='Strike Price',
        yaxis_title='Implied Volatility (%)',
        height=400
    )
    
    return fig

def display_options_table(df, title="Options Chain"):
    """Display formatted options table."""
    if df.empty:
        st.write("No options data available.")
        return
    
    # Format columns for display
    display_df = df.copy()
    
    # Format numeric columns
    numeric_columns = {
        'strike': lambda x: f"${x:.2f}",
        'bid': lambda x: f"${x:.2f}" if x > 0 else "-",
        'ask': lambda x: f"${x:.2f}" if x > 0 else "-",
        'last': lambda x: f"${x:.2f}" if x > 0 else "-",
        'mid_price': lambda x: f"${x:.2f}" if x > 0 else "-",
        'volume': lambda x: format_large_number(int(x)) if x > 0 else "-",
        'open_interest': lambda x: format_large_number(int(x)) if x > 0 else "-",
        'implied_volatility': lambda x: f"{x*100:.1f}%" if x > 0 else "-",
        'delta': lambda x: f"{x:.3f}" if abs(x) > 0 else "-",
        'gamma': lambda x: f"{x:.4f}" if abs(x) > 0 else "-",
        'theta': lambda x: f"{x:.4f}" if abs(x) > 0 else "-",
        'vega': lambda x: f"{x:.4f}" if abs(x) > 0 else "-",
        'vol_oi_ratio': lambda x: f"{x:.2f}" if x > 0 else "-"
    }
    
    for col, formatter in numeric_columns.items():
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(formatter)
    
    # Select and rename columns for display
    display_columns = {
        'symbol': 'Symbol',
        'option_type': 'Type',
        'strike': 'Strike',
        'expiration_date': 'Expiration',
        'days_to_expiration': 'DTE',
        'bid': 'Bid',
        'ask': 'Ask',
        'last': 'Last',
        'volume': 'Volume',
        'open_interest': 'OI',
        'implied_volatility': 'IV',
        'delta': 'Delta',
        'gamma': 'Gamma',
        'theta': 'Theta',
        'vega': 'Vega',
        'vol_oi_ratio': 'Vol/OI'
    }
    
    # Filter to existing columns
    available_columns = {k: v for k, v in display_columns.items() if k in display_df.columns}
    
    final_df = display_df[list(available_columns.keys())].rename(columns=available_columns)
    
    st.subheader(title)
    st.dataframe(
        final_df,
        use_container_width=True,
        height=400
    )

def create_ipo_dashboard():
    """Create the IPO tracking dashboard."""
    st.header("🚀 IPO Tracker - Upcoming & Recent IPOs")
    st.markdown("Track upcoming Initial Public Offerings and recent IPO performance")
    
    # Initialize IPO tracker
    ipo_tracker = IPOTracker()
    
    # IPO Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Upcoming IPOs", "📊 Recent Performance", "📈 IPO Calendar", "📋 Market Overview"])
    
    with tab1:
        st.subheader("🔮 Upcoming IPOs")
        
        # Controls for upcoming IPOs
        col1, col2 = st.columns(2)
        with col1:
            days_ahead = st.slider("Days Ahead to Look", 7, 365, 90)
        with col2:
            sector_filter = st.selectbox("Filter by Sector", 
                                       ["All Sectors", "Technology", "Biotechnology", 
                                        "Financial Technology", "Clean Energy", "Healthcare", 
                                        "Consumer Retail", "Industrial"])
        
        # Fetch and display upcoming IPOs
        upcoming_df = ipo_tracker.get_upcoming_ipos(days_ahead=days_ahead)
        
        if not upcoming_df.empty:
            # Apply sector filter
            if sector_filter != "All Sectors":
                upcoming_df = upcoming_df[upcoming_df['sector'] == sector_filter]
            
            if not upcoming_df.empty:
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Upcoming", len(upcoming_df))
                with col2:
                    avg_days = upcoming_df['days_until_ipo'].mean()
                    st.metric("Avg Days Until IPO", f"{avg_days:.0f}")
                with col3:
                    total_raise = upcoming_df['estimated_raise'].sum()
                    st.metric("Total Est. Raise", format_large_number(int(total_raise)))
                with col4:
                    avg_score = upcoming_df['appeal_score'].mean()
                    st.metric("Avg Appeal Score", f"{avg_score:.0f}/100")
                
                # Display upcoming IPOs table
                display_ipo_table(upcoming_df, "upcoming")
            else:
                st.info(f"No upcoming IPOs found in {sector_filter} sector for the next {days_ahead} days.")
        else:
            st.info("No upcoming IPO data available.")
    
    with tab2:
        st.subheader("📊 Recent IPO Performance")
        
        # Controls for recent IPOs
        col1, col2 = st.columns(2)
        with col1:
            days_back = st.slider("Days Back to Look", 7, 180, 30)
        with col2:
            sort_by = st.selectbox("Sort by", 
                                 ["IPO Date", "Current Return", "First Day Return", "Volume"])
        
        # Fetch recent IPOs
        recent_df = ipo_tracker.get_recent_ipos(days_back=days_back)
        
        if not recent_df.empty:
            # Sort dataframe
            sort_mapping = {
                "IPO Date": "ipo_date",
                "Current Return": "current_return",
                "First Day Return": "first_day_return",
                "Volume": "volume_today"
            }
            if sort_by in sort_mapping:
                recent_df = recent_df.sort_values(sort_mapping[sort_by], ascending=False)
            
            # Display performance metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Recent IPOs", len(recent_df))
            with col2:
                avg_return = recent_df['current_return'].mean()
                st.metric("Avg Return", f"{avg_return:+.1f}%")
            with col3:
                winners = len(recent_df[recent_df['current_return'] > 0])
                st.metric("Positive Returns", f"{winners}/{len(recent_df)}")
            with col4:
                best_performer = recent_df.loc[recent_df['current_return'].idxmax(), 'current_return']
                st.metric("Best Performer", f"+{best_performer:.1f}%")
            
            # Performance chart
            create_ipo_performance_chart(recent_df)
            
            # Display recent IPOs table
            display_ipo_table(recent_df, "recent")
        else:
            st.info("No recent IPO data available.")
    
    with tab3:
        st.subheader("📈 IPO Calendar View")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now().date())
        with col2:
            end_date = st.date_input("End Date", (datetime.now() + timedelta(days=180)).date())
        
        # Get calendar data
        calendar_df = ipo_tracker.get_ipo_calendar(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not calendar_df.empty:
            # Create calendar visualization
            create_ipo_calendar_chart(calendar_df)
            
            # Display calendar table
            st.subheader("IPO Calendar Details")
            display_ipo_table(calendar_df, "calendar")
        else:
            st.info("No IPO data available for the selected date range.")
    
    with tab4:
        st.subheader("📋 IPO Market Overview")
        
        # Get market statistics
        stats = ipo_tracker.get_ipo_statistics()
        
        if stats:
            # Market overview metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Upcoming IPOs", stats.get('upcoming_count', 0))
            with col2:
                st.metric("Recent IPOs (90d)", stats.get('recent_count', 0))
            with col3:
                avg_return = stats.get('recent_performance', {}).get('avg_return', 0)
                st.metric("Avg Recent Return", f"{avg_return:+.1f}%")
            with col4:
                sentiment = stats.get('market_sentiment', 'Neutral')
                st.metric("Market Sentiment", sentiment)
            
            # Hot sectors
            if stats.get('hot_sectors'):
                st.subheader("🔥 Hot Sectors")
                hot_sectors = stats['hot_sectors']
                for i, sector in enumerate(hot_sectors[:3]):
                    st.write(f"{i+1}. **{sector}**")
            
            # Sector breakdown
            if stats.get('upcoming_sectors'):
                st.subheader("📊 Upcoming IPOs by Sector")
                sector_data = stats['upcoming_sectors']
                
                # Create pie chart
                fig = px.pie(
                    values=list(sector_data.values()),
                    names=list(sector_data.keys()),
                    title="Upcoming IPOs Distribution by Sector"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance breakdown
            perf_data = stats.get('recent_performance', {})
            if perf_data:
                st.subheader("📈 Recent IPO Performance Breakdown")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Positive Returns", perf_data.get('positive_returns', 0))
                with col2:
                    st.metric("Negative Returns", perf_data.get('negative_returns', 0))
        else:
            st.info("No market overview data available.")

def display_ipo_table(df: pd.DataFrame, table_type: str):
    """Display formatted IPO table."""
    if df.empty:
        return
    
    display_df = df.copy()
    
    if table_type == "upcoming":
        # Format upcoming IPO columns
        columns_to_show = {
            'symbol': 'Symbol',
            'company_name': 'Company',
            'sector': 'Sector',
            'expected_date': 'Expected Date',
            'days_until_ipo': 'Days Until',
            'price_range': 'Price Range',
            'estimated_raise_formatted': 'Est. Raise',
            'status': 'Status',
            'appeal_score': 'Appeal Score'
        }
    elif table_type == "recent":
        # Format recent IPO columns
        columns_to_show = {
            'symbol': 'Symbol',
            'company_name': 'Company',
            'sector': 'Sector',
            'ipo_date': 'IPO Date',
            'ipo_price': 'IPO Price',
            'current_price': 'Current Price',
            'current_return': 'Return %',
            'volume_today': 'Volume'
        }
        
        # Format percentage columns
        display_df['current_return'] = display_df['current_return'].apply(lambda x: f"{x:+.1f}%")
        display_df['ipo_price'] = display_df['ipo_price'].apply(lambda x: f"${x:.2f}")
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
        display_df['volume_today'] = display_df['volume_today'].apply(format_large_number)
    else:
        # Calendar view
        columns_to_show = {
            'symbol': 'Symbol',
            'company_name': 'Company',
            'sector': 'Sector',
            'expected_date': 'Date',
            'status': 'Status',
            'type': 'Type'
        }
    
    # Filter to available columns
    available_columns = {k: v for k, v in columns_to_show.items() if k in display_df.columns}
    
    if available_columns:
        final_df = display_df[list(available_columns.keys())].rename(columns=available_columns)
        st.dataframe(final_df, use_container_width=True, height=400)

def create_ipo_performance_chart(df: pd.DataFrame):
    """Create IPO performance visualization."""
    if df.empty:
        return
    
    # Create performance chart
    fig = go.Figure()
    
    # Add current returns
    fig.add_trace(go.Bar(
        x=df['symbol'],
        y=df['current_return'],
        name='Current Return %',
        marker_color=['green' if x > 0 else 'red' for x in df['current_return']],
        text=[f"{x:+.1f}%" for x in df['current_return']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Recent IPO Performance",
        xaxis_title="IPO Symbol",
        yaxis_title="Return %",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_ipo_calendar_chart(df: pd.DataFrame):
    """Create IPO calendar timeline visualization."""
    if df.empty:
        return
    
    # Create timeline chart
    fig = px.timeline(
        df,
        x_start='expected_date',
        x_end='expected_date',
        y='company_name',
        color='sector',
        title="IPO Timeline",
        height=max(400, len(df) * 25)
    )
    
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application function."""
    st.title("📈 Schwab Options & IPO Tracker")
    st.markdown("**Real-time options analysis for ANY stock or ETF** • **IPO tracking & analysis** • Unusual activity detection • Advanced Greeks calculations")
    
    # Main navigation tabs
    main_tab1, main_tab2 = st.tabs(["📊 Options Analysis", "🚀 IPO Tracker"])
    
    with main_tab1:
        options_dashboard()
    
    with main_tab2:
        create_ipo_dashboard()

def options_dashboard():
    """Original options dashboard functionality."""
    # Show current capabilities
    st.info("💡 **Track Any Stock**: Enter any ticker symbol (AAPL, TSLA, NVDA, etc.) to analyze its options chain in real-time!")
    
    # Load configuration
    config = load_config()
    
    # Initialize API client
    try:
        client = initialize_api_client()
    except Exception as e:
        st.error(f"Failed to initialize API client: {str(e)}")
        return
    
    # Sidebar controls
    st.sidebar.header("📈 Stock Selection")
    
    # Symbol input with examples
    st.sidebar.markdown("**Enter any stock ticker symbol:**")
    default_ticker = os.getenv('DEFAULT_TICKER', 'SPY')
    symbol = st.sidebar.text_input(
        "Stock Symbol", 
        value=default_ticker,
        placeholder="e.g., AAPL, TSLA, MSFT, NVDA, QQQ",
        help="Enter any publicly traded stock or ETF symbol"
    ).upper()
    
    # Popular symbols quick select
    st.sidebar.markdown("**Quick Select Popular Symbols:**")
    popular_symbols = {
        "🔥 Mega Cap": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
        "📊 ETFs": ["SPY", "QQQ", "IWM", "VIX", "GLD", "TLT", "EEM"],
        "💰 Finance": ["JPM", "BAC", "WFC", "GS", "MS", "C", "V"],
        "🏭 Industrial": ["BA", "CAT", "GE", "MMM", "HON", "UPS", "LMT"],
        "💊 Healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "DHR"],
        "⚡ Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO"]
    }
    
    selected_category = st.sidebar.selectbox("Select Category:", list(popular_symbols.keys()))
    
    cols = st.sidebar.columns(4)
    for i, ticker in enumerate(popular_symbols[selected_category]):
        if cols[i % 4].button(ticker, key=f"btn_{ticker}"):
            symbol = ticker
            st.rerun()
    
    # Recent symbols
    if 'recent_symbols' not in st.session_state:
        st.session_state.recent_symbols = []
    
    if st.session_state.recent_symbols:
        st.sidebar.markdown("**Recently Viewed:**")
        recent_cols = st.sidebar.columns(min(len(st.session_state.recent_symbols), 5))
        for i, recent_symbol in enumerate(st.session_state.recent_symbols[:5]):
            if recent_cols[i % 5].button(recent_symbol, key=f"recent_{recent_symbol}"):
                symbol = recent_symbol
                st.rerun()
    
    st.sidebar.header("⚙️ Options Parameters")
    
    # Expiration filtering
    exp_days = st.sidebar.selectbox(
        "Days to Expiration",
        options=[7, 14, 30, 45, 60, 90, "All"],
        index=2
    )
    
    # Contract type
    contract_type = st.sidebar.selectbox(
        "Contract Type",
        options=["ALL", "CALL", "PUT"],
        index=0
    )
    
    # Strike range
    strike_count = st.sidebar.slider("Number of Strikes", 5, 50, 20)
    
    # Advanced options
    with st.sidebar.expander("Advanced Options"):
        range_type = st.selectbox(
            "Strike Range",
            options=["ALL", "ITM", "OTM", "NTM"],
            index=0
        )
        
        include_quotes = st.checkbox("Include Real-time Quotes", value=True)
    
    # Unusual activity parameters
    st.sidebar.header("Unusual Activity")
    vol_threshold = st.sidebar.number_input("Volume Threshold", value=100, min_value=0)
    oi_threshold = st.sidebar.number_input("Open Interest Threshold", value=50, min_value=0)
    ratio_threshold = st.sidebar.number_input("Vol/OI Ratio Threshold", value=2.0, min_value=0.1, step=0.1)
    
    # Symbol validation and search
    st.sidebar.header("🔍 Symbol Lookup")
    if st.sidebar.button("🔎 Validate Symbol"):
        if symbol:
            with st.spinner(f"Validating symbol {symbol}..."):
                try:
                    # Try to get a quote to validate the symbol
                    quote_data = client.get_quote(symbol)
                    if quote_data and symbol in quote_data:
                        quote_info = quote_data[symbol]
                        company_name = quote_info.get('description', 'N/A')
                        last_price = quote_info.get('last', 0)
                        st.sidebar.success(f"✅ Valid Symbol")
                        st.sidebar.write(f"**{symbol}**: {company_name}")
                        st.sidebar.write(f"**Price**: ${last_price:.2f}")
                    else:
                        st.sidebar.error(f"❌ Invalid symbol: {symbol}")
                except Exception as e:
                    st.sidebar.warning(f"⚠️ Could not validate: {str(e)}")
        else:
            st.sidebar.error("Please enter a symbol to validate")
    
    # Fetch data button
    if st.sidebar.button("🔄 Fetch Options Data", type="primary"):
        if not symbol:
            st.error("Please enter a stock symbol.")
            return
        
        with st.spinner(f"Fetching options data for {symbol}..."):
            try:
                # Prepare parameters
                params = {
                    'symbol': symbol,
                    'contract_type': contract_type,
                    'strike_count': strike_count,
                    'include_quotes': include_quotes,
                    'range_type': range_type
                }
                
                # Add expiration filter
                if exp_days != "All":
                    from_date = datetime.now().strftime('%Y-%m-%d')
                    to_date = (datetime.now() + timedelta(days=exp_days)).strftime('%Y-%m-%d')
                    params['from_date'] = from_date
                    params['to_date'] = to_date
                
                # Fetch option chain
                option_data = client.get_option_chain(**params)
                
                if option_data:
                    # Store in session state
                    st.session_state.option_data = option_data
                    st.session_state.symbol = symbol
                    
                    # Add to recent symbols (avoid duplicates)
                    if symbol not in st.session_state.recent_symbols:
                        st.session_state.recent_symbols.insert(0, symbol)
                        # Keep only last 10 symbols
                        st.session_state.recent_symbols = st.session_state.recent_symbols[:10]
                    elif symbol in st.session_state.recent_symbols:
                        # Move to front if already exists
                        st.session_state.recent_symbols.remove(symbol)
                        st.session_state.recent_symbols.insert(0, symbol)
                    
                    st.success(f"✅ Successfully fetched options data for {symbol}")
                else:
                    st.error(f"❌ Failed to fetch options data for {symbol}")
                    return
                    
            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")
                return
    
    # Display data if available
    if hasattr(st.session_state, 'option_data') and st.session_state.option_data:
        option_data = st.session_state.option_data
        symbol = st.session_state.symbol
        
        # Format data
        df = format_option_data(option_data)
        
        if df.empty:
            st.warning("No options data available for the selected criteria.")
            return
        
        # Display summary metrics
        st.header(f"📊 Options Summary for {symbol}")
        
        summary = calculate_option_metrics_summary(df)
        underlying = option_data.get('underlying', {})
        underlying_price = underlying.get('last', 0)
        
        # Show company info if available
        company_name = underlying.get('description', symbol)
        if company_name != symbol:
            st.markdown(f"**Company**: {company_name}")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Underlying Price", format_currency(underlying_price))
        with col2:
            st.metric("Total Contracts", format_large_number(summary.get('total_contracts', 0)))
        with col3:
            st.metric("Total Volume", format_large_number(summary.get('total_volume', 0)))
        with col4:
            st.metric("Total OI", format_large_number(summary.get('total_open_interest', 0)))
        with col5:
            st.metric("Avg IV", format_percentage(summary.get('avg_implied_vol', 0) * 100, 1))
        
        col6, col7, col8 = st.columns(3)
        with col6:
            st.metric("Call Volume", format_large_number(summary.get('call_volume', 0)))
        with col7:
            st.metric("Put Volume", format_large_number(summary.get('put_volume', 0)))
        with col8:
            pcr = summary.get('put_call_volume_ratio', 0)
            if pcr == float('inf'):
                pcr_display = "∞"
            else:
                pcr_display = f"{pcr:.2f}"
            st.metric("P/C Ratio", pcr_display)
        
        # Charts section
        st.header("📈 Visualizations")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            chart_type = st.selectbox("Chart Type", ["volume", "open_interest", "implied_volatility"])
            chart = create_options_chart(df, chart_type)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
        
        with chart_col2:
            vol_chart = create_volatility_smile(df)
            if vol_chart:
                st.plotly_chart(vol_chart, use_container_width=True)
        
        # Unusual Activity
        st.header("🚨 Unusual Activity Detection")
        
        unusual_df = detect_unusual_activity(df, vol_threshold, oi_threshold, ratio_threshold)
        
        if not unusual_df.empty:
            st.write(f"Found {len(unusual_df)} contracts with unusual activity:")
            display_options_table(unusual_df, "Unusual Activity")
        else:
            st.info("No unusual activity detected with current thresholds.")
        
        # Full Options Chain
        st.header("🔗 Complete Options Chain")
        
        # Filter options
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            exp_filter = st.selectbox(
                "Filter by Expiration",
                options=["All"] + sorted(df['expiration_date'].unique().tolist()),
                index=0
            )
        
        with filter_col2:
            type_filter = st.selectbox(
                "Filter by Type",
                options=["All", "CALL", "PUT"],
                index=0
            )
        
        with filter_col3:
            itm_filter = st.selectbox(
                "Filter by Moneyness",
                options=["All", "ITM", "OTM"],
                index=0
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if exp_filter != "All":
            filtered_df = filtered_df[filtered_df['expiration_date'] == exp_filter]
        
        if type_filter != "All":
            filtered_df = filtered_df[filtered_df['option_type'] == type_filter]
        
        if itm_filter != "All":
            filtered_df = filtered_df[filtered_df['itm_otm'] == itm_filter]
        
        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            options=["strike", "volume", "open_interest", "implied_volatility", "days_to_expiration"],
            index=1
        )
        
        sort_order = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True)
        ascending = sort_order == "Ascending"
        
        filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)
        
        display_options_table(filtered_df, f"Options Chain ({len(filtered_df)} contracts)")
        
        # Export functionality
        st.header("💾 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Download Full Chain CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{symbol}_options_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🚨 Download Unusual Activity CSV"):
                if not unusual_df.empty:
                    csv = unusual_df.to_csv(index=False)
                    st.download_button(
                        label="Download Unusual Activity CSV",
                        data=csv,
                        file_name=f"{symbol}_unusual_activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No unusual activity data to export")
        
        with col3:
            if st.button("📋 Download Summary JSON"):
                json_data = json.dumps({
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat(),
                    'underlying_price': underlying_price,
                    'summary': summary
                }, indent=2)
                st.download_button(
                    label="Download Summary JSON",
                    data=json_data,
                    file_name=f"{symbol}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()