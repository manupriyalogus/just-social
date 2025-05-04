import json
import os
import appdirs

class Config:
    def __init__(self):
        self.app_name = "WhatsAppClone"
        self.config_dir = appdirs.user_config_dir(self.app_name)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config = self.load_config()

    def load_config(self):
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Load existing config or create default
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_config()
        else:
            return self.get_default_config()

    def get_default_config(self):
        return {
            'theme': 'light',
            'notifications': {
                'enabled': True,
                'sound': True,
                'preview': True
            },
            'privacy': {
                'read_receipts': True,
                'last_seen': True,
                'typing_indicator': True
            },
            'storage': {
                'download_location': os.path.expanduser("~/Downloads"),
                'auto_download_media': True
            }
        }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()