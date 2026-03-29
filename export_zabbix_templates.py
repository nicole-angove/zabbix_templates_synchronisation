import os
import requests
import logging
import sys
from datetime import datetime
from config import *
from template_funcs import *


def main():
    if not HAS_JSONSCHEMA:
        err_msg = "The 'jsonschema' library is required for validation. Please run: pip3 install jsonschema"
        send_trapper_alert(err_msg)
        sys.exit(1)
    
    # Make sure the export direcory exists.
    os.makedirs(GIT_DIR, exist_ok=True)

    # Git Pull
    logging.info("Performing git pull...")
    if run_git_command(["pull"]) != 0: # returns 0 for success
        err_msg = "Git pull failed or not in a git repository."
        send_trapper_alert(err_msg)
        sys.exit(1)

    logging.info(f"Finding templates containing {EXPORT_SEARCH_STR}...")
    templates = get_templates(EXPORT_SEARCH_STR)

    # Check for no templates returned.
    if not templates:
        err_msg = f"No templates found containing {EXPORT_SEARCH_STR}."
        send_trapper_alert(err_msg)
        sys.exit(1)

    export_templates(templates, GIT_DIR)

    # Git Add
    logging.info("Staging changes in git...")
    run_git_command(["add", GIT_DIR])

    # Git Diff to check if there are any changes to commit. If changes are found, Git Commit and Git Push.
    if run_git_command(["diff", "--cached", "--quiet"]) == 1: # with --quiet option, returns 0 for no changes, 1 for changes found, >1 for errors
        logging.info("Changes detected. Committing and pushing...")
        commit_msg = f"Zabbix templates automated export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if run_git_command(["commit", "-m", commit_msg]) == 0: # returns 0 for success
            run_git_command(["push"])
            logging.info("Changes pushed.")
        else:
            err_msg = "Failed to commit"
            send_trapper_alert(err_msg)
    else:
        logging.info("No changes detected in templates. Skipping git commit.")

if __name__ == "__main__":
    main()
