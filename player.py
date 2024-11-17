from utils import distance
from vars import console
import time
import random
import vars
import sys

def update_player_stats():
    """Update the player's stats based on equipped items."""
    weapon = vars.player['equipped']['weapon']
    armor = vars.player['equipped']['armor']
    accessory = vars.player['equipped']['accessory']

    vars.player['attack'] = vars.player['base_attack'] + (weapon['attack'] if weapon else 0)
    vars.player['defense'] = vars.player['base_defense'] + (armor['defense'] if armor else 0)
    vars.player['agility'] = vars.player['base_agility'] + (accessory['agility'] if accessory else 0)
    vars.player['wisdom'] = vars.player['base_wisdom'] + (accessory['wisdom'] if accessory else 0)
    vars.player['awareness'] = vars.player['base_awareness'] + (accessory['awareness'] if accessory else 0)
    vars.player['max_health'] = vars.player['base_max_health'] + (accessory['health'] if accessory else 0)

def check_level_up():
    exp_needed = vars.player['level'] * 20
    if vars.player['exp'] >= exp_needed:
        vars.player['level'] += 1
        vars.player['exp'] -= exp_needed
        vars.player['base_max_health'] += 10 
        vars.player['max_health'] = vars.player['base_max_health']
        vars.player['health'] = vars.player['base_max_health']
        vars.player['base_attack'] += 2
        vars.player['base_defense'] += 2
        vars.player['base_agility'] += 1
        vars.player['base_wisdom'] += 1
        vars.player['base_awareness'] += 1
        console.print(vars.message['notification']['level_up'].format(level=vars.player['level']))
        time.sleep(vars.settings["delay_leveled_up"])
        update_player_stats()
    else:
        remaining_exp = exp_needed - vars.player['exp']
        return remaining_exp

def move_player(direction):
    
    from menus import enter_shop
    from battle import encounter_enemies
    from dungeon import (
        reveal_secret_room,
        generate_dungeon,
    )
    from items import (
        find_item,
        find_treasure
    )
    from utils import is_adjacent
        
    new_y = vars.player['pos'][0] + vars.directions[direction][0]
    new_x = vars.player['pos'][1] + vars.directions[direction][1]
    if 0 <= new_y < vars.settings["dungeon_height"] and 0 <= new_x < vars.settings["dungeon_width"]:
        cell = vars.dungeon[new_y][new_x]
        adjacent_enemies = [enemy for enemy in vars.enemies if is_adjacent(enemy.pos, vars.player['pos'])]
        if len(adjacent_enemies) > 0:
            encounter_enemies(adjacent_enemies)
        elif cell == vars.graphic["wall_char"]:
            console.print(vars.message["notification"]["wall_bump"])
        elif cell == vars.graphic["secret_door_char"]:
            console.print(vars.message["notification"]["secret_door_bump"])
            vars.dungeon[new_y][new_x] = vars.graphic["floor_char"]  # Replace door with normal floor
            reveal_secret_room([new_y, new_x])  # Reveal the connected room and hallway
        elif cell in [vars.graphic["floor_char"], vars.graphic["item_char"], vars.graphic["treasure_char"], vars.graphic["exit_char"], vars.graphic["shop_char"]]:
            if (new_y, new_x) in vars.items_on_floor:
                find_item(new_y, new_x)
                del vars.items_on_floor[(new_y, new_x)]
                vars.dungeon[new_y][new_x] = vars.graphic["floor_char"]
            elif cell == vars.graphic["treasure_char"]:
                find_treasure()
                vars.dungeon[new_y][new_x] = vars.graphic["floor_char"]
            elif cell == vars.graphic["exit_char"]:
                if vars.player['floor'] == 10:
                    console.print(random.choice(vars.message["ending"]["game_finished"]))
                    vars.player['pos'] = [new_y, new_x]
                    sys.exit()
                else:
                    console.print(vars.message["notification"]["exit_found"])
                    vars.player['floor'] += 1
                    generate_dungeon(vars.player)
                    return
            elif cell == vars.graphic["shop_char"]:
                enter_shop((new_y, new_x))
            else:
                vars.player['pos'] = [new_y, new_x]

def within_awareness(tile):
    """Check if a tile is within the player's awareness range."""
    return distance(vars.player['pos'], tile) <= vars.player['awareness']