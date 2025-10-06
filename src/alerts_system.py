import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Any
from .mobile_notifications import MobileNotificationManager, send_mobile_alert, test_mobile_notifications
from .data_sync import log_alert_from_main_app

class AlertSystem:
    """
    Alert system for options unusual activity and IPO updates.
    """
    
    def __init__(self):
        self.alerts_file = 'data/alerts.json'
        self.load_alerts()
    
    def load_alerts(self):
        """Load saved alerts from file."""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                self.active_alerts = data.get('active_alerts', [])
                self.alert_history = data.get('alert_history', [])
            else:
                self.active_alerts = []
                self.alert_history = []
        except Exception:
            self.active_alerts = []
            self.alert_history = []
    
    def save_alerts(self):
        """Save alerts to file."""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'active_alerts': self.active_alerts,
                'alert_history': self.alert_history,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.alerts_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            st.error(f"Failed to save alerts: {str(e)}")
    
    def create_alert(self, alert_type: str, symbol: str, condition: str, 
                    threshold: float, description: str) -> bool:
        """Create a new alert."""
        alert = {
            'id': len(self.active_alerts) + len(self.alert_history) + 1,
            'type': alert_type,
            'symbol': symbol.upper(),
            'condition': condition,
            'threshold': threshold,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'triggered': False,
            'active': True
        }
        
        self.active_alerts.append(alert)
        self.save_alerts()
        return True
    
    def check_alerts(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alerts should be triggered."""
        triggered_alerts = []
        
        for alert in self.active_alerts:
            if self.evaluate_alert(alert, market_data):
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                alert['active'] = False
                
                self.alert_history.append(alert)
                triggered_alerts.append(alert)
                
                # Log to backtesting data sync
                try:
                    current_value = market_data.get(alert['symbol'], {}).get('price', alert['threshold'])
                    log_alert_from_main_app(
                        symbol=alert['symbol'],
                        alert_type=alert['type'], 
                        threshold=alert['threshold'],
                        current_value=current_value,
                        message=alert['description']
                    )
                except Exception as e:
                    pass  # Don't break main app if sync fails
        
        # Remove triggered alerts from active list
        self.active_alerts = [a for a in self.active_alerts if not a['triggered']]
        
        if triggered_alerts:
            self.save_alerts()
        
        return triggered_alerts
    
    def evaluate_alert(self, alert: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """Evaluate if an alert condition is met."""
        symbol = alert['symbol']
        condition = alert['condition']
        threshold = alert['threshold']
        
        # Mock evaluation - in real implementation, use actual market data
        if alert['type'] == 'unusual_volume':
            # Check if volume exceeds threshold
            current_volume = market_data.get(symbol, {}).get('volume', 0)
            if condition == 'above' and current_volume > threshold:
                return True
        
        elif alert['type'] == 'price_change':
            # Check price movement
            current_price = market_data.get(symbol, {}).get('price', 0)
            price_change = market_data.get(symbol, {}).get('price_change_pct', 0)
            if condition == 'above' and price_change > threshold:
                return True
            elif condition == 'below' and price_change < -threshold:
                return True
        
        elif alert['type'] == 'iv_spike':
            # Check implied volatility spike
            current_iv = market_data.get(symbol, {}).get('avg_iv', 0)
            if condition == 'above' and current_iv > threshold:
                return True
        
        return False

def create_alerts_dashboard():
    """Create the alerts dashboard."""
    st.header("🚨 Smart Alerts System")
    st.markdown("Set up alerts for unusual options activity, price movements, and IPO updates")
    
    # Initialize alert system
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = AlertSystem()
    
    alert_system = st.session_state.alert_system
    
    # Alert tabs
    alert_tab1, alert_tab2, alert_tab3, alert_tab4 = st.tabs([
        "➕ Create Alert", "🔔 Active Alerts", "📜 Alert History", "⚙️ Settings"
    ])
    
    with alert_tab1:
        st.subheader("➕ Create New Alert")
        
        # Alert creation form
        col1, col2 = st.columns(2)
        
        with col1:
            alert_type = st.selectbox("Alert Type", [
                "unusual_volume", "price_change", "iv_spike", "options_flow", "ipo_update"
            ])
            
            symbol = st.text_input("Symbol", placeholder="e.g., AAPL, SPY")
        
        with col2:
            if alert_type == "unusual_volume":
                condition = st.selectbox("Condition", ["above"])
                threshold = st.number_input("Volume Threshold", min_value=0, value=100000)
                description = f"Alert when {symbol} volume exceeds {threshold:,}"
                
            elif alert_type == "price_change":
                condition = st.selectbox("Condition", ["above", "below"])
                threshold = st.number_input("Price Change % Threshold", min_value=0.0, value=5.0, step=0.1)
                description = f"Alert when {symbol} moves {condition} {threshold}%"
                
            elif alert_type == "iv_spike":
                condition = st.selectbox("Condition", ["above"])
                threshold = st.number_input("IV Threshold (%)", min_value=0.0, value=50.0, step=1.0)
                description = f"Alert when {symbol} IV exceeds {threshold}%"
                
            elif alert_type == "options_flow":
                condition = st.selectbox("Condition", ["large_trade", "sweep"])
                threshold = st.number_input("Trade Size Threshold", min_value=0, value=1000000)
                description = f"Alert for large options flow in {symbol}"
                
            else:  # ipo_update
                condition = st.selectbox("Condition", ["filing", "pricing", "trading"])
                threshold = 0
                description = f"Alert for IPO updates on {symbol}"
        
        # Custom description
        custom_description = st.text_area("Custom Description (optional)", value=description)
        
        if st.button("Create Alert", type="primary"):
            if symbol and threshold >= 0:
                success = alert_system.create_alert(
                    alert_type, symbol, condition, threshold, custom_description
                )
                if success:
                    st.success(f"✅ Alert created for {symbol.upper()}")
                    st.rerun()
                else:
                    st.error("❌ Failed to create alert")
            else:
                st.error("Please fill in all required fields")
    
    with alert_tab2:
        st.subheader("🔔 Active Alerts")
        
        if alert_system.active_alerts:
            # Display active alerts
            alerts_df = pd.DataFrame(alert_system.active_alerts)
            
            # Format for display
            display_df = alerts_df[['symbol', 'type', 'condition', 'threshold', 'description', 'created_at']].copy()
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(display_df, use_container_width=True)
            
            # Delete alert functionality
            st.subheader("🗑️ Manage Alerts")
            alert_to_delete = st.selectbox("Select alert to delete:", 
                [f"{a['symbol']} - {a['type']}" for a in alert_system.active_alerts])
            
            if st.button("Delete Alert") and alert_to_delete:
                # Remove the selected alert
                symbol_type = alert_to_delete.split(' - ')
                alert_system.active_alerts = [
                    a for a in alert_system.active_alerts 
                    if not (a['symbol'] == symbol_type[0] and a['type'] == symbol_type[1])
                ]
                alert_system.save_alerts()
                st.success("Alert deleted!")
                st.rerun()
        else:
            st.info("No active alerts. Create some above!")
    
    with alert_tab3:
        st.subheader("📜 Alert History")
        
        if alert_system.alert_history:
            # Display alert history
            history_df = pd.DataFrame(alert_system.alert_history)
            
            # Format for display
            display_df = history_df[['symbol', 'type', 'description', 'triggered_at']].copy()
            display_df['triggered_at'] = pd.to_datetime(display_df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')
            display_df = display_df.sort_values('triggered_at', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Clear history
            if st.button("Clear History"):
                alert_system.alert_history = []
                alert_system.save_alerts()
                st.success("Alert history cleared!")
                st.rerun()
        else:
            st.info("No triggered alerts yet.")
    
    with alert_tab4:
        st.subheader("⚙️ Alert Settings")
        
        # Global alert settings
        st.write("**Global Settings**")
        
        enable_email = st.checkbox("Enable Email Notifications", value=False)
        if enable_email:
            email_address = st.text_input("Email Address", placeholder="your@email.com")
            st.info("Email notifications require SMTP configuration")
        
        enable_push = st.checkbox("Enable Browser Notifications", value=True)
        if enable_push:
            st.info("Browser notifications work when the app is open")
        
        # Alert frequency
        check_frequency = st.selectbox("Check Frequency", [
            "Real-time", "Every 1 minute", "Every 5 minutes", "Every 15 minutes"
        ])
        
        # Sound alerts
        enable_sound = st.checkbox("Enable Sound Alerts", value=True)
        
        # Testing alerts
        st.write("**Test Alerts**")
        if st.button("Send Test Alert"):
            st.success("🔔 Test alert triggered!")
            
            # Test mobile notifications
            try:
                results = test_mobile_notifications()
                if any(results.values()):
                    st.success("📱 Mobile notifications sent successfully!")
                    for method, success in results.items():
                        if success:
                            st.info(f"✅ {method.title()} notification delivered")
                        else:
                            st.warning(f"❌ {method.title()} notification failed")
                else:
                    st.warning("No mobile notifications configured. Check your .env file!")
            except Exception as e:
                st.error(f"Mobile notification error: {str(e)}")
            
            st.balloons()
        
        # Mobile notification status
        st.write("**📱 Mobile Notification Status**")
        try:
            notifier = MobileNotificationManager()
            status = notifier.get_config_status()
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Configuration:**")
                st.write(f"📧 Email: {'✅' if status['email_configured'] else '❌'}")
                st.write(f"📱 Telegram: {'✅' if status['telegram_configured'] else '❌'}")
                st.write(f"💬 Discord: {'✅' if status['discord_configured'] else '❌'}")
            
            with col2:
                st.write("**Enabled:**")
                st.write(f"📧 Email: {'✅' if status['email_enabled'] else '❌'}")
                st.write(f"📱 Telegram: {'✅' if status['telegram_enabled'] else '❌'}")
                st.write(f"💬 Discord: {'✅' if status['discord_enabled'] else '❌'}")
        
        except Exception as e:
            st.error(f"Could not load notification status: {str(e)}")

def check_and_display_alerts():
    """Check for triggered alerts and display them."""
    if 'alert_system' in st.session_state:
        alert_system = st.session_state.alert_system
        
        # Mock market data for testing
        mock_market_data = {
            'AAPL': {'volume': 50000000, 'price': 150.0, 'price_change_pct': 3.2, 'avg_iv': 25.5},
            'TSLA': {'volume': 80000000, 'price': 250.0, 'price_change_pct': -2.1, 'avg_iv': 45.2},
            'SPY': {'volume': 100000000, 'price': 420.0, 'price_change_pct': 1.1, 'avg_iv': 18.3}
        }
        
        triggered_alerts = alert_system.check_alerts(mock_market_data)
        
        if triggered_alerts:
            for alert in triggered_alerts:
                st.success(f"🚨 ALERT TRIGGERED: {alert['description']}")
                
                # Send mobile notification
                try:
                    mobile_results = send_mobile_alert(
                        title=f"Alert: {alert['symbol']}",
                        message=alert['description'],
                        alert_type=alert['type']
                    )
                    if mobile_results:
                        st.info("📱 Mobile notification sent!")
                except Exception as e:
                    st.warning(f"Mobile notification failed: {str(e)}")
                
                # Show alert details in sidebar
                with st.sidebar:
                    st.error(f"🚨 {alert['symbol']}: {alert['description']}")

# Add this function to check alerts periodically
def auto_refresh_alerts():
    """Auto-refresh alerts functionality."""
    # This would be called periodically in a real implementation
    # For now, we'll check alerts manually
    if st.button("🔄 Check Alerts Now"):
        check_and_display_alerts()
        st.rerun()