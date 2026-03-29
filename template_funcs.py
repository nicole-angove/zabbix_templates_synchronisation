import os
import json
import requests
import logging
import sys
import subprocess
from config import *


# Try to import jsonschema for validation.
try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# Set up logging.
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)


# Generic zabbix API call.
def zabbix_api(method, params, auth):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth,
    }

    headers = {"Content-Type": "application/json-rpc"}

    try:
        response = requests.post(ZABBIX_URL, data=json.dumps(payload), headers=headers)
        data = response.json()

        if "error" in data:
            err_msg = f"Error details: {data['error']}"
            send_trapper_alert(err_msg)
            return None
        return data.get("result")
    except Exception as e:
        err_msg = f"API Request failed: {e}"
        send_trapper_alert(err_msg)
        sys.exit(1)


# Validate template structure against JSON schema.
def validate_template(template_content):
    try:
        data = json.loads(template_content)
        validate(instance=data, schema=TEMPLATE_SCHEMA)
        return True
    except json.JSONDecodeError as e:
        logging.error(f"Exported content is not valid JSON: {e}")
        return False
    except ValidationError as e:
        logging.error(f"Template failed schema validation: {e.message}")
        return False


# Use zabbix_sender command to send an alert.
def send_trapper_alert(message):
    logging.error(f"Sending trapper alert: {message}")

    cmd = [
        "zabbix_sender",
        "-z", ZABBIX_SERVER,
        "-p", str(ZABBIX_TRAPPER_PORT),
        "-s", TRAPPER_HOST,
        "-k", TRAPPER_KEY,
        "-o", message
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logging.info(f"zabbix_sender successful: {result.stdout.strip()}")
        else:
            logging.error(f"zabbix_sender failed with exit code {result.returncode}")
    except Exception as e:
        logging.error(f"An error occurred while running zabbix_sender: {e}")


# Run generic git command.
def run_git_command(args):
    cmd = ["git"] + args
    result = subprocess.run(cmd, cwd=GIT_DIR, capture_output=True)
    return result.returncode


# Return a list of templateids and template names.
def get_templates(search_str):
    params = {
        "output": ["templateid", "name"],
        "search": {"name": search_str},
        "startSearch": True
    }

    return zabbix_api("template.get", params, ZABBIX_API_TOKEN)


# Export a template after doing some checks. 
def export_template(template_id, template_name, export_dir):
        filename = f"{template_name}.json"
        file_path = os.path.join(export_dir, filename)

        # Export configuration
        export_params = {
            "options": {"templates": [template_id]},
            "format": "json"
        }

        template_content = zabbix_api("configuration.export", export_params, ZABBIX_API_TOKEN)

        if template_content:
            try:
                if validate_template(template_content):
                    with open(file_path, "w") as f:
                        f.write(template_content)
                    logging.info(f"Saved to {file_path}")
                else:
                    err_msg = f"Template targeting {file_path} failed to validate and will not be written."
                    send_trapper_alert(err_msg)
            except IOError as e:
                err_msg = f"Failed to write file {file_path}: {e}"
                send_trapper_alert(err_msg)
        else:
            return


# Export templates one at a time.
def export_templates(templates, export_dir):
    for template in templates:
        template_id = template["templateid"]
        template_name = template["name"]
        export_template(template_id, template_name, export_dir)
