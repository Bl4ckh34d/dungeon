import math
import time
import vars
from vars import console

def fire_ranged_weapon(weapon):
    console.print(f"You use the {weapon['name']} to fire at an enemy.")
    # Check for enemies in line of sight
    targets = get_targets_in_line_of_sight()
    if not targets:
        console.print("No targets in line of sight.")
        return
    console.print("Targets in line of sight:")
    for idx, enemy in enumerate(targets):
        console.print(f"{idx+1}. {enemy.type['name']} at position {enemy.pos}")
    choice = console.input("Enter the number of the target to attack or hit enter to cancel: ")
    if choice == '':
        return
    elif choice.isdigit() and 1 <= int(choice) <= len(targets):
        target_enemy = targets[int(choice)-1]
        # Fire projectile towards the enemy
        create_player_projectile(target_enemy.pos, weapon, target_enemy)

def get_targets_in_line_of_sight():
    
    from utils import (
        is_in_line_of_sight
    )
    
    targets = []
    for enemy in vars.enemies:
        if is_in_line_of_sight(vars.player['pos'], enemy.pos):
            targets.append(enemy)
    return targets

def create_player_projectile(target_pos, weapon, target):
    dy = target_pos[0] - vars.player['pos'][0]
    dx = target_pos[1] - vars.player['pos'][1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        return
    direction = (int(round(dy / distance)), int(round(dx / distance)))

    # Assign projectile symbol based on weapon or effect
    if weapon.get('effect') == 'burn':
        symbol = '[red]🔥[/red]'
    elif weapon.get('effect') == 'freeze':
        symbol = '[cyan]❄️[/cyan]'
    elif weapon.get('effect') == 'shock':
        symbol = '[yellow]⚡[/yellow]'
    elif weapon.get('effect') == 'poison':
        symbol = '[green]☠️[/green]'
    else:
        symbol = '[grey]➵[/grey]'  # Default arrow symbol

    projectile = {
        'pos': vars.player['pos'].copy(),
        'direction': direction,
        'symbol': symbol,
        'owner_type': 'player',
        'weapon': weapon
    }
    vars.projectiles.append(projectile)
    console.print(vars.message["battle"]["notifications"]["shoot_projectile"].format(type=target.type['name']))
    time.sleep(vars.settings["delay_shoot_projectile"])
