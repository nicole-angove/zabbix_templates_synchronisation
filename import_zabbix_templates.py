import os
import logging
import sys
from config import *
from template_funcs import *
from import_funcs import *


def main():
    if not HAS_JSONSCHEMA:
        err_msg = "The 'jsonschema' library is required for validation."
        send_trapper_alert(err_msg)
        sys.exit(1)

    # Make sure the export direcory exists.
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Git Pull.
    logging.info("Performing git pull...")
    if run_git_command(["pull"]) != 0: # returns 0 for success
        err_msg = "Git pull failed or not in a git repository."
        send_trapper_alert(err_msg)
        sys.exit(1)

    # Back up all existing templates.
    backup_templates = get_templates("")

    # Check for no templates returned.
    if not backup_templates:
        err_msg = f"No templates found to back up."
        send_trapper_alert(err_msg)
        sys.exit(1)

    export_templates(backup_templates, BACKUP_DIR)

    process_imports()

if __name__ == "__main__":
    main()
