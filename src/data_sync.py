#!/usr/bin/env python3
"""
OptiFlow Data Sync Module
Handles data sharing between main OptiFlow app and backtesting application.
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiveAlert:
    """Structure for live alerts from OptiFlow."""
    timestamp: datetime
    symbol: str
    alert_type: str
    threshold: float
    current_value: float
    message: str
    triggered: bool = True

@dataclass
class BacktestAlert:
    """Structure for backtested alerts."""
    timestamp: datetime
    symbol: str
    alert_type: str
    threshold: float
    simulated_value: float
    actual_outcome: Optional[float] = None
    accuracy_score: Optional[float] = None

class DataSyncManager:
    """Manages data synchronization between OptiFlow and backtester."""
    
    def __init__(self, db_path: str = "data/optiflow_sync.db"):
        self.db_path = db_path
        self.ensure_data_dir()
        self.init_database()
        self._running = False
        self._sync_thread = None
    
    def ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs("data", exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database for data sharing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Live alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS live_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        threshold REAL NOT NULL,
                        current_value REAL NOT NULL,
                        message TEXT,
                        triggered BOOLEAN DEFAULT TRUE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Backtest results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        threshold REAL NOT NULL,
                        simulated_value REAL NOT NULL,
                        actual_outcome REAL,
                        accuracy_score REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Strategy performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        backtest_date TEXT NOT NULL,
                        win_rate REAL,
                        total_return REAL,
                        sharpe_ratio REAL,
                        max_drawdown REAL,
                        total_signals INTEGER,
                        config TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def log_live_alert(self, alert: LiveAlert):
        """Log a live alert from OptiFlow main app."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO live_alerts 
                    (timestamp, symbol, alert_type, threshold, current_value, message, triggered)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.timestamp.isoformat(),
                    alert.symbol,
                    alert.alert_type, 
                    alert.threshold,
                    alert.current_value,
                    alert.message,
                    alert.triggered
                ))
                conn.commit()
                logger.info(f"Logged live alert: {alert.symbol} {alert.alert_type}")
        except Exception as e:
            logger.error(f"Error logging live alert: {str(e)}")
    
    def log_backtest_result(self, strategy_name: str, symbol: str, 
                           backtest_results: Dict[str, Any]):
        """Log backtest results for comparison with live performance."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO strategy_performance 
                    (strategy_name, symbol, backtest_date, win_rate, total_return, 
                     sharpe_ratio, max_drawdown, total_signals, config)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    strategy_name,
                    symbol,
                    datetime.now().isoformat(),
                    backtest_results.get('win_rate', 0),
                    backtest_results.get('total_return', 0),
                    backtest_results.get('sharpe_ratio', 0),
                    backtest_results.get('max_drawdown', 0),
                    backtest_results.get('total_signals', 0),
                    json.dumps(backtest_results.get('config', {}))
                ))
                conn.commit()
                logger.info(f"Logged backtest result: {strategy_name} on {symbol}")
        except Exception as e:
            logger.error(f"Error logging backtest result: {str(e)}")
    
    def get_live_alerts(self, symbol: Optional[str] = None, 
                       hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get recent live alerts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()
                
                if symbol:
                    cursor.execute("""
                        SELECT * FROM live_alerts 
                        WHERE symbol = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                    """, (symbol, cutoff_time))
                else:
                    cursor.execute("""
                        SELECT * FROM live_alerts 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                    """, (cutoff_time,))
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return results
        except Exception as e:
            logger.error(f"Error getting live alerts: {str(e)}")
            return []
    
    def get_strategy_performance(self, strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get historical backtest performance data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if strategy_name:
                    cursor.execute("""
                        SELECT * FROM strategy_performance 
                        WHERE strategy_name = ?
                        ORDER BY created_at DESC
                    """, (strategy_name,))
                else:
                    cursor.execute("""
                        SELECT * FROM strategy_performance 
                        ORDER BY created_at DESC LIMIT 50
                    """)
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return results
        except Exception as e:
            logger.error(f"Error getting strategy performance: {str(e)}")
            return []
    
    def sync_with_main_app(self):
        """Sync data with main OptiFlow app alerts.json."""
        try:
            alerts_file = "data/alerts.json"
            if not os.path.exists(alerts_file):
                return
            
            with open(alerts_file, 'r') as f:
                alerts_data = json.load(f)
            
            # Process recent alert history
            alert_history = alerts_data.get('alert_history', [])
            
            for alert_data in alert_history[-10:]:  # Last 10 alerts
                try:
                    alert = LiveAlert(
                        timestamp=datetime.fromisoformat(alert_data['timestamp']),
                        symbol=alert_data.get('symbol', 'UNKNOWN'),
                        alert_type=alert_data.get('type', 'unknown'),
                        threshold=alert_data.get('threshold', 0.0),
                        current_value=alert_data.get('current_value', 0.0),
                        message=alert_data.get('description', '')
                    )
                    
                    # Check if already logged (simple duplicate check)
                    if not self._is_duplicate_alert(alert):
                        self.log_live_alert(alert)
                        
                except Exception as e:
                    logger.error(f"Error processing alert: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error syncing with main app: {str(e)}")
    
    def _is_duplicate_alert(self, alert: LiveAlert) -> bool:
        """Check if alert is already logged (simple duplicate detection)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM live_alerts 
                    WHERE symbol = ? AND alert_type = ? AND 
                          ABS(julianday(?) - julianday(timestamp)) < 0.01
                """, (alert.symbol, alert.alert_type, alert.timestamp.isoformat()))
                
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.error(f"Error checking duplicate: {str(e)}")
            return False
    
    def start_sync_daemon(self, sync_interval: int = 30):
        """Start background sync daemon."""
        if self._running:
            return
        
        self._running = True
        
        def sync_loop():
            while self._running:
                try:
                    self.sync_with_main_app()
                    time.sleep(sync_interval)
                except Exception as e:
                    logger.error(f"Sync daemon error: {str(e)}")
                    time.sleep(sync_interval)
        
        self._sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info(f"Started sync daemon with {sync_interval}s interval")
    
    def stop_sync_daemon(self):
        """Stop background sync daemon."""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("Stopped sync daemon")
    
    def export_performance_report(self, output_file: str = "data/performance_report.json"):
        """Export comprehensive performance report."""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'live_alerts_summary': {},
                'backtest_performance': {},
                'strategy_comparison': []
            }
            
            # Live alerts summary
            live_alerts = self.get_live_alerts(hours_back=24*7)  # Last week
            symbols = set(alert['symbol'] for alert in live_alerts)
            
            for symbol in symbols:
                symbol_alerts = [a for a in live_alerts if a['symbol'] == symbol]
                report['live_alerts_summary'][symbol] = {
                    'total_alerts': len(symbol_alerts),
                    'alert_types': list(set(a['alert_type'] for a in symbol_alerts)),
                    'latest_alert': max(symbol_alerts, key=lambda x: x['timestamp']) if symbol_alerts else None
                }
            
            # Strategy performance
            strategy_data = self.get_strategy_performance()
            strategies = set(s['strategy_name'] for s in strategy_data)
            
            for strategy in strategies:
                strategy_results = [s for s in strategy_data if s['strategy_name'] == strategy]
                if strategy_results:
                    latest = max(strategy_results, key=lambda x: x['created_at'])
                    report['backtest_performance'][strategy] = {
                        'latest_win_rate': latest['win_rate'],
                        'latest_return': latest['total_return'],
                        'latest_sharpe': latest['sharpe_ratio'],
                        'total_backtests': len(strategy_results)
                    }
            
            # Save report
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Performance report exported to {output_file}")
            return report
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return None

# Global sync manager instance
sync_manager = DataSyncManager()

def log_alert_from_main_app(symbol: str, alert_type: str, threshold: float, 
                           current_value: float, message: str):
    """
    Helper function for main OptiFlow app to log alerts.
    Call this from the main app's alert system.
    """
    alert = LiveAlert(
        timestamp=datetime.now(),
        symbol=symbol,
        alert_type=alert_type,
        threshold=threshold,
        current_value=current_value,
        message=message
    )
    sync_manager.log_live_alert(alert)

def log_backtest_from_backtester(strategy_name: str, symbol: str, results: Dict[str, Any]):
    """
    Helper function for backtester app to log results.
    Call this from the backtester after running a strategy.
    """
    sync_manager.log_backtest_result(strategy_name, symbol, results)

def get_recent_live_performance(symbol: str, hours: int = 24) -> Dict[str, Any]:
    """
    Get recent live alert performance for comparison with backtests.
    """
    alerts = sync_manager.get_live_alerts(symbol, hours)
    
    if not alerts:
        return {'alerts': 0, 'types': [], 'latest': None}
    
    return {
        'alerts': len(alerts),
        'types': list(set(a['alert_type'] for a in alerts)),
        'latest': alerts[0] if alerts else None,
        'symbols_affected': list(set(a['symbol'] for a in alerts))
    }

if __name__ == "__main__":
    # Test the sync manager
    sync = DataSyncManager()
    sync.start_sync_daemon(sync_interval=10)
    
    try:
        print("Sync manager started. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sync.stop_sync_daemon()
        print("Sync manager stopped.")