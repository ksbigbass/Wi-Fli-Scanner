# backend/app.py
from flask import Flask, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MQTT Configuration
mqtt_broker = os.environ.get('MQTT_BROKER', 'mqtt-broker')
mqtt_port = int(os.environ.get('MQTT_PORT', 1883))

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe("wifi/packets")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        socketio.emit('wifi_data', data)
    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

def start_mqtt():
    try:
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

if __name__ == '__main__':
    start_mqtt()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
