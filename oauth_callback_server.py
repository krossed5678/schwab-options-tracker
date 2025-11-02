#!/usr/bin/env python3
"""
Schwab OAuth Callback Server
Handles the OAuth callback and extracts the authorization code
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback"""
    
    def do_GET(self):
        """Handle GET requests to the callback URL"""
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            if parsed_url.path == '/callback':
                # Check if we got an authorization code
                if 'code' in query_params:
                    auth_code = query_params['code'][0]
                    
                    # Save the auth code to a file for the main app to read
                    with open('auth_code.txt', 'w') as f:
                        f.write(auth_code)
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    success_html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>OptiFlow - Authorization Success</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                            .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                            .success { color: #28a745; font-size: 24px; margin-bottom: 20px; }
                            .code { background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all; margin: 20px 0; }
                            .next-steps { text-align: left; margin-top: 30px; }
                            .next-steps ol { padding-left: 20px; }
                            .next-steps li { margin: 10px 0; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="success">✅ Authorization Successful!</div>
                            <p>Your Schwab API authorization was successful. The authorization code has been captured.</p>
                            
                            <div class="code">
                                <strong>Authorization Code:</strong><br>
                                """ + auth_code + """
                            </div>
                            
                            <div class="next-steps">
                                <h3>Next Steps:</h3>
                                <ol>
                                    <li>Close this browser window</li>
                                    <li>Return to your terminal/command prompt</li>
                                    <li>The setup script will automatically exchange this code for tokens</li>
                                    <li>Your OptiFlow bot will then be ready with Schwab API access!</li>
                                </ol>
                            </div>
                            
                            <p style="margin-top: 30px; color: #6c757d; font-size: 14px;">
                                You can close this window now. The authorization process will continue automatically.
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(success_html.encode('utf-8'))
                    
                    print(f"\n✅ Authorization code received: {auth_code[:20]}...")
                    print("🔄 Proceeding with token exchange...")
                    
                elif 'error' in query_params:
                    error = query_params['error'][0]
                    error_description = query_params.get('error_description', ['Unknown error'])[0]
                    
                    # Send error response
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    error_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>OptiFlow - Authorization Error</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
                            .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
                            .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="error">❌ Authorization Failed</div>
                            <p><strong>Error:</strong> {error}</p>
                            <p><strong>Description:</strong> {error_description}</p>
                            <p>Please try the authorization process again.</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(error_html.encode('utf-8'))
                    
                    print(f"\n❌ Authorization error: {error}")
                    print(f"Description: {error_description}")
                    
            else:
                # Unknown path
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            print(f"Error handling callback: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_callback_server(port=8080):
    """Start the OAuth callback server"""
    try:
        server = HTTPServer(('localhost', port), CallbackHandler)
        print(f"🚀 OAuth callback server started on http://localhost:{port}")
        print("🔗 Make sure ngrok is tunneling to this port!")
        print("⏳ Waiting for OAuth callback...")
        
        # Handle one request (the callback) then shutdown
        server.handle_request()
        server.server_close()
        
        # Check if we got an auth code
        if os.path.exists('auth_code.txt'):
            with open('auth_code.txt', 'r') as f:
                auth_code = f.read().strip()
            os.remove('auth_code.txt')  # Clean up
            return auth_code
        else:
            return None
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return None
    except Exception as e:
        print(f"❌ Server error: {e}")
        return None

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    auth_code = start_callback_server(port)
    
    if auth_code:
        print(f"✅ Got authorization code: {auth_code[:20]}...")
    else:
        print("❌ No authorization code received")