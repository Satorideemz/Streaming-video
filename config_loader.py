import json
import time
import threading

class ConfigManager:
    def __init__(self, config_files, switch_interval=10):
        self.config_files = config_files
        self.current_index = 0
        self.config = self._load_config(self.config_files[self.current_index])
        self.switch_interval = switch_interval
        self.running = True
        self.lock = threading.Lock()

        self._start_switcher_thread()

    def _load_config(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def _switch_config(self):
        while self.running:
            time.sleep(self.switch_interval)
            with self.lock:
                self.current_index = (self.current_index + 1) % len(self.config_files)
                new_config = self._load_config(self.config_files[self.current_index])
                self.config = new_config
                print(f"[CONFIG] Configuración cargada desde {self.config_files[self.current_index]}")

    def _start_switcher_thread(self):
        thread = threading.Thread(target=self._switch_config, daemon=True)
        thread.start()

    def get(self, key, default=None):
        with self.lock:
            return self.config.get(key, default)

    def stop(self):
        self.running = False
