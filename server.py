# server.py
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/wifi-data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Run nmcli command to get Wi-Fi data
            try:
                output = subprocess.check_output(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi'], universal_newlines=True)
                wifi_list = []
                for line in output.strip().split('\n'):
                    ssid, signal, security = line.split(':')
                    wifi_list.append({
                        "ssid": ssid,
                        "signal": int(signal),
                        "security": security
                    })
                data = {"wifi_networks": wifi_list}
            except subprocess.CalledProcessError:
                data = {"error": "Failed to retrieve Wi-Fi data"}
            
            self.wfile.write(json.dumps(data).encode())
        else:
            super().do_GET()

# Start server
server = HTTPServer(('0.0.0.0', 8000), RequestHandler)
print("Server running on port 8000")
server.serve_forever()
