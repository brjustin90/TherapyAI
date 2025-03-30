import os
import sys
import unittest
import threading
import time
import http.server
import socketserver
import json
import urllib.request

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple HTTP handler for testing
class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/':
            response = {"message": "Welcome to the Test API"}
        elif self.path == '/health':
            response = {"status": "healthy", "version": "1.0.0"}
        else:
            response = {"error": "Not found"}
            
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Suppress logging output during tests
        return


class TestHTTP(unittest.TestCase):
    """Tests for basic HTTP functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Start HTTP server in a separate thread"""
        cls.port = 8787
        cls.server = socketserver.TCPServer(("", cls.port), TestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        # Give server time to start
        time.sleep(0.1)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        url = f"http://localhost:{self.port}/"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            self.assertEqual(data, {"message": "Welcome to the Test API"})
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        url = f"http://localhost:{self.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["version"], "1.0.0")
    
    @classmethod
    def tearDownClass(cls):
        """Stop the HTTP server"""
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(1)


if __name__ == "__main__":
    unittest.main() 