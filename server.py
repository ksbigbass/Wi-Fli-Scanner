# improved_server.py
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WifiScanner:
    """Handles Wi-Fi scanning operations"""
    
    def __init__(self, interface='wlan0'):
        self.interface = interface
        self.cache = None
        self.cache_time = None
        self.cache_duration = 5  # Cache for 5 seconds
    
    def scan_nmcli(self) -> List[Dict]:
        """Scan using nmcli (NetworkManager)"""
        try:
            output = subprocess.check_output(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,CHAN,FREQ', 'dev', 'wifi'],
                universal_newlines=True,
                timeout=10
            )
            
            wifi_list = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split(':')
                if len(parts) >= 3:
                    ssid = parts[0] if parts[0] else '(Hidden Network)'
                    signal = int(parts[1]) if parts[1].isdigit() else 0
                    security = parts[2] if len(parts) > 2 else 'Open'
                    channel = parts[3] if len(parts) > 3 else 'N/A'
                    frequency = parts[4] if len(parts) > 4 else 'N/A'
                    
                    wifi_list.append({
                        "ssid": ssid,
                        "signal": signal,
                        "security": security,
                        "channel": channel,
                        "frequency": frequency,
                        "quality": self._signal_to_quality(signal)
                    })
            
            return sorted(wifi_list, key=lambda x: x['signal'], reverse=True)
            
        except subprocess.TimeoutExpired:
            logger.error("nmcli command timed out")
            raise Exception("Scan timeout")
        except subprocess.CalledProcessError as e:
            logger.error(f"nmcli failed: {e}")
            raise Exception("Scan failed")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def scan_iwlist(self) -> List[Dict]:
        """Fallback: scan using iwlist"""
        try:
            output = subprocess.check_output(
                ['iwlist', self.interface, 'scanning'],
                universal_newlines=True,
                timeout=10
            )
            
            # Parse iwlist output (simplified)
            wifi_list = []
            current_network = {}
            
            for line in output.split('\n'):
                line = line.strip()
                
                if 'Cell' in line and 'Address' in line:
                    if current_network:
                        wifi_list.append(current_network)
                    current_network = {}
                    
                elif 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip('"')
                    current_network['ssid'] = ssid if ssid else '(Hidden Network)'
                    
                elif 'Quality=' in line:
                    quality_str = line.split('Quality=')[1].split()[0]
                    if '/' in quality_str:
                        num, denom = quality_str.split('/')
                        signal = int((int(num) / int(denom)) * 100)
                        current_network['signal'] = signal
                        current_network['quality'] = self._signal_to_quality(signal)
                        
                elif 'Encryption key:' in line:
                    encrypted = 'on' in line.lower()
                    current_network['security'] = 'Secured' if encrypted else 'Open'
                    
                elif 'Channel:' in line:
                    current_network['channel'] = line.split('Channel:')[1].strip()
            
            if current_network:
                wifi_list.append(current_network)
                
            return sorted(wifi_list, key=lambda x: x.get('signal', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"iwlist scan failed: {e}")
            raise
    
    def scan(self) -> List[Dict]:
        """Scan with caching"""
        now = time.time()
        
        # Return cached data if fresh
        if self.cache and self.cache_time and (now - self.cache_time) < self.cache_duration:
            logger.info("Returning cached scan results")
            return self.cache
        
        # Try nmcli first, fallback to iwlist
        try:
            logger.info("Scanning with nmcli...")
            networks = self.scan_nmcli()
        except:
            logger.info("nmcli failed, trying iwlist...")
            try:
                networks = self.scan_iwlist()
            except:
                logger.error("All scan methods failed")
                return []
        
        # Update cache
        self.cache = networks
        self.cache_time = now
        
        return networks
    
    @staticmethod
    def _signal_to_quality(signal: int) -> str:
        """Convert signal strength to quality rating"""
        if signal >= 70:
            return "Excellent"
        elif signal >= 50:
            return "Good"
        elif signal >= 30:
            return "Fair"
        else:
            return "Poor"


class RequestHandler(SimpleHTTPRequestHandler):
    scanner = WifiScanner()
    
    def do_GET(self):
        if self.path == '/api/wifi-data':
            self.handle_wifi_api()
        elif self.path == '/api/health':
            self.handle_health_check()
        else:
            super().do_GET()
    
    def handle_wifi_api(self):
        """Handle Wi-Fi data API request"""
        try:
            networks = self.scanner.scan()
            
            response = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "count": len(networks),
                "wifi_networks": networks
            }
            
            self.send_json_response(200, response)
            logger.info(f"Served {len(networks)} networks")
            
        except Exception as e:
            logger.error(f"API error: {e}")
            self.send_json_response(500, {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def handle_health_check(self):
        """Health check endpoint"""
        self.send_json_response(200, {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    
    def send_json_response(self, status_code: int, data: dict):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Configure properly for production
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Override to use logging module"""
        logger.info("%s - %s" % (self.address_string(), format % args))


def run_server(host='127.0.0.1', port=8000):
    """Start the HTTP server"""
    server = HTTPServer((host, port), RequestHandler)
    logger.info(f"Server running on http://{host}:{port}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()