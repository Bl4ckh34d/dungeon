import os
import sys
import json
import random
import vars
from utils import get_line

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
    player['pos'] = [first_room['y'] + first_room['settings["dungeon_height"]'] // 2, first_room['x'] + first_room['settings["dungeon_width"]'] // 2]

    # Place exit in the last room
    last_room = vars.rooms[-1]
    exit_x = last_room['x'] + last_room['settings["dungeon_height"]'] // 2
    exit_y = last_room['y'] + last_room['settings["dungeon_width"]'] // 2
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
    global dungeon, rooms, secret_rooms
    # Initialize map with walls
    for y in range(vars.settings["dungeon_height"]):
        for x in range(vars.settings["dungeon_width"]):
            vars.dungeon[y][x] = vars.graphic["wall_char"]

    # Define the number of rooms
    max_rooms = 20  # Adjusted number of rooms
    min_size = 4
    max_size = 10

    for _ in range(max_rooms):
        w = random.randint(min_size, max_size)
        h = random.randint(min_size, max_size)
        x = random.randint(1, vars.settings["dungeon_width"] - w - 2)
        y = random.randint(1, vars.settings["dungeon_height"] - h - 2)

        new_room = {'x': x, 'y': y, 'settings["dungeon_width"]': w, 'settings["dungeon_height"]': h}

        # Check for overlap
        if any(rooms_overlap(new_room, other_room) for other_room in vars.rooms + vars.secret_rooms):
            continue

        create_room(new_room)
        if vars.rooms:
            # Connect the new room to the previous room
            prev_room = vars.rooms[-1]
            connect_rooms(prev_room, new_room)

        vars.rooms.append(new_room)

def create_secret_rooms():
    num_secret_rooms = random.randint(1, 3)
    for _ in range(num_secret_rooms):
        attempts = 0
        while attempts < 100:
            w = random.randint(4, 6)
            h = random.randint(4, 6)
            x = random.randint(1, vars.settings["dungeon_width"] - w - 2)
            y = random.randint(1, vars.settings["dungeon_height"] - h - 2)

            secret_room = {'x': x, 'y': y, 'settings["dungeon_width"]': w, 'settings["dungeon_height"]': h}

            # Check for overlap
            if any(rooms_overlap(secret_room, other_room) for other_room in vars.rooms + vars.secret_rooms):
                attempts += 1
                continue

            create_secret_room(secret_room)
            # Connect the secret room to a random room via a secret door
            target_room = random.choice(vars.rooms)
            connect_secret_room(secret_room, target_room)

            # Place stronger enemy and loot in secret room
            place_strong_enemy(secret_room)
            place_secret_room_items(secret_room)

            vars.secret_rooms.append(secret_room)
            break

def create_secret_room(room):
    for x in range(room['x'], room['x'] + room['settings["dungeon_width"]']):
        for y in range(room['y'], room['y'] + room['settings["dungeon_height"]']):
            vars.dungeon[y][x] = vars.graphic["secret_floor_char"]

def connect_secret_room(secret_room, target_room):
    # Create a secret corridor
    x1, y1 = secret_room['x'] + secret_room['settings["dungeon_width"]'] // 2, secret_room['y'] + secret_room['settings["dungeon_height"]'] // 2
    x2, y2 = target_room['x'] + target_room['settings["dungeon_width"]'] // 2, target_room['y'] + target_room['settings["dungeon_height"]'] // 2

    path = get_line(x1, y1, x2, y2)
    for x, y in path:
        if vars.dungeon[y][x] == vars.graphic["wall_char"]:
            vars.dungeon[y][x] = vars.graphic["secret_wall_char"]  # Secret walls
            
def place_strong_enemy(room):
    from enemy import Enemy
    
    x = room['x'] + room['settings["dungeon_width"]'] // 2
    y = room['y'] + room['settings["dungeon_height"]'] // 2
    # Select a strong enemy based on floor level
    enemy_type = select_strong_enemy_type()
    enemy = Enemy(enemy_type, y, x)
    vars.enemies.append(enemy)

def select_strong_enemy_type():
    floor = vars.player['floor']
    suitable_enemies = [et for et in vars.enemy_types_list if et['base_health'] >= 15 + floor * 2]
    if not suitable_enemies:
        suitable_enemies = vars.enemy_types_list
    return random.choice(suitable_enemies)

def place_secret_room_items(room):
    num_items = random.randint(1, 2)
    for _ in range(num_items):
        attempts = 0
        while attempts < 100:
            x = random.randint(room['x'] + 1, room['x'] + room['settings["dungeon_width"]'] - 2)
            y = random.randint(room['y'] + 1, room['y'] + room['settings["dungeon_height"]'] - 2)
            if vars.dungeon[y][x] == vars.graphic["secret_floor_char"]:
                vars.dungeon[y][x] = vars.graphic["item_char"]
                item = random.choice([item for item in vars.items if item['type'] in ['weapon', 'armor', 'accessory']])
                vars.items_on_floor[(y, x)] = item  # Store the item in the items_on_floor dictionary
                break
            attempts += 1

def rooms_overlap(room1, room2):
    return (room1['x'] <= room2['x'] + room2['settings["dungeon_width"]'] and
            room1['x'] + room1['settings["dungeon_width"]'] >= room2['x'] and
            room1['y'] <= room2['y'] + room2['settings["dungeon_height"]'] and
            room1['y'] + room1['settings["dungeon_height"]'] >= room2['y'])

def create_room(room):
    for x in range(room['x'], room['x'] + room['settings["dungeon_width"]']):
        for y in range(room['y'], room['y'] + room['settings["dungeon_height"]']):
            vars.dungeon[y][x] = vars.graphic["floor_char"]

def connect_rooms(room1, room2):
    x1, y1 = room1['x'] + room1['settings["dungeon_height"]'] // 2, room1['y'] + room1['settings["dungeon_height"]'] // 2
    x2, y2 = room2['x'] + room2['settings["dungeon_height"]'] // 2, room2['y'] + room2['settings["dungeon_height"]'] // 2

    if random.choice([True, False]):
        create_h_tunnel(x1, x2, y1)
        create_v_tunnel(y1, y2, x2)
    else:
        create_v_tunnel(y1, y2, x1)
        create_h_tunnel(x1, x2, y2)

def create_h_tunnel(x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if vars.dungeon[y][x] == vars.graphic["wall_char"]:
            vars.dungeon[y][x] = vars.graphic["floor_char"]

def create_v_tunnel(y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if vars.dungeon[y][x] == vars.graphic["wall_char"]:
            vars.dungeon[y][x] = vars.graphic["floor_char"]

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