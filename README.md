# zabbix_templates_synchronisation
Python scripts for template synchronisation across multiple Zabbix servers.

This project provides a robust, automated workflow for managing Zabbix templates across multiple Zabbix servers using Git as the central "Source of Truth."

## The Workflow

   1. Source of Truth: One Zabbix server is designated as the master. Any changes to templates are made here.
   2. Automated Export: The master server runs export_zabbix_templates.py to export changed templates to a Git repository.
   3. Automated Import: Other Zabbix servers run import_zabbix_templates.py to pull the latest templates from Git and sync them to their local environment.

## Key Features

   * Only imports templates if the logic has actually changed (ignores date/metadata noise).
   * Automatically performs a full backup of all local templates before any import.
   * Prevents importing templates from a newer Zabbix version into an older server.
   * Uses jsonschema to ensure files are not corrupted before writing to disk or Zabbix.
   * Sends Zabbix Trapper alerts immediately if a script fails or an import error occurs.
   * Configured to update templates without unlinking hosts, ensuring historical monitoring data is never lost.

## Prerequisites

   * Python 3.8+
   * Zabbix 7.0+ (Optimized for 7.0 snake_case API)
   * Dependencies: pip3 install requests jsonschema
   * System Tools: git and zabbix_sender must be installed and in the system PATH.

## Project Structure

   * config.py: Centralized configuration for API URLs, tokens, and file paths.
   * template_funcs.py: Shared core logic (API wrapper, alerts, validation).
   * import_funcs.py: Logic for intelligent template comparison and synchronisation.
   * export_zabbix_templates.py: The script for the master "Source of Truth" server.
   * import_zabbix_templates.py: The script for the consumer/subscriber servers.

## Setup

  1. Zabbix Configuration

  For each server, create a Zabbix API Token (Admin role) and a Trapper Item:

   * Host Name: zabbix (Matches TRAPPER_HOST in config)
   * Item Key: export.script.status
   * Type: Zabbix Trapper
   * Type of Information: Log

  2. Script Configuration

  Edit config.py with your environment details:

   * ZABBIX_URL = "https://your-server/api_jsonrpc.php"
   * ZABBIX_API_TOKEN = "your-token"
   * GIT_DIR = "/path/to/your/templates/git/repo"
   * BACKUP_DIR = "/path/to/template/backups" # Don't forget to rotate backups
   * LOG_FILE = "/path/to/log/file" # Don't forget to rotate logs
   * TRAPPER_HOST = "host-for-trapper-in-zabbix"
   * TRAPPER_KEY = "trapper.key" # e.g. template.script.status
   * ZABBIX_SERVER = "127.0.0.1" # Destination for zabbix_sender
   * ZABBIX_TRAPPER_PORT = 10051
   * EXPORT_SEARCH_STR = "" # Opportunity to add a search string; otherwise, empty string to export all templates
   

  3. Git Repository

  Ensure the directory specified in GIT_DIR is a valid Git repository with a remote configured:

   * cd /path/to/zabbix_templates
   * git init
   * git remote add origin <your-git-url>

## Usage

  On the Master Server (Export)

  Run this via Cron (e.g., every hour) to push changes to Git:

   1. python3 export_zabbix_templates.py
   2. Make sure logs are rotating in LOG_DIR

  On Consumer Servers (Import)

  Run this via Cron (e.g., once a day) to pull updates from Git:

   1. python3 import_zabbix_templates.py
   2. Make sure logs are rotating in LOG_DIR
   3. Make sure backups are rotating in BACKUP_DIR

## Security

   * Never commit your config.py to a public repository.

