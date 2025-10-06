#!/usr/bin/env python3
"""
Mobile Notifications Setup Script
Quick setup wizard for configuring mobile notifications
"""

import os
from dotenv import load_dotenv, set_key

def setup_mobile_notifications():
    """Interactive setup for mobile notifications."""
    
    print("📱 OPTIFLOW MOBILE NOTIFICATIONS SETUP")
    print("="*50)
    print("This wizard will help you configure mobile alerts for your OptiFlow trading dashboard")
    print("\nChoose your preferred notification methods:")
    
    env_file = ".env"
    
    # Load existing env
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Found existing .env file")
    else:
        print("❌ No .env file found. Creating one...")
        if os.path.exists(".env.template"):
            import shutil
            shutil.copy(".env.template", ".env")
            print("✅ Created .env from template")
    
    print("\n" + "="*50)
    print("NOTIFICATION METHOD SELECTION")
    print("="*50)
    
    # Method 1: Browser Push Notifications
    print("\n1️⃣ BROWSER PUSH NOTIFICATIONS (Easiest)")
    print("   ✅ Works immediately, no setup required")
    print("   ✅ Shows on phone when browser is open")
    browser_push = input("   Enable browser push notifications? (Y/n): ").lower() != 'n'
    
    # Method 2: Email/SMS
    print("\n2️⃣ EMAIL/SMS NOTIFICATIONS")
    print("   ✅ Very reliable, works anywhere") 
    print("   ⚙️ Requires email configuration")
    email_enable = input("   Setup email notifications? (y/N): ").lower() == 'y'
    
    if email_enable:
        print("\n   📧 EMAIL SETUP:")
        email_addr = input("   Your email address: ")
        print("   For Gmail, you need an 'App Password' (not your regular password)")
        print("   Go to: Google Account → Security → App Passwords → Generate")
        email_pass = input("   Email app password: ")
        
        print("\n   📱 SMS SETUP (Optional - send texts via email):")
        print("   Verizon: yourphone@vtext.com")
        print("   AT&T: yourphone@txt.att.net") 
        print("   T-Mobile: yourphone@tmomail.net")
        sms_email = input("   SMS email gateway (or press Enter to skip): ")
        
        # Save email config
        set_key(env_file, "EMAIL_ADDRESS", email_addr)
        set_key(env_file, "EMAIL_PASSWORD", email_pass)
        set_key(env_file, "ENABLE_EMAIL_NOTIFICATIONS", "true")
        if sms_email:
            set_key(env_file, "ALERT_EMAIL", sms_email)
    
    # Method 3: Telegram
    print("\n3️⃣ TELEGRAM NOTIFICATIONS (Recommended)")
    print("   ✅ Instant, reliable, works anywhere")
    print("   ⚙️ Requires Telegram bot setup (5 minutes)")
    telegram_enable = input("   Setup Telegram notifications? (y/N): ").lower() == 'y'
    
    if telegram_enable:
        print("\n   🤖 TELEGRAM BOT SETUP:")
        print("   1. Open Telegram and message @BotFather")
        print("   2. Send: /newbot")
        print("   3. Choose bot name and username")
        print("   4. Copy the bot token")
        bot_token = input("   Bot token: ")
        
        print("\n   5. Start your bot (send it any message)")
        print("   6. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        print("   7. Find 'chat' → 'id' in the response")
        chat_id = input("   Your chat ID: ")
        
        # Save Telegram config
        set_key(env_file, "TELEGRAM_BOT_TOKEN", bot_token)
        set_key(env_file, "TELEGRAM_CHAT_ID", chat_id)
        set_key(env_file, "ENABLE_TELEGRAM_NOTIFICATIONS", "true")
    
    # Method 4: Discord (Optional)
    print("\n4️⃣ DISCORD NOTIFICATIONS (Optional)")
    print("   ✅ Good for sharing with trading groups")
    discord_enable = input("   Setup Discord webhook? (y/N): ").lower() == 'y'
    
    if discord_enable:
        print("\n   💬 DISCORD WEBHOOK SETUP:")
        print("   1. Go to your Discord server")
        print("   2. Right-click channel → Edit Channel → Integrations → Webhooks")
        print("   3. Create New Webhook")
        print("   4. Copy webhook URL")
        webhook_url = input("   Webhook URL: ")
        
        # Save Discord config
        set_key(env_file, "DISCORD_WEBHOOK_URL", webhook_url)
        set_key(env_file, "ENABLE_DISCORD_NOTIFICATIONS", "true")
    
    # Save browser push setting
    set_key(env_file, "ENABLE_PUSH_NOTIFICATIONS", "true" if browser_push else "false")
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETE!")
    print("="*50)
    
    print("\n📱 CONFIGURED NOTIFICATIONS:")
    if browser_push:
        print("   ✅ Browser Push Notifications")
    if email_enable:
        print("   ✅ Email Notifications" + (" + SMS" if sms_email else ""))
    if telegram_enable:
        print("   ✅ Telegram Notifications")
    if discord_enable:
        print("   ✅ Discord Notifications")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Start your app: streamlit run main.py")
    print("   2. Go to 🚨 Alerts tab → ⚙️ Settings")
    print("   3. Click 'Send Test Alert' to verify notifications work")
    print("   4. Create your first alert!")
    
    print("\n💡 TIPS:")
    print("   • Set smart thresholds to avoid notification spam")
    print("   • Use Telegram for urgent alerts, email for summaries")
    print("   • Check MOBILE_NOTIFICATIONS.md for detailed guides")
    
    return True

def test_notifications():
    """Test all configured notification methods."""
    print("\n🧪 TESTING NOTIFICATIONS...")
    
    try:
        from src.mobile_notifications import test_mobile_notifications
        results = test_mobile_notifications()
        
        print("\n📱 TEST RESULTS:")
        for method, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {method.title()}: {status}")
        
        if any(results.values()):
            print("\n🎉 At least one notification method is working!")
        else:
            print("\n⚠️ No notifications were sent. Check your configuration.")
            
    except Exception as e:
        print(f"\n❌ Error testing notifications: {str(e)}")

if __name__ == "__main__":
    try:
        setup_mobile_notifications()
        
        print("\n" + "="*50)
        test_choice = input("Test notifications now? (Y/n): ").lower()
        if test_choice != 'n':
            test_notifications()
            
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {str(e)}")
        print("Check MOBILE_NOTIFICATIONS.md for manual setup instructions")