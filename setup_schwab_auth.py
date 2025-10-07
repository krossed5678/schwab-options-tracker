#!/usr/bin/env python3
"""
Schwab API Authentication Setup
Run this once to authenticate with Schwab API and generate tokens
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_schwab_auth():
    """Setup Schwab authentication and generate initial tokens"""
    
    try:
        from src.auth import SchwabAuth
        
        # Get credentials from environment
        app_key = os.getenv('SCHWAB_APP_KEY')
        app_secret = os.getenv('SCHWAB_APP_SECRET')
        redirect_uri = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1')
        
        if not app_key or not app_secret:
            print("❌ Error: SCHWAB_APP_KEY and SCHWAB_APP_SECRET must be set in .env file")
            return False
        
        print("🔐 Setting up Schwab API authentication...")
        print(f"App Key: {app_key[:10]}...{app_key[-4:]}")
        print(f"Redirect URI: {redirect_uri}")
        
        # Initialize authentication
        auth = SchwabAuth(app_key, app_secret, redirect_uri)
        
        # Check if we already have valid tokens
        if auth.is_authenticated():
            print("✅ Already authenticated! Tokens are valid.")
            return True
        
        print("\n📋 Authentication Process:")
        print("1. A browser window will open to Schwab's login page")
        print("2. Log in with your Schwab credentials")
        print("3. Grant permission to your application")
        print("4. Copy the authorization code from the redirect URL")
        print("5. Paste it when prompted")
        
        input("\nPress Enter to continue...")
        
        # Start OAuth flow
        auth_url = auth.get_authorization_url()
        print(f"\n🌐 Opening browser to: {auth_url}")
        
        import webbrowser
        webbrowser.open(auth_url)
        
        print("\n⏳ After logging in and granting permission, you'll be redirected to:")
        print("https://127.0.0.1/?code=AUTHORIZATION_CODE&session=...")
        print("\n📝 Copy the 'code' parameter from the URL and paste it below:")
        
        auth_code = input("Authorization code: ").strip()
        
        if not auth_code:
            print("❌ No authorization code provided")
            return False
        
        # Exchange code for tokens
        print("🔄 Exchanging authorization code for tokens...")
        if auth.get_tokens(auth_code):
            print("✅ Authentication successful! Tokens saved.")
            print("🚀 Your OptiFlow bot is now ready to use Schwab API!")
            return True
        else:
            print("❌ Token exchange failed")
            return False
            
    except ImportError:
        print("❌ Error: Schwab authentication module not available")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Authentication setup failed: {e}")
        return False

def test_api_connection():
    """Test the API connection after authentication"""
    try:
        from src.auth import SchwabAuth
        from src.schwab_client import SchwabClient
        
        app_key = os.getenv('SCHWAB_APP_KEY')
        app_secret = os.getenv('SCHWAB_APP_SECRET')
        
        auth = SchwabAuth(app_key, app_secret)
        client = SchwabClient(auth)
        
        print("🧪 Testing API connection...")
        
        # Test with a simple quote
        if client.test_connection():
            print("✅ Schwab API connection successful!")
            print("🎉 Ready to run your OptiFlow Discord bot!")
            return True
        else:
            print("❌ API connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 OptiFlow Schwab API Setup")
    print("=" * 50)
    
    # Setup authentication
    if not setup_schwab_auth():
        print("❌ Authentication setup failed")
        return False
    
    # Test connection
    if not test_api_connection():
        print("❌ API connection test failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("You can now run your Discord bot:")
    print("python discord_bot.py")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n💡 Troubleshooting:")
        print("1. Verify your Schwab API credentials in .env")
        print("2. Make sure your redirect URI matches your Schwab app settings")
        print("3. Check that you have a Schwab brokerage account")
        print("4. Ensure your app has the required API permissions")
        
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)