import time
import vars
    
def distance(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

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

def format_encounter_line(variable, total_length=89):
    # Define the encounter message with the placeholder for type
    base_text = f"You encountered a [bold red]{variable}[/bold red]!"
    
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(base_text)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = "=" * padding_needed
    right_padding = "=" * (total_length - len(left_padding) - len(base_text))
    
    # Construct and return the centered line
    return f"{left_padding} {base_text} {right_padding}"

def format_battle_line(variable, total_length=89):
    # Define the encounter message with the placeholder for type
    base_text = f"Fighting the [bold red]{variable}[/bold red]!"
    
    # Calculate the length of padding needed on each side
    padding_needed = (total_length - len(base_text)) // 2
    # Ensure we have an even distribution of '=' on both sides
    left_padding = "=" * padding_needed
    right_padding = "=" * (total_length - len(left_padding) - len(base_text))
    
    # Construct and return the centered line
    return f"{left_padding} {base_text} {right_padding}"

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