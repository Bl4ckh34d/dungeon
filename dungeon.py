import random
import vars
from rich.console import Console
from rich.text import Text
from utils import clear_screen, format_visualization_line
# Initialize the rich console
console = Console()

def print_dungeon_ascii(dungeon, nodes=None, title="BSP Splitting"):
    """Visualize the dungeon as ASCII art in the terminal with colors."""
    clear_screen()  # Clear the screen before printing
    console.print(format_visualization_line(title))

    dungeon_height = len(dungeon)
    dungeon_width = len(dungeon[0]) if dungeon else 0

    dungeon_copy = [[cell for cell in row] for row in dungeon]

    if nodes:
        # Assign a unique color for each node
        node_colors = [
            "red", "green", "blue", "yellow", "magenta", "cyan", "white",
            "bright_red", "bright_green", "bright_blue", "bright_yellow",
            "bright_magenta", "bright_cyan", "bright_white"
        ]
        node_mapping = {
            id(node): node_colors[i % len(node_colors)] for i, node in enumerate(nodes)
        }

        # Overlay the active nodes
        for node in nodes:
            color = node_mapping[id(node)]
            for y in range(node.y, node.y + node.height):
                for x in range(node.x, node.x + node.width):
                    dungeon_copy[y][x] = f"[{color}]█[/]"  # Color for active splits

    # Print the dungeon with updated visual distinctions
    for row in dungeon_copy:
        console.print("".join(row))

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

    def create_room(self, padding=vars.settings["padding"], visualizing=vars.settings["debug"]):
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

        # Temporarily visualize the room as dark grey if in visualization mode
        if visualizing:
            create_room(room, visualizing=vars.settings["debug"])
        else:
            create_room(room)

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
    make_map(visualize_split=vars.settings["debug"])

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
        
def make_map(visualize_split=vars.settings["debug"]):
    root = BSPNode(0, 0, vars.settings["dungeon_width"], vars.settings["dungeon_height"])
    nodes = [root]
    min_size = vars.settings["min_room_size"]

    # Initialize the dungeon
    vars.dungeon = [[vars.graphic["wall_char"] for _ in range(vars.settings["dungeon_width"])]
                    for _ in range(vars.settings["dungeon_height"])]
    
    if visualize_split:
        print_dungeon_ascii(vars.dungeon, [root], title="Initial BSP Node")
        input("Press Enter to proceed...")

    # Split nodes
    while nodes:
        node = nodes.pop(0)
        if node.split(min_size):
            nodes.append(node.left)
            nodes.append(node.right)
            if visualize_split:
                print_dungeon_ascii(vars.dungeon, nodes, title="BSP Splitting in Progress")
                input("Press Enter to proceed...")

    # Create rooms
    rooms = []
    leaf_nodes = [node for node in get_all_leaves(root)]
    for i, node in enumerate(leaf_nodes):
        room = node.create_room(visualizing=vars.settings["debug"])
        if room:
            rooms.append(room)
            create_room(room, visualizing=vars.settings["debug"])
            if visualize_split:
                print_dungeon_ascii(vars.dungeon, title=f"Room {i+1} Placement")
                input("Press Enter to proceed...")

    # Maybe add a single secret room
    if random.random() < vars.settings["secret_room_chance"]:
        create_single_secret_room(rooms)

    if visualize_split:
        print_dungeon_ascii(vars.dungeon, title="Final Room Layout Before Hallways")
        input("Press Enter to proceed...")

    # Connect rooms efficiently
    connect_all_rooms(rooms)

    vars.rooms = rooms

def create_single_secret_room(existing_rooms):
    """Create a single secret room and connect it to the nearest suitable room."""
    attempts = 0
    while attempts < 100:
        w = random.randint(4, 6)
        h = random.randint(4, 6)
        x = random.randint(1, vars.settings["dungeon_width"] - w - 2)
        y = random.randint(1, vars.settings["dungeon_height"] - h - 2)

        secret_room = {'x': x, 'y': y, 'width': w, 'height': h, 'is_secret': True}

        # Check for overlap with existing rooms
        if any(rooms_overlap(secret_room, other_room) for other_room in existing_rooms + vars.secret_rooms):
            attempts += 1
            continue

        # Create the secret room
        create_secret_room(secret_room)

        # Find the nearest regular room
        nearest_room = find_nearest_room(secret_room, existing_rooms)
        
        # Connect to the nearest room
        connect_secret_room(secret_room, nearest_room)

        # Place items and enemies
        place_strong_enemy(secret_room)
        place_secret_room_items(secret_room)

        # Clear existing secret rooms (should be empty anyway) and add this one
        vars.secret_rooms = [secret_room]
        break

def find_nearest_room(target_room, rooms):
    """Find the nearest regular room to the target room."""
    nearest = None
    min_dist = float('inf')
    
    for room in rooms:
        # Calculate distance between room centers
        dist = abs((target_room['x'] + target_room['width']//2) - 
                  (room['x'] + room['width']//2)) + \
               abs((target_room['y'] + target_room['height']//2) - 
                  (room['y'] + room['height']//2))
        if dist < min_dist:
            min_dist = dist
            nearest = room
            
    return nearest

def create_secret_room(room):
    """Create a secret room with wall tiles."""
    for x in range(room['x'], room['x'] + room['width']):
        for y in range(room['y'], room['y'] + room['height']):
            # During visualization, show as dark grey
            if vars.settings["debug"]:
                vars.dungeon[y][x] = "[#222222]█[/]"
            else:
                # During gameplay, show as wall
                vars.dungeon[y][x] = vars.graphic["wall_char"]

def create_secret_room(room):
    """Carve out the secret room with solid walls until revealed."""
    for x in range(room['x'], room['x'] + room['width']):
        for y in range(room['y'], room['y'] + room['height']):
            vars.dungeon[y][x] = vars.graphic["wall_char"]  # Render as wall initially

def connect_all_rooms(rooms):
    """Connect all rooms using an efficient spanning tree approach."""
    if not rooms:
        return

    # Create a list of all possible connections between rooms
    connections = []
    for i, room1 in enumerate(rooms):
        for j, room2 in enumerate(rooms[i+1:], i+1):
            dist = manhattan_distance(room1, room2)
            # Store as a tuple with distance first for proper sorting
            connections.append((dist, i, j, room1, room2))

    # Sort connections by distance
    connections.sort()

    # Keep track of connected room groups using lists instead of sets
    connected_groups = [[room] for room in rooms]

    # Connect rooms using a minimum spanning tree approach
    for dist, i, j, room1, room2 in connections:
        # Find the groups containing these rooms
        group1 = next(g for g in connected_groups if room1 in g)
        group2 = next(g for g in connected_groups if room2 in g)

        # If rooms are in different groups, connect them
        if group1 is not group2:
            # Create corridor only if path doesn't intersect other rooms
            if not path_intersects_rooms(room1, room2, rooms):
                connect_rooms(room1, room2)
                # Merge the groups by extending group1 with group2's rooms
                group1.extend(group2)
                connected_groups.remove(group2)

def manhattan_distance(room1, room2):
    """Calculate Manhattan distance between room centers."""
    x1 = room1['x'] + room1['width'] // 2
    y1 = room1['y'] + room1['height'] // 2
    x2 = room2['x'] + room2['width'] // 2
    y2 = room2['y'] + room2['height'] // 2
    return abs(x1 - x2) + abs(y1 - y2)

def path_intersects_rooms(room1, room2, all_rooms):
    """Check if a potential path between rooms would intersect other rooms."""
    # Get room centers
    x1 = room1['x'] + room1['width'] // 2
    y1 = room1['y'] + room1['height'] // 2
    x2 = room2['x'] + room2['width'] // 2
    y2 = room2['y'] + room2['height'] // 2

    # Create a set of points along the potential path
    path_points = set()
    
    # Add points for L-shaped path
    for x in range(min(x1, x2), max(x1, x2) + 1):
        path_points.add((x, y1))
    for y in range(min(y1, y2), max(y1, y2) + 1):
        path_points.add((x2, y))

    # Check if path intersects any room (except room1 and room2)
    for room in all_rooms:
        if room is room1 or room is room2:
            continue
            
        # Expand room bounds slightly to prevent corridors from being too close
        for x in range(room['x'] - 1, room['x'] + room['width'] + 1):
            for y in range(room['y'] - 1, room['y'] + room['height'] + 1):
                if (x, y) in path_points:
                    return True
                    
    return False

def connect_secret_room(secret_room, target_room):
    """Connect a secret room to a normal room via a secret door."""
    # Find closest points between rooms
    closest_points = find_closest_room_points(secret_room, target_room)
    if closest_points:
        (x1, y1), (x2, y2) = closest_points
    else:
        # Fallback to room centers if closest points cannot be found
        x1 = secret_room['x'] + secret_room['width'] // 2
        y1 = secret_room['y'] + secret_room['height'] // 2
        x2 = target_room['x'] + target_room['width'] // 2
        y2 = target_room['y'] + target_room['height'] // 2

    # Create the corridor (hidden initially)
    if random.choice([True, False]):
        create_h_tunnel(x1, x2, y1, is_secret=True)
        create_v_tunnel(y1, y2, x2, is_secret=True)
    else:
        create_v_tunnel(y1, y2, x1, is_secret=True)
        create_h_tunnel(x1, x2, y2, is_secret=True)

    # Place the secret door at the connection point with the target room
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
    suitable_enemies = [et for et in vars.enemy_types_list if et['base_max_health'] >= 15 + floor * 2]
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

def create_room(room, visualizing=False):
    """Carve out a room in the dungeon."""
    for x in range(room['x'], room['x'] + room['width']):
        for y in range(room['y'], room['y'] + room['height']):
            if room.get('is_secret') and visualizing:
                # Display secret rooms in dark grey temporarily
                vars.dungeon[y][x] = "[#222222]█[/]"
            elif room.get('is_secret'):
                # During gameplay, secret rooms are rendered as walls
                vars.dungeon[y][x] = vars.graphic["wall_char"]
            else:
                # Regular room floors
                vars.dungeon[y][x] = vars.graphic["floor_char"]

def connect_rooms(room1, room2, visualizing=vars.settings["debug"]):
    """Connect two rooms using an improved pathfinding approach that considers existing rooms and corridors."""
    # Get center points of both rooms
    x1, y1 = room1['x'] + room1['width'] // 2, room1['y'] + room1['height'] // 2
    x2, y2 = room2['x'] + room2['width'] // 2, room2['y'] + room2['height'] // 2
    
    # Find the closest points between rooms instead of using center points
    closest_points = find_closest_room_points(room1, room2)
    if closest_points:
        (x1, y1), (x2, y2) = closest_points

    # Track visualized tiles for debugging
    visualized_tiles = []
    
    # Try to find doorway points on room edges
    door1 = find_door_point(room1, x2, y2)
    door2 = find_door_point(room2, x1, y1)
    
    if door1 and door2:
        x1, y1 = door1
        x2, y2 = door2

    # Create corridor using improved path finding
    create_smart_corridor(x1, y1, x2, y2, visualizing, visualized_tiles)

    # Visualize if needed
    if visualizing:
        print_dungeon_ascii(vars.dungeon, title="Hallway Created")
        input("Press Enter to proceed...")

    # Reset visualization
    for y, x in visualized_tiles:
        vars.dungeon[y][x] = vars.graphic["floor_char"]

def find_closest_room_points(room1, room2):
    """Find the closest points between two rooms."""
    min_dist = float('inf')
    closest_points = None
    
    # Check all points along the edges of both rooms
    for x1 in range(room1['x'], room1['x'] + room1['width']):
        for y1 in [room1['y'], room1['y'] + room1['height'] - 1]:
            for x2 in range(room2['x'], room2['x'] + room2['width']):
                for y2 in [room2['y'], room2['y'] + room2['height'] - 1]:
                    dist = abs(x1 - x2) + abs(y1 - y2)  # Manhattan distance
                    if dist < min_dist:
                        min_dist = dist
                        closest_points = ((x1, y1), (x2, y2))
    
    for y1 in range(room1['y'], room1['y'] + room1['height']):
        for x1 in [room1['x'], room1['x'] + room1['width'] - 1]:
            for y2 in range(room2['y'], room2['y'] + room2['height']):
                for x2 in [room2['x'], room2['x'] + room2['width'] - 1]:
                    dist = abs(x1 - x2) + abs(y1 - y2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_points = ((x1, y1), (x2, y2))
    
    return closest_points

def find_door_point(room, target_x, target_y):
    """Find the best door point on a room's edge closest to the target."""
    candidates = []
    
    # Add points along horizontal edges
    for x in range(room['x'] + 1, room['x'] + room['width'] - 1):
        candidates.append((x, room['y']))  # Top edge
        candidates.append((x, room['y'] + room['height'] - 1))  # Bottom edge
    
    # Add points along vertical edges
    for y in range(room['y'] + 1, room['y'] + room['height'] - 1):
        candidates.append((room['x'], y))  # Left edge
        candidates.append((room['x'] + room['width'] - 1, y))  # Right edge
    
    # Find closest point to target
    return min(candidates, key=lambda p: abs(p[0] - target_x) + abs(p[1] - target_y), default=None)

def create_smart_corridor(x1, y1, x2, y2, visualizing=vars.settings["debug"], visualized_tiles=None):
    """Create a corridor between two points using an improved pathfinding approach."""
    # Determine the primary and secondary directions
    dx = x2 - x1
    dy = y2 - y1
    
    # Calculate intermediate points for smoother paths
    intermediate_points = []
    
    # Choose path based on relative positions
    if abs(dx) > abs(dy):
        # Horizontal primary direction
        mid_x = x1 + dx // 2
        intermediate_points = [
            (mid_x, y1),
            (mid_x, y2),
            (x2, y2)
        ]
    else:
        # Vertical primary direction
        mid_y = y1 + dy // 2
        intermediate_points = [
            (x1, mid_y),
            (x2, mid_y),
            (x2, y2)
        ]
    
    # Connect all points
    current = (x1, y1)
    for next_point in intermediate_points:
        connect_points(current[0], current[1], next_point[0], next_point[1], visualizing, visualized_tiles)
        current = next_point

def connect_points(x1, y1, x2, y2, visualizing=vars.settings["debug"], visualized_tiles=None):
    """Connect two points with a straight line while avoiding obstacles."""
    # Create horizontal or vertical line
    if x1 == x2:  # Vertical line
        for y in range(min(y1, y2), max(y1, y2) + 1):
            place_corridor_tile(x1, y, visualizing, visualized_tiles)
    else:  # Horizontal line
        for x in range(min(x1, x2), max(x1, x2) + 1):
            place_corridor_tile(x, y1, visualizing, visualized_tiles)

def place_corridor_tile(x, y, visualizing=vars.settings["debug"], visualized_tiles=None):
    """Place a corridor tile while respecting existing structures."""
    # Don't override room floors or existing corridors
    if vars.dungeon[y][x] not in [vars.graphic["floor_char"], vars.graphic["secret_floor_char"]]:
        if visualizing:
            if visualized_tiles is not None:
                visualized_tiles.append((y, x))
            vars.dungeon[y][x] = "[#444444]█[/]"
        else:
            vars.dungeon[y][x] = vars.graphic["floor_char"]

def create_h_tunnel(x1, x2, y, is_secret=False, visualizing=False, visualized_tiles=None):
    """Create a horizontal tunnel."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if visualizing:
            if visualized_tiles is not None:
                visualized_tiles.append((y, x))
            vars.dungeon[y][x] = "[#444444]█[/]"
        else:
            vars.dungeon[y][x] = vars.graphic["wall_char"] if is_secret else vars.graphic["floor_char"]

def create_v_tunnel(y1, y2, x, is_secret=False, visualizing=False, visualized_tiles=None):
    """Create a vertical tunnel."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if visualizing:
            if visualized_tiles is not None:
                visualized_tiles.append((y, x))
            vars.dungeon[y][x] = "[#444444]█[/]"
        else:
            vars.dungeon[y][x] = vars.graphic["wall_char"] if is_secret else vars.graphic["floor_char"]

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
        weak_enemies = [et for et in vars.enemy_types_list if et['base_max_health'] <= 10]
        return random.choice(weak_enemies)
    else:
        # Increase enemy strength with floor
        suitable_enemies = [et for et in vars.enemy_types_list if et['base_max_health'] <= 10 + floor * 5]
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