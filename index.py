"""
Ponto de entrada para o Vercel - Bot Strategy Hub
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "success",
            "message": "Bot Strategy Hub API is running",
            "timestamp": datetime.now().isoformat(),
            "python_version": "3.12",
            "environment": "Vercel"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            response = {
                "status": "success",
                "message": "Data received successfully",
                "received_data": data,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError:
            response = {
                "status": "error",
                "message": "Invalid JSON data",
                "timestamp": datetime.now().isoformat()
            }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return