# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    HOST: str = os.getenv('HOST', '127.0.0.1')  # Localhost by default
    PORT: int = int(os.getenv('PORT', 8000))
    SCAN_INTERVAL: int = 10  # seconds
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    WIFI_INTERFACE: str = os.getenv('WIFI_INTERFACE', 'wlan0')