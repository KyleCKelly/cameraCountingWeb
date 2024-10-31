from flask import Flask, render_template, jsonify, request, send_file
from camera import Camera
import json
import os

app = Flask(__name__)

# Initialize variables
cameras = []
occupancy_limit = 100
config_path = "ReloadConfig.json"

# Function to load configuration on startup
def load_config():
    global occupancy_limit
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            # Clear current cameras and load from config
            cameras.clear()
            for cam in config_data.get("cameras", []):
                new_camera = Camera(cam['ip'], cam['username'], cam['password'])
                cameras.append(new_camera)
            # Set occupancy limit from config
            occupancy_limit = config_data.get("occupancy_limit", 100)

# Function to save configuration after changes
def save_config():
    config_data = {
        "cameras": [{"ip": cam.ip, "username": cam.username, "password": cam.password} for cam in cameras],
        "occupancy_limit": occupancy_limit
    }
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

# Load configuration on app startup
load_config()

@app.route('/')
def dashboard():
    # Calculate the total currently in by summing up each camera's currently_in value
    total_currently_in = sum(camera.get_counts()[2] for camera in cameras)
    return render_template('dashboard.html', total_currently_in=total_currently_in, occupancy_limit=occupancy_limit, camera_count=len(cameras))

@app.route('/get_cameras', methods=['GET'])
def get_cameras():
    # Collect data for each camera dynamically
    camera_data = [
        {
            "entered": camera.get_counts()[0],
            "exited": camera.get_counts()[1],
            "currently_in": camera.get_counts()[2]
        }
        for camera in cameras
    ]
    # Calculate total currently in by summing each camera's currently_in value
    total_currently_in = sum(cam["currently_in"] for cam in camera_data)
    print("Camera data:", camera_data)  # Debugging: Confirm data is sent to the client
    return jsonify(cameras=camera_data, total_currently_in=total_currently_in)

@app.route('/add_camera', methods=['POST'])
def add_camera():
    ip = request.json.get('ip')
    username = request.json.get('username')
    password = request.json.get('password')
    if ip and username and password:
        new_camera = Camera(ip, username, password)
        cameras.append(new_camera)
        save_config()  # Save configuration after adding a camera
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Invalid camera details")

@app.route('/remove_camera/<int:index>', methods=['POST'])
def remove_camera(index):
    try:
        del cameras[index]
        save_config()  # Save configuration after removing a camera
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
    save_config()  # Save configuration after changing occupancy limit
    return jsonify(success=True)

@app.route('/export_config', methods=['GET'])
def export_config():
    config_data = [{"ip": cam.ip, "username": cam.username, "password": cam.password} for cam in cameras]
    config_path = "camera_config.json"
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)
    return send_file(config_path, as_attachment=True)

@app.route('/load_config', methods=['POST'])
def load_config_route():
    file = request.files.get('config_file')
    if file:
        config_data = json.load(file)
        cameras.clear()
        for cam in config_data:
            new_camera = Camera(cam['ip'], cam['username'], cam['password'])
            cameras.append(new_camera)
        save_config()  # Save configuration after loading new config
        return jsonify(success=True)
    return jsonify(success=False, error="No file provided")

# The __main__ block has been removed for Apache to handle app startup