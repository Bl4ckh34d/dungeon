import json
import sys
import os

try:
    from rich import print
    from rich.console import Console
except ImportError:
    print("The 'rich' library is not installed. Installing now...")
    os.system('pip install rich')
    from rich import print
    from rich.console import Console
try:
    import ffmpeg
except ImportError:
    print("The 'ffmpeg' library is not installed. Installing now...")
    os.system('pip install ffmpeg')
    import ffmpeg
    
console = Console()
dungeon = []
enemies = []
projectiles = []
rooms = []
secret_rooms = []
items_on_floor = {}

try:
    with open("data/player_base.json", encoding="utf-8") as f:
        player = json.load(f)
    with open("data/items.json", encoding="utf-8") as f:
        items = json.load(f)
    with open("data/enemies.json", encoding="utf-8") as f:
        enemy_types_list = json.load(f)
    with open("data/directions.json", encoding="utf-8") as f:
        directions = json.load(f)
    with open("data/effects.json", encoding="utf-8") as f:
        effects = json.load(f)
    with open("data/graphics.json", encoding="utf-8") as f:
        graphic = json.load(f)
    with open("data/settings.json", encoding="utf-8") as f:
        settings = json.load(f)
    with open("data/messages.json", encoding="utf-8") as f:
        message = json.load(f)
        
except FileNotFoundError as e:
    console.print(message["error"]["data_error"].format(error=e))
    sys.exit(1)
