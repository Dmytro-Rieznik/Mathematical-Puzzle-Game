import json

class CompletedLevels:
    def __init__(self):
        self.file_path = 'completed_levels.json'
        self.data = self._load_data()

    def _load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {"level": 0}

    def _save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def get_level(self):
        return self.data.get("level", 0)

    def update_level(self, level):
        if level > self.data["level"]:
            self.data["level"] = level
            self._save_data()