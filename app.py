import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/run-wifite', methods=['POST'])
def run_wifite():
    """
    Run Wifite for a specific Wi-Fi network (by BSSID or SSID).
    """
    data = request.get_json()
    target = data.get('bssid') or data.get('ssid')

    if not target:
        return jsonify({"success": False, "error": "No target provided"}), 400

    try:
        # Run Wifite in a non-blocking detached subprocess
        subprocess.Popen(
            ["sudo", "wifite", "-i", "wlan0", "-b", target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({"success": True, "message": f"Wifite started against {target}."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
