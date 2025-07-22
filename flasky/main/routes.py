from flask import Blueprint, Response, redirect
from flasky.utils import utilities
from flask import current_app
from flask import jsonify
from collections import deque
from flasky.config import Config

main = Blueprint('main', __name__)

@main.route("/", methods=['GET'])
def home():
    return jsonify(current_app.config['MIST_OBJ'].data)

@main.route("/api", methods=['GET'])
def home_api():
    return jsonify(current_app.config['MIST_OBJ'].data)

@main.route('/api/logs/', defaults={'lines': 100})
@main.route("/api/logs/<int:lines>", methods=['GET'])
def logs(lines=100):
    try:
        with open('/tmp/misty.log', 'r') as f:
            last_x_lines = deque(f, maxlen=lines)
        content = "".join(last_x_lines)
        return Response(content, mimetype='text/plain')
    except FileNotFoundError:
        return Response("File not found.", status=404)
    except Exception as e:
        return Response(f"An error occurred: {str(e)}", status=500)

@main.route("/api/reload_data", methods=['GET'])
def reload_data():
    current_app.config['MIST_OBJ'].reload_data()
    return current_app.config['MIST_OBJ'].data

@main.route("/api/create_networks", methods=['GET'])
def create_networks():
    return current_app.config['MIST_OBJ'].create_networks()

@main.route("/api/delete_networks", methods=['GET'])
def delete_networks():
    return current_app.config['MIST_OBJ'].delete_networks()

@main.route("/api/create_sites", methods=['GET'])
def create_sites():
    return current_app.config['MIST_OBJ'].create_sites()

@main.route("/api/delete_sites", methods=['GET'])
def delete_sites():
    return current_app.config['MIST_OBJ'].delete_sites()

@main.route("/api/create_site_variables", methods=['GET'])
def create_site_variables():
    return current_app.config['MIST_OBJ'].create_site_variables()

@main.route("/api/assign_devices", methods=['GET'])
def assign_devices():
    return current_app.config['MIST_OBJ'].assign_devices()

@main.route("/api/unassign_devices", methods=['GET'])
def unassign_devices():
    return current_app.config['MIST_OBJ'].unassign_devices()

@main.route("/api/create_applications", methods=['GET'])
def create_applications():
    return current_app.config['MIST_OBJ'].create_applications()

@main.route("/api/delete_applications", methods=['GET'])
def delete_applications():
    return current_app.config['MIST_OBJ'].delete_applications()

@main.route("/api/create_vpns", methods=['GET'])
def create_vpns():
    return current_app.config['MIST_OBJ'].create_vpns()

@main.route("/api/delete_vpns", methods=['GET'])
def delete_vpns():
    return current_app.config['MIST_OBJ'].delete_vpns()

@main.route("/api/create_hub_profiles", methods=['GET'])
def create_hub_profiles():
    return current_app.config['MIST_OBJ'].create_hub_profiles()

@main.route("/api/delete_hub_profiles", methods=['GET'])
def delete_hub_profiles():
    return current_app.config['MIST_OBJ'].delete_hub_profiles()

@main.route("/api/create_wan_edge_templates", methods=['GET'])
def create_wan_edge_templates():
    return current_app.config['MIST_OBJ'].create_wan_edge_templates()

@main.route("/api/delete_wan_edge_templates", methods=['GET'])
def delete_wan_edge_templates():
    return current_app.config['MIST_OBJ'].delete_wan_edge_templates()

@main.route("/api/create_switch_templates", methods=['GET'])
def create_switch_templates():
    return current_app.config['MIST_OBJ'].create_switch_templates()

@main.route("/api/delete_switch_templates", methods=['GET'])
def delete_switch_templates():
    return current_app.config['MIST_OBJ'].delete_switch_templates()

@main.route("/api/create_wlan_templates", methods=['GET'])
def create_wlan_templates():
    return current_app.config['MIST_OBJ'].create_wlan_templates()

@main.route("/api/delete_wlan_templates", methods=['GET'])
def delete_wlan_templates():
    return current_app.config['MIST_OBJ'].delete_wlan_templates()

@main.route("/api/create_wlans", methods=['GET'])
def create_wlans():
    return current_app.config['MIST_OBJ'].create_wlans()

@main.route("/api/delete_wlans", methods=['GET'])
def delete_wlans():
    return current_app.config['MIST_OBJ'].delete_wlans()

@main.route("/api/create_psks", methods=['GET'])
def create_psks():
    return current_app.config['MIST_OBJ'].create_psks()

@main.route("/api/delete_psks", methods=['GET'])
def delete_psks():
    return current_app.config['MIST_OBJ'].delete_psks()

@main.route("/api/create_all", methods=['GET'])
def create_all():
    return current_app.config['MIST_OBJ'].create_all()

@main.route("/api/delete_all", methods=['GET'])
def delete_all():
    return current_app.config['MIST_OBJ'].delete_all()