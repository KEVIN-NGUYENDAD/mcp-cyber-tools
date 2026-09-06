#!/usr/bin/env python3
"""
Simple HTTP server to serve Executive Dashboard
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8888
DASHBOARD_DIR = Path(__file__).parent.parent / 'dashboard'

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_message(self, format, *args):
        # Quieter logging
        pass

if __name__ == '__main__':
    os.chdir(str(DASHBOARD_DIR.parent))

    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f'🌐 Dashboard Server: http://localhost:{PORT}/dashboard/executive.html')
        print(f'📊 Press Ctrl+C to stop')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n✅ Server stopped')
