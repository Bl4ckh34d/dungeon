import time
import vars
import sys
import os
import re

def display_dungeon():
    clear_screen()
    vars.console.print(vars.message["notification"]["map_line"])
    for y in range(vars.settings["dungeon_height"]):
        row = ""
        for x in range(vars.settings["dungeon_width"]):
            if [y, x] == vars.player['pos']:
                row += vars.player['symbol']
            else:
                enemy_here = next((e for e in vars.enemies if e.pos == [y, x]), None)
                if enemy_here:
                    row += enemy_here.symbol
                else:
                    projectile_here = next((p for p in vars.projectiles if p['pos'] == [y, x]), None)
                    if projectile_here:
                        row += projectile_here['symbol']
                    else:
                        # Handle visibility of secret doors and tiles
                        cell = vars.dungeon[y][x]
                        if cell == vars.graphic["wall_char"] and within_awareness([y, x]):
                            if is_secret_door([y, x]):
                                row += vars.graphic["secret_door_char"]
                            else:
                                row += vars.graphic["wall_char"]
                        elif cell == vars.graphic["secret_wall_char"] and within_awareness([y, x]):
                            row += vars.graphic["wall_char"]
                        else:
                            row += cell
        vars.console.print(row, end="")
        print()  # Newline after each row

def get_line(x1, y1, x2, y2):
    # Bresenham's line algorithm
    points = []
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy
    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x1 += sx
        if e2 <= dx:
            err += dx
            y1 += sy
    return points

def clear_screen():
    """Clears the console screen."""
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')
    vars.console.print(format_stats_line(vars.player))

def distance(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def is_in_line_of_sight(start_pos, end_pos):
    """Determine if there is a clear line of sight between two positions."""
    path = get_line(start_pos[1], start_pos[0], end_pos[1], end_pos[0])
    for x, y in path:
        if vars.dungeon[y][x] == vars.graphic["wall_char"] or vars.dungeon[y][x] == vars.graphic["secret_wall_char"]:
            return False
        if [y, x] == end_pos:
            return True
    return False

def within_awareness(tile):
    """Check if a tile is within the player's awareness range."""
    return distance(vars.player['pos'], tile) <= vars.player['awareness']


def get_limited_input(prompt, max_length):
    # Prompt the user and get the full input
    user_input = input(prompt)
    
    # Check if the input exceeds the max length
    if len(user_input) > max_length:
        # Truncate the input to the allowed maximum length
        user_input = user_input[:max_length]
        print(f" [bold red][Warning:][/bold red] Input truncated to {max_length} characters!")
        time.sleep(vars.settings["delay_input_truncated"])
    
    return user_input
def format_encounter_line(variable, total_length=70):
    # Define the encounter message with the placeholder for type
    base_text = f"| You encountered a {variable}! |"
    filtered_text = re.sub(r'\[/?[a-zA-Z\s]+\]', '', variable)
    text_to_count = f"| You encountered a {filtered_text}! |"
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(text_to_count)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = "=" * padding_needed
    right_padding = "=" * (total_length - len(left_padding) - len(text_to_count))
    
    # Construct and return the centered line
    return f"{left_padding}{base_text}{right_padding}"

def format_visualization_line(variable, total_length=70):
    # Define the encounter message with the placeholder for type
    base_text = f"| {variable} |"
    filtered_text = re.sub(r'\[/?[a-zA-Z\s]+\]', '', variable)
    text_to_count = f"| {filtered_text} |"
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(text_to_count)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = "=" * padding_needed
    right_padding = "=" * (total_length - len(left_padding) - len(text_to_count))
    
    # Construct and return the centered line
    return f"{left_padding}{base_text}{right_padding}"

def format_battle_line(variable, total_length=70):
    # Define the encounter message with the placeholder for type
    base_text = f"| Fighting the {variable}! |"
    filtered_text = re.sub(r'\[/?[a-zA-Z\s]+\]', '', variable)
    text_to_count = f"| Fighting the {filtered_text}! |"
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(text_to_count)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = "=" * padding_needed
    right_padding = "=" * (total_length - len(left_padding) - len(text_to_count))
    
    # Construct and return the centered line
    return f"{left_padding}{base_text}{right_padding}"

def format_stats_line(player, total_length=69):
    # Define the encounter message with the placeholder for type
    base_text = f"Floor: {player['floor']} | Level: {player['level']} | HP: {player['health']}/{player['max_health']} | Gold: {player['gold']} | Exp: {player['exp']} | Awareness: {player['awareness']}"
    
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(base_text)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = " " * padding_needed
    right_padding = " " * (total_length - len(left_padding) - len(base_text))
    
    # Construct and return the centered line
    return f"{left_padding} {base_text} {right_padding}"
        
# Detect OS for clearing the screen
def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')
        
    else:
        os.system('clear')
    
    vars.console.print(format_stats_line(vars.player))
    
def is_secret_door(tile):
    """Determine if a tile is part of a secret door."""
    for room in vars.secret_rooms:
        if room_contains_tile(room, tile):
            return True
    return False

def room_contains_tile(room, tile):
    """Check if a tile is within the bounds of a room."""
    return room['x'] <= tile[1] < room['x'] + room['width'] and \
           room['y'] <= tile[0] < room['y'] + room['height']
           
def is_adjacent(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1])) == 1