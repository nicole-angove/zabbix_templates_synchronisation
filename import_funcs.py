import os
import json
import logging
import sys
from config import *
from template_funcs import *


# Check if git template version is valid to import. Return True if local server version >= git template version.
def is_compatible(local_version, git_content):
    try:
        git_json = json.loads(git_content)
        template_version = git_json.get("zabbix_export", {}).get("version")
        if not template_version:
            return False
        return float(local_version) >= float(template_version)
    except Exception:
        return False


# Helper to compare two JSON strings while ignoring the 'date' field.
def has_changes(new_content, old_content):
    try:
        new_json = json.loads(new_content)
        old_json = json.loads(old_content)
        
        # Remove date fields to compare only structure and logic
        if "zabbix_export" in new_json: new_json["zabbix_export"].pop("date", None)
        if "zabbix_export" in old_json: old_json["zabbix_export"].pop("date", None)
        
        return new_json != old_json
    except:
        return True


# Import a single template.
def import_template(content, filename):
    rules = {
        'template_groups': {'createMissing': True, 'updateExisting': True},
        'templates': {'createMissing': True, 'updateExisting': True},
        'items': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False},
        'triggers': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False},
        'graphs': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False},
        'discoveryRules': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False},
        'httptests': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False},
        'valueMaps': {'createMissing': True, 'updateExisting': True, 'deleteMissing': False}
    }
    
    import_params = {
        "rules": rules,
        "source": content,
        "format": "json"
    }
    
    return zabbix_api("configuration.import", import_params, ZABBIX_API_TOKEN)


# Perform checks and import templates.
def process_imports():
    # Check API version
    local_version_full = zabbix_api("apiinfo.version", [], None)
    local_version_major = ".".join(local_version_full.split(".")[:2]) if local_version_full else "0.0"

    logging.info(f"Local Zabbix Version: {local_version_major}.")
    logging.info(f"Checking for template changes in {GIT_DIR}...")

    # List of all files in git directory
    files = [f for f in os.listdir(GIT_DIR) if f.endswith(f".json")]
    
    success_count = 0
    fail_count = 0
    skip_count = 0

    # Loop through every file in the git directory and check whether to import it
    for filename in files:
        git_template_path = os.path.join(GIT_DIR, filename)
        backup_template_path = os.path.join(BACKUP_DIR, filename)
        
        with open(git_template_path, "r") as f:
            git_template_content = f.read()
            
        # Check if the template has changes and if so, import it
        should_import = True
        if os.path.exists(backup_template_path):
            with open(backup_template_path, "r") as f:
                backup_template_content = f.read()
            if not has_changes(git_template_content, backup_template_content):
                should_import = False
        
        if should_import:
            logging.info(f"Change detected in {filename}. Importing...")
            
            # Check for version incompatibility when git version > local version
            if not is_compatible(local_version_major, git_template_content):
                err_msg = f"SKIPPING {filename}: Local version ({local_version_major}) is older than Template ({filename})."
                send_trapper_alert(err_msg)
                fail_count += 1
                continue

            # Perform check against json schema
            if validate_template(git_template_content):
                if import_template(git_template_content, filename) is not None:
                    logging.info(f"Successfully imported {filename}")
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        else:
            skip_count += 1

    logging.info(f"Import finished. Success: {success_count}, Failed: {fail_count}, Skipped (no changes): {skip_count}")

    if fail_count > 0:
        send_trapper_alert(f"Import finished with {fail_count} failures on {TRAPPER_HOST}.")

