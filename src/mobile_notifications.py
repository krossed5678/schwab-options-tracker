import requests
import smtplib
import os
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MobileNotificationManager:
    """
    Handle various mobile notification methods.
    """
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load notification configuration from environment variables."""
        self.config = {
            # Email/SMS Configuration
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_address': os.getenv('EMAIL_ADDRESS'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'alert_email': os.getenv('ALERT_EMAIL'),
            
            # Telegram Configuration
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            
            # Discord Configuration
            'discord_webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
            
            # Notification Toggles
            'enable_push': os.getenv('ENABLE_PUSH_NOTIFICATIONS', 'true').lower() == 'true',
            'enable_email': os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
            'enable_telegram': os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'false').lower() == 'true',
            'enable_discord': os.getenv('ENABLE_DISCORD_NOTIFICATIONS', 'false').lower() == 'true',
        }
    
    def send_notification(self, title: str, message: str, alert_type: str = "info") -> Dict[str, bool]:
        """
        Send notification via all enabled methods.
        
        Args:
            title: Notification title
            message: Notification message
            alert_type: Type of alert (info, warning, error, success)
            
        Returns:
            Dictionary showing success/failure for each method
        """
        results = {}
        
        # Email/SMS Notification
        if self.config['enable_email'] and self.config['email_address']:
            results['email'] = self.send_email_notification(title, message, alert_type)
        
        # Telegram Notification
        if self.config['enable_telegram'] and self.config['telegram_bot_token']:
            results['telegram'] = self.send_telegram_notification(title, message, alert_type)
        
        # Discord Notification
        if self.config['enable_discord'] and self.config['discord_webhook_url']:
            results['discord'] = self.send_discord_notification(title, message, alert_type)
        
        return results
    
    def send_email_notification(self, title: str, message: str, alert_type: str) -> bool:
        """Send email notification (can also be SMS via email gateway)."""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.config['email_address']
            msg['To'] = self.config['alert_email'] or self.config['email_address']
            msg['Subject'] = f"🚨 {title}"
            
            # Format message based on alert type
            emoji_map = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅',
                'unusual_volume': '📈',
                'price_change': '💰',
                'ipo_update': '🚀'
            }
            
            emoji = emoji_map.get(alert_type, 'ℹ️')
            body = f"{emoji} {title}\n\n{message}\n\nSent from OptiFlow"
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_address'], self.config['email_password'])
            
            text = msg.as_string()
            server.sendmail(self.config['email_address'], msg['To'], text)
            server.quit()
            
            logger.info(f"Email notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def send_telegram_notification(self, title: str, message: str, alert_type: str) -> bool:
        """Send Telegram notification via bot."""
        try:
            # Format message with emojis
            emoji_map = {
                'info': 'ℹ️',
                'warning': '⚠️', 
                'error': '❌',
                'success': '✅',
                'unusual_volume': '📈',
                'price_change': '💰',
                'ipo_update': '🚀'
            }
            
            emoji = emoji_map.get(alert_type, 'ℹ️')
            
            telegram_message = f"{emoji} *{title}*\n\n{message}\n\n_OptiFlow_"
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/sendMessage"
            
            payload = {
                'chat_id': self.config['telegram_chat_id'],
                'text': telegram_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent: {title}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False
    
    def send_discord_notification(self, title: str, message: str, alert_type: str) -> bool:
        """Send Discord notification via webhook."""
        try:
            # Color mapping for different alert types
            color_map = {
                'info': 0x3498db,      # Blue
                'warning': 0xf39c12,   # Orange
                'error': 0xe74c3c,     # Red
                'success': 0x2ecc71,   # Green
                'unusual_volume': 0x9b59b6,  # Purple
                'price_change': 0x1abc9c,    # Teal
                'ipo_update': 0xf1c40f       # Yellow
            }
            
            # Check if @everyone tagging is enabled and for which alert types
            tag_everyone_enabled = self.config.get('discord_tag_everyone', 'true').lower() == 'true'
            tag_everyone_types = self.config.get('discord_tag_everyone_types', 'unusual_volume,price_change,ipo_update,options_flow').split(',')
            tag_everyone_types = [t.strip() for t in tag_everyone_types]
            
            should_tag_everyone = tag_everyone_enabled and alert_type in tag_everyone_types
            
            embed = {
                "title": title,
                "description": message,
                "color": color_map.get(alert_type, 0x3498db),
                "footer": {
                    "text": "OptiFlow"
                },
                "timestamp": f"{requests.utils.default_headers()}"
            }
            
            # Build payload with optional @everyone mention
            payload = {
                "embeds": [embed]
            }
            
            # Add @everyone mention for important alerts with custom emoji based on alert type
            if should_tag_everyone:
                alert_emojis = {
                    'unusual_volume': '📊',
                    'price_change': '📈',
                    'ipo_update': '🚀',
                    'options_flow': '💰',
                    'iv_spike': '⚡',
                    'warning': '⚠️',
                    'error': '🚨'
                }
                emoji = alert_emojis.get(alert_type, '🔔')
                payload["content"] = f"@everyone {emoji} **OPTIFLOW ALERT** - {alert_type.replace('_', ' ').title()}"
            
            response = requests.post(
                self.config['discord_webhook_url'], 
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:  # Discord webhook success code
                logger.info(f"Discord notification sent: {title}")
                return True
            else:
                logger.error(f"Discord webhook error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return False
    
    def test_notifications(self) -> Dict[str, bool]:
        """Test all enabled notification methods."""
        test_title = "🧪 Test Alert"
        test_message = "This is a test notification from your OptiFlow trading dashboard. If you received this, notifications are working!"
        
        return self.send_notification(test_title, test_message, "success")
    
    def send_alert_notification(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """Send notification for a specific alert."""
        title = f"Alert Triggered: {alert['symbol']}"
        message = alert['description']
        alert_type = alert.get('type', 'info')
        
        return self.send_notification(title, message, alert_type)
    
    def send_summary_notification(self, summary_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send daily/periodic summary notification."""
        title = "📊 Daily Trading Summary"
        
        message = f"""
Portfolio P&L: ${summary_data.get('total_pnl', 0):.2f}
Active Positions: {summary_data.get('active_positions', 0)}
Alerts Triggered: {summary_data.get('alerts_triggered', 0)}
Top Mover: {summary_data.get('top_mover', 'N/A')}
        """.strip()
        
        return self.send_notification(title, message, "info")
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get status of notification configuration."""
        return {
            'email_configured': bool(self.config['email_address'] and self.config['email_password']),
            'telegram_configured': bool(self.config['telegram_bot_token'] and self.config['telegram_chat_id']),
            'discord_configured': bool(self.config['discord_webhook_url']),
            'email_enabled': self.config['enable_email'],
            'telegram_enabled': self.config['enable_telegram'],
            'discord_enabled': self.config['enable_discord'],
            'push_enabled': self.config['enable_push']
        }

# Utility functions for easy use
def send_mobile_alert(title: str, message: str, alert_type: str = "info") -> bool:
    """Quick function to send mobile notification."""
    notifier = MobileNotificationManager()
    results = notifier.send_notification(title, message, alert_type)
    return any(results.values())  # Return True if any method succeeded

def test_mobile_notifications() -> Dict[str, bool]:
    """Quick function to test all notification methods."""
    notifier = MobileNotificationManager()
    return notifier.test_notifications()