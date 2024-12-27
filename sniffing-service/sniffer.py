import time
import paho.mqtt.client as mqtt
from scapy.all import *
import json
import os
import subprocess
import sys

class WifiSniffer:
    def __init__(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_broker = os.environ.get('MQTT_BROKER', 'localhost')
        self.mqtt_port = int(os.environ.get('MQTT_PORT', 1883))
        self.interface = None
        
    def setup_interface(self):
        """Set up wireless interface in monitor mode."""
        try:
            # Get list of wireless interfaces
            iwconfig_output = subprocess.check_output(['iwconfig'], stderr=subprocess.STDOUT).decode()
            interfaces = [line.split()[0] for line in iwconfig_output.split('\n') if 'IEEE 802.11' in line]
            
            if not interfaces:
                print("No wireless interfaces found. Please ensure your wireless adapter is connected.")
                print("Available interfaces:")
                subprocess.run(['ifconfig'])
                sys.exit(1)
                
            self.interface = interfaces[0]  # Use first wireless interface found
            
            # Kill any processes that might interfere with monitor mode
            subprocess.run(['airmon-ng', 'check', 'kill'], stderr=subprocess.DEVNULL)
            
            # Stop monitor mode if it's already running
            subprocess.run(['airmon-ng', 'stop', f'{self.interface}mon'], stderr=subprocess.DEVNULL)
            
            # Start monitor mode
            print(f"Setting up monitor mode on {self.interface}")
            result = subprocess.run(['airmon-ng', 'start', self.interface], 
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode != 0:
                print(f"Failed to set up monitor mode: {result.stderr}")
                sys.exit(1)
                
            # The monitor interface is usually interface name + 'mon'
            self.interface = f"{self.interface}mon"
            
            # Verify monitor mode is active
            iwconfig_check = subprocess.check_output(['iwconfig', self.interface]).decode()
            if 'Mode:Monitor' not in iwconfig_check:
                print(f"Failed to verify monitor mode on {self.interface}")
                sys.exit(1)
                
            print(f"Successfully set up monitor mode on {self.interface}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting up wireless interface: {str(e)}")
            sys.exit(1)
            
    def connect_mqtt(self):
        """Connect to MQTT broker with retry logic."""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"Attempting to connect to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
                self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
                self.mqtt_client.loop_start()
                print("Successfully connected to MQTT broker")
                return
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to MQTT broker (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    print("Max retries reached. Exiting.")
                    sys.exit(1)
        
    def packet_handler(self, pkt):
        """Handle captured packets and publish to MQTT."""
        try:
            if pkt.haslayer(Dot11):
                packet_data = {
                    'timestamp': time.time(),
                    'type': pkt.type,
                    'subtype': pkt.subtype,
                    'signal_strength': -(256-ord(pkt.notdecoded[-4:-3])) if pkt.notdecoded else None,
                    'src': pkt.addr2 if pkt.addr2 else None,
                    'dst': pkt.addr1 if pkt.addr1 else None,
                    'channel': int(ord(pkt.notdecoded[-4:-3])) if pkt.notdecoded else None
                }
                self.mqtt_client.publish('wifi/packets', json.dumps(packet_data))
        except Exception as e:
            print(f"Error handling packet: {str(e)}")
            
    def start_sniffing(self):
        """Start packet capture."""
        if not self.interface:
            print("No interface set up. Please run setup_interface() first.")
            return
            
        print(f"Starting WiFi monitoring on {self.interface}")
        try:
            sniff(iface=self.interface, prn=self.packet_handler, store=0)
        except Exception as e:
            print(f"Error during packet capture: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    sniffer = WifiSniffer()
    sniffer.setup_interface()
    sniffer.connect_mqtt()
    sniffer.start_sniffing()
