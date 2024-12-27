# scan_wifi.py
import os
import json
import requests

def scan_wifi():
    scan_result = os.popen('iwlist wlan0 scanning').read()
    # Parse scan_result for SSID, Signal, Channel, etc. (Example uses dummy data)
    parsed_data = [{"SSID": "Network1", "Signal": -40, "Channel": 6},
                   {"SSID": "Network2", "Signal": -60, "Channel": 11}]
    return parsed_data

def send_to_server(data):
    url = "http://192.168.40.106:5000/api/wifi"
    requests.post(url, json=data)

if __name__ == "__main__":
    data = scan_wifi()
    send_to_server(data)
