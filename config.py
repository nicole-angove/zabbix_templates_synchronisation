# Configuration - add your own config here. See README for help.
ZABBIX_URL =
ZABBIX_API_TOKEN =
GIT_DIR =
BACKUP_DIR =
LOG_FILE =
TRAPPER_HOST =
TRAPPER_KEY =
ZABBIX_SERVER =
ZABBIX_TRAPPER_PORT =
EXPORT_SEARCH_STR =

# Zabbix template schema for structural validation.
TEMPLATE_SCHEMA = {
    "type": "object",
    "required": ["zabbix_export"],
    "properties": {
        "zabbix_export": {
            "type": "object",
            "required": ["version", "templates"],
            "properties": {
                "version": {"type": "string"},
                "templates": {
                    "type": "array",
                    "minItems": 1
                }
            }
        }
    }
}
