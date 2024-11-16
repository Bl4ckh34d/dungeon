import os
import sys
import vars
import time
import math
import random
from dungeon import generate_dungeon
import menus
from utils import get_line, get_limited_input, format_encounter_line, format_battle_line, format_stats_line, distance
from vars import console


# Detect OS for clearing the screen
def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')
        
    else:
        os.system('clear')
    
    console.print(format_stats_line(vars.player))

def display_dungeon():
    clear_screen()
    console.print(vars.message["notification"]["map_line"])
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
                        cell = vars.dungeon[y][x]
                        if cell == vars.graphic["secret_wall_char"] or cell == vars.graphic["wall_char"]:
                            # Check if within detection distance
                            if distance(vars.player['pos'], [y, x]) <= vars.player['awareness']:
                                if cell == vars.graphic["secret_wall_char"]:
                                    row += vars.graphic["door_char"]  # Reveal secret door
                                else:
                                    row += vars.graphic["wall_char"]
                            else:
                                row += vars.graphic["wall_char"]
                        else:
                            # Check if item is on this cell
                            if (y, x) in vars.items_on_floor:
                                row += vars.graphic["item_char"]
                            else:
                                row += cell
        console.print(row, end="")
        print()  # Newline after each row

def move_player(direction):
    new_y = vars.player['pos'][0] + vars.directions[direction][0]
    new_x = vars.player['pos'][1] + vars.directions[direction][1]
    if 0 <= new_y < vars.settings["dungeon_height"] and 0 <= new_x < vars.settings["dungeon_width"]:
        cell = vars.dungeon[new_y][new_x]
        enemy_here = next((e for e in vars.enemies if e.pos == [new_y, new_x]), None)
        if enemy_here:
            encounter_enemy(enemy_here)
        elif cell == vars.graphic["wall_char"]:
            console.print(vars.message["notification"]["wall_bump"])
        elif cell == vars.graphic["secret_wall_char"]:
            console.print(vars.message["notification"]["wall_bump"])
        elif cell in [vars.graphic["floor_char"], vars.graphic["door_char"], vars.graphic["secret_floor_char"], vars.graphic["item_char"], vars.graphic["treasure_char"], vars.graphic["exit_char"], vars.graphic["shop_char"]]:
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
                    sys.exit()
                else:
                    console.print(vars.message["notification"]["exit_found"])
                    vars.player['floor'] += 1
                    generate_dungeon()
                    return
            elif cell == vars.graphic["shop_char"]:
                menus.enter_shop((new_y, new_x))
            vars.player['pos'] = [new_y, new_x]

# Encounter an enemy
def encounter_enemy(enemy):
    display_dungeon()
    console.print(format_encounter_line(enemy.type['name']))
    time.sleep(vars.settings["delay_enemy_encounter"] * (1 / 3))
    console.print(vars.message['battle']['battle_sit_rep'].format(enemy=enemy.type['name']))
    time.sleep(vars.settings["delay_enemy_encounter"] * (2 / 3))
    while enemy.health > 0 and vars.player['health'] > 0:
        display_dungeon()
        console.print(vars.message["notification"]["player_action"])
        time.sleep(vars.settings["delay_player_action"] / 2)
        action = console.input(vars.message["notification"]["cursor"]).upper()
        time.sleep(vars.settings["delay_player_action"] / 2)
        if action == 'A':
            display_dungeon()
            console.print(format_battle_line(enemy.type['name']))
            weapon = vars.player['equipped']['weapon']
            weapon_attack = weapon['attack'] if weapon and 'attack' in weapon else 0
            damage_to_enemy = max(0, vars.player['attack'] + weapon_attack - enemy.defense + random.randint(-2, 2))
            enemy.health -= damage_to_enemy
            console.print(vars.message["battle"]["enemy_hit_by_player"].format(damage=damage_to_enemy, type=enemy.type['name']))
            if weapon and 'effect' in weapon:
                apply_status_effect(enemy, weapon['effect'])
            if enemy.health <= 0:
                time.sleep(vars.settings["delay_enemy_defeated"] / 2)
                console.print(vars.message["battle"]["enemy_defeated"].format(type=enemy.type['name']))
                time.sleep(vars.settings["delay_enemy_defeated"] / 2)
                vars.player['exp'] += enemy.exp
                # Handle loot drops based on enemy type
                handle_loot(enemy)
                check_level_up()
                break
            # Enemy attacks player
            enemy_attack(enemy)
            if vars.player['health'] <= 0:
                game_over()
                return
            display_dungeon()
        elif action == 'U':
            display_dungeon()
            menus.use_item()
        elif action == 'R':
            display_dungeon()
            # Attempt to run away
            success = attempt_run_away()
            if success:
                console.print(vars.message["notification"]["escape_line"])
                time.sleep(vars.settings["delay_flee_success"] / 2)
                console.print(vars.message["battle"]["ran_away"])
                time.sleep(vars.settings["delay_flee_success"] / 2)
                return
            else:
                console.print(vars.message["notification"]["battle_line"])
                time.sleep(vars.settings["delay_flee_success"] / 2)
                console.print(vars.message["battle"]["flee_fail"])
                time.sleep(vars.settings["delay_flee_success"] / 2)
                enemy_attack(enemy)
                if vars.player['health'] <= 0:
                    game_over()
                    return
        else:
            display_dungeon()
            console.print(vars.message["notification"]["battle_line"])
            time.sleep(vars.settings["delay_invalid_action"])

def attempt_run_away():
    # Run away success based on player's agility
    run_chance = vars.player['agility'] / 10  # Example: agility 5 -> 50% chance
    return random.random() < run_chance

def enemy_attack(enemy):
    damage_to_player = max(0, enemy.attack - vars.player['defense'] + random.randint(-2, 2))
    vars.player['health'] -= damage_to_player
    time.sleep(vars.settings["delay_enemy_attack"])
    console.print(vars.message["battle"]["player_hit_by_enemy"].format(type=enemy.type['name'], damage=damage_to_player))
    # Chance to apply poison effect
    if random.random() < 0.2 and enemy.type['name'].lower() not in ['mage', 'dragon']:
        apply_status_effect(vars.player, 'poison')
    time.sleep(vars.settings["delay_enemy_attack"])

def apply_status_effect(target, effect):
    from enemy import Enemy
    if isinstance(target, Enemy):
        # Check if enemy is immune to the effect
        if 'immunities' in target.type and effect in target.type['immunities']:
            console.print(vars.message["battle"]["enemy_immune"].format(type=target.type['name'], effect=effect))
            return
        # Check if enemy has weakness to the effect
        if 'weaknesses' in target.type and effect in target.type['weaknesses']:
            # Apply enhanced effect or additional damage
            duration_multiplier = 2
            console.print(vars.message["battle"]["enemy_weak"].format(type=target.type['name'], effect=effect))
        else:
            duration_multiplier = 1
        if effect == 'poison':
            duration = effect["effect"][0]["duration"] * duration_multiplier
        elif effect == 'burn':
            duration = effect["effect"][1]["duration"] * duration_multiplier
        else:
            duration = 5 * duration_multiplier
        target.status_effects.append({'effect': effect, 'duration': duration})
        console.print(vars.message["battle"]["enemy_effect"].format(effect=effect))
    else:
        # Handle player status effects
        if effect == 'poison':
            target['status_effects'].append(vars.effects["effect"][0])
            console.print(vars.message["status_effects"]["poison"])
        elif effect == 'burn':
            target['status_effects'].append(vars.effects["effect"][1])
            console.print(vars.message["status_effects"]["fire"])
        elif effect == 'freeze':
            target['status_effects'].append(vars.effects["effect"][2])
            console.print(vars.message["status_effects"]["ice"])
        elif effect == 'shock':
            target['status_effects'].append(vars.effects["effect"][3])
            console.print(vars.message["status_effects"]["shock"])
        elif effect == 'invisibility':
            target['status_effects'].append(vars.effects["effect"][4])
            console.print(vars.message["status_effects"]["invisible"])
        elif effect == 'blindness':
            target['status_effects'].append(vars.effects["effect"][5])
            console.print(vars.message["status_effects"]["blindness"])
        elif effect == 'poison_resist':
            target['status_effects'].append(vars.effects["effect"][6])
            console.print(vars.message["status_effects"]["poison_resist"])
        elif effect == 'fire_resist':
            target['status_effects'].append(vars.effects["effect"][7])
            console.print(vars.message["status_effects"]["fire_resist"])
        elif effect == 'ice_resist':
            target['status_effects'].append(vars.effects["effect"][8])
            console.print(vars.message["status_effects"]["ice_resist"])
        elif effect == 'shock_resist':
            target['status_effects'].append(vars.effects["effect"][9])
            console.print(vars.message["status_effects"]["shock_resist"])
        elif effect == 'blind_resist':
            target['status_effects'].append(vars.effects["effect"][10])
            console.print(vars.message["status_effects"]["blind_resist"])
        elif effect == 'heal':
            target['health'] = min(target['health'] + 10, target['max_health'])
            console.print(vars.message["status_effects"]["heal"])
        elif effect == 'cure_poison':
            target['status_effects'] = [e for e in target['status_effects'] if e['effect'] != 'poison']
            console.print(vars.message["status_effects"]["cure"])
        elif effect == 'cure_burn':
            target['status_effects'] = [e for e in target['status_effects'] if e['effect'] != 'burn']
            console.print(vars.message["status_effects"]["extinguished"])
        elif effect == 'strength':
            target['attack'] += 2
            console.print(vars.message["status_effects"]["strength_up"])
        elif effect == 'defense':
            target['defense'] += 2
            console.print(vars.message["status_effects"]["defense_up"])
        elif effect == 'speed':
            vars.player['agility'] += 2
            console.print(vars.message["status_effects"]["speed_up"])
        elif effect == 'wisdom':
            console.print(vars.message["status_effects"]["wisdom_up"])
        elif effect == 'identify':
            menus.identify_item()
        time.sleep(vars.settings["delay_apply_status_effect"])

def handle_status_effects():
    # Handle player status effects
    for effect in vars.player['status_effects'][:]:
        if effect['effect'] == 'poison':
            vars.player['health'] -= vars.effects["effect_damage"]["POISON_DAMAGE"]
            console.print(f"You take [red]{vars.effects['effect_damage']['POISON_DAMAGE']}[/red] [bold green]poison[/bold green] [red]damage[/red]!")
        elif effect['effect'] == 'burn':
            vars.player['health'] -= vars.effects["effect_damage"]["BURN_DAMAGE"]
            console.print(f"You take [red]{vars.effects['effect_damage']['BURN_DAMAGE']}[/red] [bold red]burn[/bold red] [red]damage[/red]!")
        elif effect['effect'] == 'shock':
            vars.player['health'] -= vars.effects["effect_damage"]["SHOCK_DAMAGE"]
            console.print(f"You take [red]{vars.effects['effect_damage']['SHOCK_DAMAGE']}[/red] [bold blue]shock[/bold blue] [red]damage[/red]!")
        effect['duration'] -= 1
        if effect['duration'] <= 0:
            vars.player['status_effects'].remove(effect)
            console.print(f"You are no longer affected by {effect['effect']}.")

    # Handle enemy status effects
    for enemy in vars.enemies:
        for effect in enemy.status_effects[:]:
            if effect['effect'] == 'poison':
                enemy.health -= vars.effects["effect_damage"]["POISON_DAMAGE"]
                console.print(f"[bold green]{enemy.type['name']} takes {vars.effects['effect_damage']['POISON_DAMAGE']} poison damage![/bold green]")
            elif effect['effect'] == 'burn':
                enemy.health -= vars.effects["effect_damage"]["BURN_DAMAGE"]
                console.print(f"[bold red]{enemy.type['name']} takes {vars.effects['effect_damage']['BURN_DAMAGE']} burn damage![/bold red]")
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                enemy.status_effects.remove(effect)
                console.print(f"{enemy.type['name']} is no longer affected by {effect['effect']}.")
    time.sleep(vars.settings["delay_enemy_status_effect"])

def find_treasure():
    display_dungeon()
    console.print(vars.message["notification"]["controls_line"])
    loot = random.choice([item for item in vars.items if item['type'] == 'money'])
    amount = loot['amount'] + random.randint(-5, 5)
    amount = max(1, amount)  # Ensure at least 1 gold
    vars.player['gold'] += amount
    console.print(vars.message["notification"]["found_loot"].format(loot=loot['name'], amount=amount))
    time.sleep(vars.settings["delay_find_treasure"])

def find_item(y, x):
    display_dungeon()
    console.print(vars.message["notification"]["controls_line"])
    item = vars.items_on_floor.get((y, x))
    if item:
        item = item.copy()  # Create a copy to avoid modifying the original
        if item['type'] in ['weapon', 'armor', 'accessory']:
            item['identified'] = False
            item['name'] = f"Unidentified {item['type'].capitalize()}"
        vars.player['inventory'].append(item)
        console.print(vars.message["notification"]["found_item"].format(item=item['name']))
    else:
        console.print("You found nothing.")
    time.sleep(vars.settings["delay_find_item"])

def handle_loot(enemy):
    if enemy.loot_type == 'weapon':
        if enemy.weapon:
            console.print(f"The {enemy.type['name']} dropped something and you pick it up!") #f"The {enemy.type['name']} dropped its {enemy.weapon['name']}!"
            # Ensure the weapon is marked as identified when dropped by enemies
            enemy.weapon['identified'] = False
            enemy.weapon['name'] = f"Unidentified {enemy.weapon['type'].capitalize()}"

            vars.player['inventory'].append(enemy.weapon)
    elif enemy.loot_type == 'magical':
        magical_items = [item for item in vars.items if item['type'] in ['weapon', 'accessory'] and 'magic' in item.get('effect', '')]
        if magical_items:
            drop = random.choice(magical_items)
            drop = drop.copy()
            drop['identified'] = False
            drop['name'] = f"Unidentified {drop['type'].capitalize()}"
            vars.player['inventory'].append(drop)
            console.print(f"The {enemy.type['name']} dropped a {drop['name']}!")
    elif enemy.loot_type == 'treasure':
        loot = random.choice([item for item in vars.items if item['type'] in ['money', 'potion']])
        if loot['type'] == 'money':
            amount = loot['amount'] + random.randint(-10, 10)
            amount = max(5, amount)
            vars.player['gold'] += amount
            console.print(f"The {enemy.type['name']} dropped {amount} gold!")
        else:
            loot = loot.copy()
            if loot['type'] in ['weapon', 'armor', 'accessory']:
                loot['identified'] = False
                loot['name'] = f"Unidentified {loot['type'].capitalize()}"
            vars.player['inventory'].append(loot)
            console.print(f"The {enemy.type['name']} dropped a {loot['name']}!")
    time.sleep(vars.settings["delay_enemy_drop_loot"])



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
        create_player_projectile(target_enemy.pos, weapon)
    else:
        console.print(vars.message["warning"]["invalid_choice"])

def get_targets_in_line_of_sight():
    targets = []
    for enemy in vars.enemies:
        if is_in_line_of_sight(vars.player['pos'], enemy.pos):
            targets.append(enemy)
    return targets

def is_in_line_of_sight(start_pos, end_pos):
    path = get_line(start_pos[1], start_pos[0], end_pos[1], end_pos[0])
    for x, y in path:
        if vars.dungeon[y][x] == vars.graphic["wall_char"] or vars.dungeon[y][x] == vars.graphic["secret_wall_char"]:
            return False
        if [y, x] == end_pos:
            return True
    return False

def create_player_projectile(target_pos, weapon):
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
    console.print(vars.message["battle"]["shoot_projectile"])
    time.sleep(vars.settings["delay_shoot_projectile"])

# Check for level up
def check_level_up():
    exp_needed = vars.player['level'] * 20
    if vars.player['exp'] >= exp_needed:
        vars.player['level'] += 1
        vars.player['exp'] -= exp_needed
        vars.player['max_health'] += 10
        vars.player['health'] = vars.player['max_health']
        vars.player['attack'] += 2
        vars.player['defense'] += 2
        vars.player['agility'] += 1
        vars.player['awareness'] += 1  # Increase awareness with level
        console.print(f"[green]You have leveled up to level [blue]{vars.player['level']}[/blue]![/green]")
        time.sleep(vars.settings["delay_leveled_up"])
    # return remaining exp until next level-up
    else:
        remaining_exp = exp_needed - vars.player['exp']
        return remaining_exp 

def equip_item(item):
    if item['type'] == 'weapon':
        vars.player['equipped']['weapon'] = item
        console.print(f"You equipped {item['name']}.")
    elif item['type'] == 'armor':
        vars.player['equipped']['armor'] = item
        console.print(f"You equipped {item['name']}.")
    elif item['type'] == 'accessory':
        # Remove effect of current accessory if any
        if vars.player['equipped']['accessory']:
            remove_accessory_effect(vars.player['equipped']['accessory'])
        vars.player['equipped']['accessory'] = item
        apply_accessory_effect(item)
        console.print(f"You equipped {item['name']}.")
    else:
        console.print("You cannot equip this item.")
    # Update player class based on new equipment
    menus.determine_player_class()
    time.sleep(vars.settings["delay_equip_item"])

def apply_accessory_effect(item):
    effect = item.get('effect')
    if effect == 'health_boost':
        vars.player['max_health'] += 20
        vars.player['health'] += 20  # Increase current health
        console.print("Your maximum health has increased!")
    elif effect == 'magic_boost':
        vars.player['attack'] += 2  # Example effect
        console.print("Your magic power has increased!")
    # Add other accessory effects as needed

def remove_accessory_effect(item):
    effect = item.get('effect')
    if effect == 'health_boost':
        vars.player['max_health'] -= 20
        vars.player['health'] = min(vars.player['health'], vars.player['max_health'])
        console.print("Your maximum health has decreased.")
    elif effect == 'magic_boost':
        vars.player['attack'] -= 2
        console.print("Your magic power has decreased.")
    # Add other accessory effects as needed



# Handle game over
def game_over():
    console.print()
    console.print(vars.message["game_over"]["defeated"])
    choice = console.input(vars.message["input"]["restart_or_quit"]).upper()
    if choice == "R":
        reset_game()
        main_game_loop()
    elif choice == "Q":
        console.print()
        console.print(vars.message["game_over"]["thank_you"])
        sys.exit()
    else:
        console.print()
        console.print(vars.message["game_over"]["invalid_choice"])
        sys.exit()

def reset_game():
    vars.player['health'] = vars.player['max_health']
    vars.player['gold'] = random.randint(0,50)
    vars.player['floor'] = 1
    vars.player['level'] = 1
    vars.player['exp'] = 0
    vars.player['attack'] = 10
    vars.player['defense'] = 5
    vars.player['agility'] = 5
    vars.player['awareness'] = 1
    vars.player['inventory'] = []
    vars.player['equipped'] = {'weapon': None, 'armor': None, 'accessory': None}
    vars.player['status_effects'] = []
    vars.player['symbol'] = '[green]@[/green]'
    vars.player['class'] = 'Warrior'
    vars.player['shops_visited'] = set()

# Main game loop
def main_game_loop():
    generate_dungeon(vars.player)
    while vars.player['health'] > 0:
        display_dungeon()
        console.print(vars.message["notification"]["controls_line"])
        move = console.input(vars.message["notification"]["cursor"]).upper()
        if move == "W":
            move_player("N")
        elif move == "S":
            move_player("S")
        elif move == "A":
            move_player("W")
        elif move == "D":
            move_player("E")
        elif move == "I":
            menus.show_inventory()
        elif move == "M":
            menus.show_menu()

        # Enemies take their turn
        for enemy in vars.enemies:
            enemy.move(vars.player['pos'])

        # Move projectiles
        for projectile in vars.projectiles[:]:
            p = projectile
            new_y = p['pos'][0] + p['direction'][0]
            new_x = p['pos'][1] + p['direction'][1]
            if not (0 <= new_y < vars.settings["dungeon_height"] and 0 <= new_x < vars.settings["dungeon_width"]):
                vars.projectiles.remove(p)
                continue
            if vars.dungeon[new_y][new_x] == vars.graphic["wall_char"] or vars.dungeon[new_y][new_x] == vars.graphic["secret_wall_char"]:
                vars.projectiles.remove(p)
                continue
            if [new_y, new_x] == vars.player['pos']:
                if p['owner_type'] != 'player':
                    # Find the owner enemy
                    owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                    if owner_enemy:
                        damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                    else:
                        damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))  # Default damage
                    vars.player['health'] -= damage
                    console.print(vars.message["battle"]["player_hit_by_projectile"].format(damage=damage))
                    vars.projectiles.remove(p)
                    if vars.player['health'] <= 0:
                        game_over()
                        return
            else:
                enemy_hit = next((e for e in vars.enemies if e.pos == [new_y, new_x]), None)
                if enemy_hit and p['owner_type'] == 'player':
                    weapon = p.get('weapon', {})
                    weapon_attack = weapon.get('attack', 0)
                    damage = max(0, vars.player['attack'] + weapon_attack - enemy_hit.defense + random.randint(-2, 2))
                    enemy_hit.health -= damage
                    console.print(vars.message["battle"]["enemy_hit_by_projectile"].format(enemy=enemy_hit.type['name'], damage=damage))
                    if weapon and 'effect' in weapon:
                        apply_status_effect(enemy_hit, weapon['effect'])
                    vars.projectiles.remove(p)
                    if enemy_hit.health <= 0:
                        time.sleep(vars.settings["delay_defeated_enemy"] / 2)
                        console.print(vars.message["battle"]["enemy_defeated"].format(enemy=enemy_hit.type['name']))
                        vars.player['exp'] += enemy_hit.exp
                        handle_loot(enemy_hit)
                        check_level_up()
                        time.sleep(vars.settings["delay_defeated_enemy"] / 2)
                        vars.enemies.remove(enemy_hit)
                        display_dungeon()
                    continue
                else:
                    p['pos'] = [new_y, new_x]

        # Check for enemy at player's position
        enemy_at_player = next((e for e in vars.enemies if e.pos == vars.player['pos']), None)
        if enemy_at_player:
            encounter_enemy(enemy_at_player)
            if enemy_at_player.health <= 0:
                vars.enemies.remove(enemy_at_player)

        handle_status_effects()

        # Remove dead enemies
        vars.enemies[:] = [e for e in vars.enemies if e.health > 0]

        if vars.player['health'] <= 0:
            break

if __name__ == "__main__":
    main_game_loop()
