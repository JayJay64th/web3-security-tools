import json
import os
import re
import time


class Cache:
    def __init__(self, directory, enabled=True):
        self.directory = directory
        self.enabled = enabled
        if enabled:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _path(directory, key):
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", key)
        return os.path.join(directory, safe + ".json")

    def get(self, key, max_age_hours=24):
        if not self.enabled:
            return None
        path = self._path(self.directory, key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                envelope = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        age = time.time() - envelope.get("ts", 0)
        if max_age_hours and age > max_age_hours * 3600:
            return None
        return envelope.get("data")

    def set(self, key, data):
        if not self.enabled:
            return
        path = self._path(self.directory, key)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "data": data}, f)
        os.replace(tmp, path)
