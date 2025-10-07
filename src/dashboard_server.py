#!/usr/bin/env python3
"""
OptiFlow Web Dashboard Server
Simple HTTP server to serve the live options flow dashboard
"""

import http.server
import socketserver
import os
import threading
import webbrowser
from datetime import datetime

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the dashboard server."""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory="templates", **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self.path = '/dashboard.html'
        
        # Add CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Override to reduce console spam."""
        pass  # Silent logging

class DashboardServer:
    """Simple dashboard server for OptiFlow."""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Start the dashboard server."""
        if self.running:
            return f"http://localhost:{self.port}"
        
        try:
            handler = DashboardHandler
            self.server = socketserver.TCPServer(("", self.port), handler)
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            print(f"🚀 OptiFlow Dashboard server started at http://localhost:{self.port}")
            return f"http://localhost:{self.port}"
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"⚠️  Port {self.port} already in use, trying next port...")
                self.port += 1
                return self.start()
            else:
                raise e
    
    def stop(self):
        """Stop the dashboard server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print(f"🛑 Dashboard server stopped")
    
    def get_url(self):
        """Get the server URL."""
        if self.running:
            return f"http://localhost:{self.port}"
        return None

# Global server instance
dashboard_server = DashboardServer()

def start_dashboard_server():
    """Start the dashboard server and return URL."""
    return dashboard_server.start()

def get_dashboard_url():
    """Get the dashboard URL if server is running."""
    return dashboard_server.get_url()

if __name__ == "__main__":
    # Test the server
    try:
        url = start_dashboard_server()
        print(f"Dashboard available at: {url}")
        print("Press Ctrl+C to stop...")
        
        # Keep the main thread alive
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        dashboard_server.stop()
        print("Server stopped.")