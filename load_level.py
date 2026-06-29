import json


class LoadLevel:
    def __init__(self, level_id):

        self.level_id = None
        self.level_data = None
        self.combinators = None
        self.output = None
        self.inputs = None
        self.bridge = None
        self.map_size = None
        self.textures_for_frame = None
        self.textures_for_map = None

        self.load_textures()
        self.load_level(level_id)

    def load_level(self, level_id):
        try:
            with open('levels.json', 'r') as f:
                data = json.load(f)
                levels = data.get('levels', [])

                if level_id < 0 or level_id >= len(levels):
                    print(f"Error: level_id {level_id} is out of range. Using default values.")
                    self.set_default()
                    return

                self.level_data = levels[level_id]
                self.level_id = self.level_data.get('id', 0)
                self.combinators = self.level_data.get('combinators', [])
                self.output = self.level_data.get('output', {})
                self.inputs = self.level_data.get('inputs', [])
                self.bridge = self.level_data.get('bridge', 0)
                self.map_size = self.level_data.get('mapSize', {'rows': 0, 'columns': 0})

        except FileNotFoundError:
            print("The levels file was not found. Using default values.")
            self.set_default()
        except json.JSONDecodeError:
            print("Error decoding JSON from the levels file. Using default values.")
            self.set_default()
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Using default values.")
            self.set_default()

    def load_textures(self):
        self.textures_for_frame = [
            {"sprite": "images/textures_for_frame/plus.png"},
            {"sprite": "images/textures_for_frame/minus.png"},
            {"sprite": "images/textures_for_frame/multiply.png"},
            {"sprite": "images/textures_for_frame/divide.png"},
            {"sprite": "images/textures_for_frame/degree.png"},
            {"sprite": "images/textures_for_frame/root.png"},
            {"sprite": "images/textures_for_frame/degree_3.png"},
            {"sprite": "images/textures_for_frame/root_3.png"}
        ]
        self.textures_for_map = [
            {"sprite": "images/textures_for_map/plus.png"},
            {"sprite": "images/textures_for_map/minus.png"},
            {"sprite": "images/textures_for_map/multiply.png"},
            {"sprite": "images/textures_for_map/divide.png"},
            {"sprite": "images/textures_for_map/degree.png"},
            {"sprite": "images/textures_for_map/root.png"},
            {"sprite": "images/textures_for_map/degree_3.png"},
            {"sprite": "images/textures_for_map/root_3.png"}
        ]

    def set_default(self):
        self.level_id = 0
        self.combinators = [
            {"type": "plus", "count": 0},
            {"type": "minus", "count": 0},
            {"type": "multiply", "count": 0},
            {"type": "divide", "count": 0},
            {"type": "degree", "count": 0},
            {"type": "root", "count": 0},
            {"type": "degree_3", "count": 0},
            {"type": "root_3", "count": 0}
        ]
        self.output = {"x": 0, "y": 0, "target_value": 0}
        self.inputs = []
        self.bridge = 0
        self.map_size = {"rows": 1, "columns": 1}