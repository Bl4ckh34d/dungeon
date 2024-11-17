import random
import vars

class BSPNode:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left = None
        self.right = None
        self.room = None

    def split(self, min_size):
        """Split the node into two children."""
        if self.left or self.right:
            return False  # Already split

        split_horizontally = random.choice([True, False])
        max_split = (self.height if split_horizontally else self.width) - min_size

        if max_split <= min_size:
            return False

        split = random.randint(min_size, max_split)

        if split_horizontally:
            self.left = BSPNode(self.x, self.y, self.width, split)
            self.right = BSPNode(self.x, self.y + split, self.width, self.height - split)
        else:
            self.left = BSPNode(self.x, self.y, split, self.height)
            self.right = BSPNode(self.x + split, self.y, self.width - split, self.height)

        return True

    def create_room(self, padding=vars.settings["padding"]):
        """
        Create a room within this node's boundaries.
        Padding defines the minimum distance between the room and the edges of the BSP cell.
        """
        # Ensure there's enough space for padding on all sides
        if self.width <= 2 * padding or self.height <= 2 * padding:
            return None

        # Define room size within the available space
        room_width = random.randint(4, self.width - 2 * padding)
        room_height = random.randint(4, self.height - 2 * padding)

        # Define room position within the padded area
        room_x = random.randint(self.x + padding, self.x + self.width - room_width - padding)
        room_y = random.randint(self.y + padding, self.y + self.height - room_height - padding)

        # Decide if this room should be a secret room
        is_secret_room = random.random() < vars.settings["secret_room_chance"]
        
        room = {
            'x': room_x,
            'y': room_y,
            'width': room_width,
            'height': room_height,
            'is_secret': is_secret_room
        }

        # If it's a secret room, add it to the secret_rooms list
        if is_secret_room:
            vars.secret_rooms.append(room)
        else:
            vars.rooms.append(room)

        # Store the room in the node
        self.room = room
        return room

def get_all_leaves(node):
    """Retrieve all leaf nodes from a BSP tree."""
    if not node.left and not node.right:
        return [node]
    leaves = []
    if node.left:
        leaves.extend(get_all_leaves(node.left))
    if node.right:
        leaves.extend(get_all_leaves(node.right))
    return leaves


# Dungeon Generation Functions
def generate_dungeon(player):
    vars.dungeon = [[vars.graphic["wall_char"] for _ in range(vars.settings["dungeon_width"])] for _ in range(vars.settings["dungeon_height"])]
    vars.enemies = []
    vars.rooms = []
    vars.secret_rooms = []
    vars.items_on_floor = {}
    vars.player['shops_visited'] = set()  # Reset shops visited on new floor

    # Carve out rooms and corridors
    make_map()

    # Place player in the first room
    first_room = vars.rooms[0]
    player['pos'] = [first_room['y'] + first_room['height'] // 2, first_room['x'] + first_room['width'] // 2]

    # Place exit in the last room
    last_room = vars.rooms[-1]
    exit_x = last_room['x'] + last_room['width'] // 2
    exit_y = last_room['y'] + last_room['height'] // 2
    vars.dungeon[exit_y][exit_x] = vars.graphic["exit_char"]

    # Adjust item and enemy counts based on floor
    floor_multiplier = player['floor']
    max_floor = 10
    if player['floor'] == max_floor:
        num_treasures = 5
        num_items = 5
        num_enemies = 40
    else:
        num_treasures = max(3, 8 - floor_multiplier)
        num_items = max(2, 5 - floor_multiplier)
        num_enemies = min(10 + floor_multiplier * 2, 30)

    # Place treasures, items, enemies, and shops
    place_random_items(vars.graphic["treasure_char"], num_treasures, rare=True)
    place_random_items(vars.graphic["item_char"], num_items, rare=True)
    place_enemies(num_enemies)
    if random.random() < 0.5 and player['floor'] != max_floor:
        place_shop()

    # Place secret rooms with 33% chance
    if random.random() < 0.33:
        create_secret_rooms()
        
def make_map():
    root = BSPNode(0, 0, vars.settings["dungeon_width"], vars.settings["dungeon_height"])
    nodes = [root]
    min_size = vars.settings["min_room_size"]

    while nodes:
        node = nodes.pop(0)
        if node.split(min_size):
            nodes.append(node.left)
            nodes.append(node.right)

    rooms = []
    leaf_nodes = [node for node in get_all_leaves(root)]
    for node in leaf_nodes:
        room = node.create_room()
        if room:
            if not all(k in room for k in ['x', 'y', 'width', 'height']):
                continue
            rooms.append(room)
            create_room(room)

    if not rooms:
        fallback_room = {'x': 5, 'y': 5, 'width': 10, 'height': 10}
        rooms.append(fallback_room)
        create_room(fallback_room)

    for i in range(1, len(rooms)):
        connect_rooms(rooms[i - 1], rooms[i])
    vars.rooms = rooms

def create_secret_rooms():
    """Create secret rooms and connect them to the main dungeon."""
    num_secret_rooms = random.randint(1, 3)
    for _ in range(num_secret_rooms):
        attempts = 0
        while attempts < 100:
            w = random.randint(4, 6)
            h = random.randint(4, 6)
            x = random.randint(1, vars.settings["dungeon_width"] - w - 2)
            y = random.randint(1, vars.settings["dungeon_height"] - h - 2)

            secret_room = {'x': x, 'y': y, 'width': w, 'height': h}

            # Check for overlap
            if any(rooms_overlap(secret_room, other_room) for other_room in vars.rooms + vars.secret_rooms):
                attempts += 1
                continue

            create_secret_room(secret_room)

            # Connect the secret room to a random room via a secret door
            target_room = random.choice(vars.rooms)
            connect_secret_room(secret_room, target_room)

            # Place stronger enemy and loot in the secret room
            place_strong_enemy(secret_room)
            place_secret_room_items(secret_room)

            vars.secret_rooms.append(secret_room)
            break

def create_secret_room(room):
    """Carve out the secret room with solid walls until revealed."""
    for x in range(room['x'], room['x'] + room['width']):
        for y in range(room['y'], room['y'] + room['height']):
            vars.dungeon[y][x] = vars.graphic["wall_char"]  # Render as wall initially

def connect_secret_room(secret_room, target_room):
    """Connect a secret room to a normal room via a secret door."""
    x1, y1 = secret_room['x'] + secret_room['width'] // 2, secret_room['y'] + secret_room['height'] // 2
    x2, y2 = target_room['x'] + target_room['width'] // 2, target_room['y'] + target_room['height'] // 2

    # Generate an L-shaped path
    if random.choice([True, False]):
        create_h_tunnel(x1, x2, y1)
        create_v_tunnel(y1, y2, x2)
    else:
        create_v_tunnel(y1, y2, x1)
        create_h_tunnel(x1, x2, y2)

    # Place a secret door
    vars.dungeon[y2][x2] = vars.graphic["secret_door_char"]
            
def place_strong_enemy(room):
    """Place a strong enemy in the given room."""
    from enemy import Enemy

    # Calculate the position at the center of the room
    x = room['x'] + room['width'] // 2
    y = room['y'] + room['height'] // 2

    # Select a strong enemy based on the floor level
    enemy_type = select_strong_enemy_type()
    enemy = Enemy(enemy_type, y, x)
    vars.enemies.append(enemy)

def select_strong_enemy_type():
    """Select a strong enemy type based on the floor level."""
    floor = vars.player['floor']
    suitable_enemies = [et for et in vars.enemy_types_list if et['base_health'] >= 15 + floor * 2]
    if not suitable_enemies:
        suitable_enemies = vars.enemy_types_list  # Default to all enemies if no suitable ones are found
    return random.choice(suitable_enemies)

def place_secret_room_items(room):
    """Place items in a secret room."""
    num_items = random.randint(1, 2)
    for _ in range(num_items):
        attempts = 0
        while attempts < 100:
            x = random.randint(room['x'] + 1, room['x'] + room['width'] - 2)
            y = random.randint(room['y'] + 1, room['y'] + room['height'] - 2)

            # Ensure placement on a secret floor tile
            if vars.dungeon[y][x] == vars.graphic["secret_floor_char"]:
                vars.dungeon[y][x] = vars.graphic["item_char"]
                item = random.choice([item for item in vars.items if item['type'] in ['weapon', 'armor', 'accessory']])
                vars.items_on_floor[(y, x)] = item  # Store the item in the items_on_floor dictionary
                break
            attempts += 1

def rooms_overlap(room1, room2):
    """Check if two rooms overlap."""
    required_keys = ['x', 'y', 'width', 'height']
    for key in required_keys:
        if key not in room1 or key not in room2:
            return False

    return (room1['x'] <= room2['x'] + room2['width'] - 1 and
            room1['x'] + room1['width'] - 1 >= room2['x'] and
            room1['y'] <= room2['y'] + room2['height'] - 1 and
            room1['y'] + room1['height'] - 1 >= room2['y'])

def create_room(room):
    """Carve out a room in the dungeon."""
    for x in range(room['x'], room['x'] + room['width']):
        for y in range(room['y'], room['y'] + room['height']):
            if room.get('is_secret'):
                vars.dungeon[y][x] = vars.graphic["wall_char"]  # Render secret rooms as walls initially
            else:
                vars.dungeon[y][x] = vars.graphic["floor_char"]

def connect_rooms(room1, room2):
    """Connect two rooms with straight horizontal and vertical corridors."""
    x1, y1 = room1['x'] + room1['width'] // 2, room1['y'] + room1['height'] // 2
    x2, y2 = room2['x'] + room2['width'] // 2, room2['y'] + room2['height'] // 2

    # Create an L-shaped connection: horizontal then vertical or vertical then horizontal
    if random.choice([True, False]):
        # Horizontal first
        create_h_tunnel(x1, x2, y1)
        create_v_tunnel(y1, y2, x2)
    else:
        # Vertical first
        create_v_tunnel(y1, y2, x1)
        create_h_tunnel(x1, x2, y2)

    # Place a secret door if one of the rooms is secret
    if room1.get('is_secret') or room2.get('is_secret'):
        vars.dungeon[y2][x2] = vars.graphic["secret_door_char"]

def create_h_tunnel(x1, x2, y):
    """Create a horizontal tunnel."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        vars.dungeon[y][x] = vars.graphic["floor_char"]  # Use floor_char for normal hallways

def create_v_tunnel(y1, y2, x):
    """Create a vertical tunnel."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        vars.dungeon[y][x] = vars.graphic["floor_char"]  # Use floor_char for normal hallways

def place_random_items(symbol, count, rare=False):
    for _ in range(count):
        attempts = 0
        while attempts < 100:
            x = random.randint(1, vars.settings["dungeon_width"] - 2)
            y = random.randint(1, vars.settings["dungeon_height"] - 2)
            if vars.dungeon[y][x] == vars.graphic["floor_char"] and [y, x] != vars.player['pos']:
                if symbol == vars.graphic["item_char"]:
                    if rare and random.random() < 0.1:
                        item = random.choice([item for item in vars.items if item['type'] in ['weapon', 'armor', 'accessory']])
                    else:
                        # Exclude 'Scroll of Identify' from random selection
                        item = random.choice([item for item in vars.items if item['type'] not in ['weapon', 'armor', 'accessory', 'scroll']])
                    vars.dungeon[y][x] = vars.graphic["item_char"]
                    vars.items_on_floor[(y, x)] = item  # Store the item in the items_on_floor dictionary
                else:
                    vars.dungeon[y][x] = symbol
                break
            attempts += 1

def place_enemies(num_enemies):
    from enemy import Enemy
    
    for _ in range(num_enemies):
        attempts = 0
        while attempts < 100:
            x = random.randint(1, vars.settings["dungeon_width"] - 2)
            y = random.randint(1, vars.settings["dungeon_height"] - 2)
            if (vars.dungeon[y][x] != vars.graphic["wall_char"] and
                vars.dungeon[y][x] != vars.graphic["secret_wall_char"] and
                not any(e.pos == [y, x] for e in vars.enemies) and
                [y, x] != vars.player['pos']):
                enemy_type = select_enemy_type()
                enemy = Enemy(enemy_type, y, x)
                vars.enemies.append(enemy)
                break
            attempts += 1

def select_enemy_type():
    floor = vars.player['floor']
    # Filter enemies based on floor
    if floor == 1:
        weak_enemies = [et for et in vars.enemy_types_list if et['base_health'] <= 10]
        return random.choice(weak_enemies)
    else:
        # Increase enemy strength with floor
        suitable_enemies = [et for et in vars.enemy_types_list if et['base_health'] <= 10 + floor * 5]
        return random.choice(suitable_enemies)

def place_shop():
    attempts = 0
    while attempts < 100:
        x = random.randint(1, vars.settings["dungeon_width"] - 2)
        y = random.randint(1, vars.settings["dungeon_height"] - 2)
        if (vars.dungeon[y][x] == vars.graphic["floor_char"] and
            not any(e.pos == [y, x] for e in vars.enemies) and
            [y, x] != vars.player['pos']):
            vars.dungeon[y][x] = vars.graphic["shop_char"]
            break
        attempts += 1

def reveal_secret_room(secret_door_pos):
    
    from utils import room_contains_tile
    
    """Reveal the secret room and its connected hallway."""
    for room in vars.secret_rooms:
        if room_contains_tile(room, secret_door_pos):
            # Reveal the room tiles
            for x in range(room['x'], room['x'] + room['settings["dungeon_width"]']):
                for y in range(room['y'], room['y'] + room['settings["dungeon_height"]']):
                    vars.dungeon[y][x] = vars.graphic["floor_char"]
                    # Reveal items
                    if (y, x) in vars.items_on_floor:
                        vars.dungeon[y][x] = vars.graphic["item_char"]
                    # Reveal enemies
                    for enemy in vars.enemies:
                        if enemy.pos == [y, x]:
                            vars.dungeon[y][x] = enemy.symbol
            break

def connect_to_hallway(secret_door_pos, room):
    
    from utils import get_line
    
    """Reveals the hallway connecting the door to the center of the secret room."""
    path = get_line(secret_door_pos[1], secret_door_pos[0],
                    room['x'] + room['settings["dungeon_width"]'] // 2,
                    room['y'] + room['settings["dungeon_height"]'] // 2)
    for x, y in path:
        vars.dungeon[y][x] = vars.graphic["floor_char"]