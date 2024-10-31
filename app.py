from flask import Flask, render_template, jsonify, request, send_file
from camera import Camera
import json
import os

app = Flask(__name__)

# Initialize variables
cameras = []
occupancy_limit = 100
zones = []  # Format: [{"id": "zone-0", "name": "Zone 1", "cameras": [1, 2], "occupancy_limit": 10}]
config_path = "camera_config.json"

def load_config():
    global occupancy_limit, zones
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            # Load cameras and occupancy limit
            cameras.clear()
            for cam in config_data.get("cameras", []):
                new_camera = Camera(cam['ip'], cam['username'], cam['password'])
                cameras.append(new_camera)
            occupancy_limit = config_data.get("occupancy_limit", 100)
            # Load zones with occupancy limits
            zones = config_data.get("zones", [])

def save_config():
    config_data = {
        "cameras": [{"ip": cam.ip, "username": cam.username, "password": cam.password} for cam in cameras],
        "occupancy_limit": occupancy_limit,
        "zones": zones  # Save zones with occupancy limits
    }
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

@app.route('/')
def dashboard():
    total_currently_in = sum(camera.get_counts()[2] for camera in cameras)
    return render_template('dashboard.html', total_currently_in=total_currently_in, occupancy_limit=occupancy_limit, zones=zones)

@app.route('/get_cameras', methods=['GET'])
def get_cameras():
    camera_data = [
        {
            "entered": camera.get_counts()[0],
            "exited": camera.get_counts()[1],
            "currently_in": camera.get_counts()[2]
        }
        for camera in cameras
    ]
    total_currently_in = sum(cam["currently_in"] for cam in camera_data)
    return jsonify(cameras=camera_data, zones=zones, total_currently_in=total_currently_in)

@app.route('/add_camera', methods=['POST'])
def add_camera():
    ip = request.json.get('ip')
    username = request.json.get('username')
    password = request.json.get('password')
    if ip and username and password:
        new_camera = Camera(ip, username, password)
        cameras.append(new_camera)
        save_config()
        return jsonify(success=True)
    return jsonify(success=False, error="Invalid camera details")

@app.route('/remove_camera/<int:index>', methods=['POST'])
def remove_camera(index):
    try:
        del cameras[index]
        save_config()
        return jsonify(success=True)
    except IndexError:
        return jsonify(success=False, error="Invalid camera index")

@app.route('/reset_counts', methods=['POST'])
def reset_counts():
    for camera in cameras:
        camera.reset_counts()
    return jsonify(success=True)

@app.route('/set_occupancy_limit', methods=['POST'])
def set_occupancy_limit():
    global occupancy_limit
    occupancy_limit = int(request.json.get('occupancy_limit'))
    save_config()
    return jsonify(success=True)

@app.route('/set_zone_occupancy_limit', methods=['POST'])
def set_zone_occupancy_limit():
    zone_id = request.json.get('zone_id')
    limit = int(request.json.get('occupancy_limit', 0))
    for zone in zones:
        if zone['id'] == zone_id:
            zone['occupancy_limit'] = limit
            save_config()
            return jsonify(success=True)
    return jsonify(success=False, error="Zone not found")

@app.route('/export_config', methods=['GET'])
def export_config():
    save_config()  # Ensure config is saved before export
    return send_file(config_path, as_attachment=True)

@app.route('/load_config', methods=['POST'])
def load_config_route():
    file = request.files.get('config_file')
    if file:
        config_data = json.load(file)
        cameras.clear()
        for cam in config_data.get("cameras", []):
            new_camera = Camera(cam['ip'], cam['username'], cam['password'])
            cameras.append(new_camera)
        occupancy_limit = config_data.get("occupancy_limit", 100)
        zones.extend(config_data.get("zones", []))
        save_config()
        return jsonify(success=True)
    return jsonify(success=False, error="No file provided")

# Load config on startup
load_config()

# The __main__ block has been removed for Apache to handle app startup