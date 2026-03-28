import os
import http.server
import threading
import re
import socket
from modules.utils import resource_path

# --- Local Backend Server Implementation ---
class LocalBackendHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract User-Agent from headers
        user_agent = self.headers.get('User-Agent', '')
        
        # Parse model and build from User-Agent using regex
        model_match = re.search(r'model/([a-zA-Z0-9,]+)', user_agent)
        build_match = re.search(r'build/([a-zA-Z0-9]+)', user_agent)

        if model_match and build_match:
            model = model_match.group(1)
            build = build_match.group(1)

            # Prevent directory traversal attacks
            if '..' in model or '..' in build:
                self.send_response(403)
                self.end_headers()
                return

            # Construct the local file path for patched.plist
            # Path updated to use the new 'assets' directory
            base_dir = resource_path(os.path.join('assets', 'plists'))
            file_path = os.path.join(base_dir, model, build, 'patched.plist')

            # Serve the file if it exists
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/xml')
                self.send_header('Content-Disposition', 'attachment; filename="patched.plist"')
                self.send_header('Content-Length', str(os.path.getsize(file_path)))
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Return 403 Forbidden if parsing fails or file doesn't exist
        self.send_response(403)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Forbidden')

    def log_message(self, format, *args):
        # Suppress logging to keep the console output clean
        pass

# Function to automatically get the current machine's local IP address
def get_local_ip():
    try:
        # Create a dummy socket to determine the preferred routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        # Fallback to localhost if network is unreachable
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_local_server():
    local_ip = get_local_ip()
    # Bind to 0.0.0.0 to allow access from the iOS device over Wi-Fi
    httpd = http.server.HTTPServer(("0.0.0.0", 0), LocalBackendHandler)
    port = httpd.server_address[1]
    
    # Run the server in a daemon thread so it closes when the main app exits
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    
    # Return the dynamically generated URL with the real local IP
    return f"http://{local_ip}:{port}"