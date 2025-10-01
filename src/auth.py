import os
import json
import time
import base64
import urllib.parse
import webbrowser
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

class SchwabAuth:
    """
    Handles OAuth2 authentication for Schwab Trader API.
    
    This class manages the complete OAuth2 flow including:
    - Initial authorization code retrieval
    - Token exchange
    - Token refresh
    - Persistent token storage
    """
    
    def __init__(self, app_key: str, app_secret: str, redirect_uri: str = "https://127.0.0.1"):
        """
        Initialize the Schwab authentication handler.
        
        Args:
            app_key: Your Schwab API application key
            app_secret: Your Schwab API application secret
            redirect_uri: OAuth redirect URI (must match your app registration)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.base_url = "https://api.schwabapi.com"
        
        # Token storage
        self.tokens_dir = "tokens"
        self.token_file = os.path.join(self.tokens_dir, "schwab_tokens.json")
        
        # Ensure tokens directory exists
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Current tokens
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Load existing tokens if available
        self._load_tokens()
    
    def get_authorization_url(self) -> str:
        """
        Generate the authorization URL for OAuth2 flow.
        
        Returns:
            Authorization URL that user should visit to grant permissions
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_key,
            'redirect_uri': self.redirect_uri,
            'scope': 'readonly'  # Adjust scope based on your needs
        }
        
        auth_url = f"{self.base_url}/oauth/authorize?" + urllib.parse.urlencode(params)
        return auth_url
    
    def exchange_code_for_token(self, authorization_code: str) -> bool:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Code received from OAuth callback
            
        Returns:
            True if token exchange was successful, False otherwise
        """
        try:
            # Prepare authorization header
            auth_string = f"{self.app_key}:{self.app_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(
                f"{self.base_url}/oauth/token",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                logger.info("Successfully obtained access tokens")
                return True
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during token exchange: {str(e)}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            True if token refresh was successful, False otherwise
        """
        if not self._refresh_token:
            logger.error("No refresh token available")
            return False
        
        try:
            # Prepare authorization header
            auth_string = f"{self.app_key}:{self.app_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token
            }
            
            response = requests.post(
                f"{self.base_url}/oauth/token",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                logger.info("Successfully refreshed access token")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            return False
    
    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token or None if unable to obtain one
        """
        # Check if we have a token and it's not expired
        if self._access_token and self._token_expires_at:
            # Add a 5-minute buffer to prevent edge cases
            if datetime.now() < (self._token_expires_at - timedelta(minutes=5)):
                return self._access_token
        
        # Try to refresh the token
        if self._refresh_token:
            if self.refresh_access_token():
                return self._access_token
        
        # If refresh failed, we need new authorization
        logger.warning("No valid token available. New authorization required.")
        return None
    
    def is_authenticated(self) -> bool:
        """
        Check if we have valid authentication.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.get_valid_token() is not None
    
    def start_auth_flow(self) -> str:
        """
        Start the OAuth2 authentication flow.
        
        Returns:
            Authorization code from user input
        """
        auth_url = self.get_authorization_url()
        
        print("\n" + "="*60)
        print("SCHWAB API AUTHENTICATION REQUIRED")
        print("="*60)
        print(f"\n1. Visit this URL in your browser:\n{auth_url}")
        print("\n2. Log in to your Schwab account and authorize the application")
        print("\n3. You'll be redirected to a URL that starts with your redirect URI")
        print("   Copy the 'code' parameter from that URL")
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("\n✓ Browser opened automatically")
        except:
            print("\n⚠ Could not open browser automatically")
        
        print("\n" + "="*60)
        
        # Get authorization code from user
        while True:
            code = input("\nEnter the authorization code: ").strip()
            if code:
                return code
            print("Please enter a valid authorization code.")
    
    def authenticate(self) -> bool:
        """
        Complete authentication process if needed.
        
        Returns:
            True if authenticated successfully, False otherwise
        """
        # Check if already authenticated
        if self.is_authenticated():
            logger.info("Already authenticated with valid token")
            return True
        
        # Try to refresh existing token
        if self._refresh_token:
            if self.refresh_access_token():
                logger.info("Authentication successful via token refresh")
                return True
        
        # Start new auth flow
        print("\nStarting new authentication flow...")
        auth_code = self.start_auth_flow()
        
        if self.exchange_code_for_token(auth_code):
            logger.info("Authentication successful via new authorization")
            return True
        else:
            logger.error("Authentication failed")
            return False
    
    def _store_tokens(self, token_data: Dict[str, Any]) -> None:
        """Store tokens to file and update instance variables."""
        try:
            # Update instance variables
            self._access_token = token_data.get('access_token')
            self._refresh_token = token_data.get('refresh_token')
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 1800)  # Default 30 minutes
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Prepare data for storage
            storage_data = {
                'access_token': self._access_token,
                'refresh_token': self._refresh_token,
                'expires_at': self._token_expires_at.isoformat(),
                'obtained_at': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.token_file, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            logger.info("Tokens stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing tokens: {str(e)}")
    
    def _load_tokens(self) -> None:
        """Load tokens from file if they exist."""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                
                self._access_token = data.get('access_token')
                self._refresh_token = data.get('refresh_token')
                
                expires_at_str = data.get('expires_at')
                if expires_at_str:
                    self._token_expires_at = datetime.fromisoformat(expires_at_str)
                
                logger.info("Tokens loaded from file")
            else:
                logger.info("No existing token file found")
                
        except Exception as e:
            logger.error(f"Error loading tokens: {str(e)}")
            # Reset tokens on error
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
    
    def clear_tokens(self) -> None:
        """Clear stored tokens."""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
            
            logger.info("Tokens cleared")
            
        except Exception as e:
            logger.error(f"Error clearing tokens: {str(e)}")