import time
import random
import vars
from vars import console

def encounter_enemies(enemies):
    
    from menus import use_item
    from game import game_over
    from utils import (
        format_encounter_line,
        format_battle_line,
        display_dungeon,
        is_adjacent
    )
    from player import check_level_up
    from enemy import Enemy
    
    display_dungeon()
    if len(enemies) > 2:
        enemy_names = ", ".join([enemy.type['name'] for enemy in enemies[:-1]]) + ", and " + enemies[-1].type['name']
    elif len(enemies) == 2:
        enemy_names = " and ".join([enemy.type['name'] for enemy in enemies])
    else:
        enemy_names = enemies[0].type['name']
    console.print(format_encounter_line(enemy_names))
    console.print(vars.message['battle']['battle_sit_rep'].format(enemy=enemy_names))
    time.sleep(vars.settings["delay_enemy_encounter"])
    while enemies and vars.player['health'] > 0:
        for enemy in vars.enemies:
            enemy.move(vars.player['pos'])
        adjacent_enemies = [enemy for enemy in vars.enemies if is_adjacent(enemy.pos, vars.player['pos'])]
        if adjacent_enemies:
            enemies = adjacent_enemies
        if len(enemies) > 2:
            enemy_names = ", ".join([enemy.type['name'] for enemy in enemies[:-1]]) + ", and " + enemies[-1].type['name']
        elif len(enemies) == 2:
            enemy_names = " and ".join([enemy.type['name'] for enemy in enemies])
        else:
            enemy_names = enemies[0].type['name']
        display_dungeon()
        console.print(vars.message["notification"]["player_action"])
        handle_status_effects()
        action = console.input(vars.message["notification"]["cursor"]).upper()
        time.sleep(vars.settings["delay_player_action"] / 2)
        if action == 'A':
            display_dungeon()
            console.print(format_battle_line(enemy_names))
            if len(enemies) > 1:
                console.print(vars.message["battle"]["choose_enemy"])
                for idx, enemy in enumerate(enemies):
                    console.print(f"{idx + 1}. {enemy.type['name']} (HP: {enemy.health}/{enemy.max_health})")
                choice = console.input(vars.message["notification"]["cursor"]).strip()
                if not choice.isdigit() or not (1 <= int(choice) <= len(enemies)):
                    target_enemy = enemies[0]
                else:
                    target_enemy = enemies[int(choice) - 1]
            else:
                target_enemy = enemies[0]
            display_dungeon()
            console.print(format_battle_line(enemy_names))
            weapon = vars.player['equipped']['weapon']
            weapon_attack = weapon['attack'] if weapon and 'attack' in weapon else 0
            damage_to_enemy = max(0, vars.player['attack'] + weapon_attack - target_enemy.defense + random.randint(-2, 2))
            target_enemy.health -= damage_to_enemy
            console.print(vars.message["battle"]["enemy_hit_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
            if weapon and 'effect' in weapon and random.random() < 0.2:
                apply_status_effect(target_enemy, weapon['effect'])
            if target_enemy.health <= 0:
                # time.sleep(vars.settings["delay_enemy_defeated"] / 3)
                console.print(vars.message["battle"]["enemy_defeated"].format(type=target_enemy.type['name']))
                time.sleep(vars.settings["delay_enemy_defeated"])
                vars.player['exp'] += target_enemy.exp
                # Handle loot drops based on enemy type
                handle_loot(target_enemy)
                check_level_up()
                enemies.remove(target_enemy)
                vars.enemies.remove(target_enemy)  # Remove from global enemies list
                if not enemies:
                    break
            # Enemies attack player
            for enemy in enemies:
                enemy_attack(enemy)
                if vars.player['health'] <= 0:
                    game_over()
                    return
            display_dungeon()
        elif action == 'U':
            display_dungeon()
            use_item()
        elif action == 'R':
            display_dungeon()
            success = attempt_run_away(enemy)
            if success:
                console.print(vars.message["notification"]["escape_line"])
                console.print(vars.message["battle"]["ran_away"])
                time.sleep(vars.settings["delay_flee_success"])
                return
            else:
                console.print(vars.message["notification"]["battle_line"])
                console.print(vars.message["battle"]["flee_fail"])
                time.sleep(vars.settings["delay_flee_success"])
                # Enemies attack player
                for enemy in enemies:
                    enemy_attack(enemy)
                    if vars.player['health'] <= 0:
                        game_over()
                        return
        else:
            display_dungeon()
            console.print(vars.message["notification"]["battle_line"])
            time.sleep(vars.settings["delay_invalid_action"])

def attempt_run_away(enemy):
    run_chance = max(0.1, (vars.player['agility'] - enemy['base_agility']) / 10)
    return random.random() < run_chance

def enemy_attack(enemy):
    damage_to_player = max(0, enemy.attack - vars.player['defense'] + random.randint(-2, 2))
    vars.player['health'] -= damage_to_player
    # time.sleep(vars.settings["delay_enemy_attack"])
    console.print(vars.message["battle"]["player_hit_by_enemy"].format(type=enemy.type['name'], damage=damage_to_player))
    # Chance to apply poison effect
    if enemy.type['key'].lower() in ['r', 'b', 'k', 'g']:
        if random.random() < 0.2:
            apply_status_effect(vars.player, 'poison')
    if enemy.type['key'].lower() in ['c', 'h']:
        if random.random() < 0.2 and int(enemy.type['base_attack'] / vars.player['defense']) >= 1:
            #HP Transfer from Player to Enemy
            vars.player['health'] - int(enemy.type['base_attack'] / (vars.player['defense'] * 1.5))
            enemy.type['health'] + int(enemy.type['base_attack'] / (vars.player['defense'] * 1.5))
    if enemy.type['key'].lower() in ['m', 'd']:
        if random.random() < 0.2:
            apply_status_effect(vars.player, 'burn')
    if enemy.type['key'].lower() in ['m']:
        if random.random() < 0.2:
            apply_status_effect(vars.player, 'freeze')
    if enemy.type['key'].lower() in ['m']:
        if random.random() < 0.2:
            apply_status_effect(vars.player, 'shock')
    time.sleep(vars.settings["delay_enemy_attack"])

def apply_status_effect(target, effect):
    
    from enemy import Enemy
    from menus import identify_item
    
    def has_status_effect(target, effect):
        """Check if the target already has the status effect."""
        return any(e['effect'] == effect for e in target['status_effects'])
    
    if isinstance(target, Enemy):
        # Check if the enemy already has the effect
        if has_status_effect(target, effect):
            return
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
        elif effect == 'freeze':
            duration = effect["effect"][2]["duration"] * duration_multiplier
        elif effect == 'shock':
            duration = effect["effect"][3]["duration"] * duration_multiplier
        elif effect == 'silence':
            duration = effect["effect"][4]["duration"] * duration_multiplier
        else:
            duration = 5 * duration_multiplier
        target.status_effects.append({'effect': effect, 'duration': duration})
        console.print(vars.message["battle"]["enemy_effect"].format(effect=effect))
    else:
        # Check if the player already has the effect
        if has_status_effect(target, effect):
            console.print("Player has this status effect already!")
            return
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
        elif effect == 'silence':
            target['status_effects'].append(vars.effects["effect"][6])
            console.print(vars.message["status_effects"]["silence"])
        elif effect == 'poison_resist':
            target['status_effects'].append(vars.effects["effect"][7])
            console.print(vars.message["status_effects"]["poison_resist"])
        elif effect == 'fire_resist':
            target['status_effects'].append(vars.effects["effect"][8])
            console.print(vars.message["status_effects"]["fire_resist"])
        elif effect == 'ice_resist':
            target['status_effects'].append(vars.effects["effect"][9])
            console.print(vars.message["status_effects"]["ice_resist"])
        elif effect == 'shock_resist':
            target['status_effects'].append(vars.effects["effect"][10])
            console.print(vars.message["status_effects"]["shock_resist"])
        elif effect == 'blind_resist':
            target['status_effects'].append(vars.effects["effect"][11])
            console.print(vars.message["status_effects"]["blind_resist"])
        elif effect == 'silence_resist':
            target['status_effects'].append(vars.effects["effect"][12])
            console.print(vars.message["status_effects"]["silence_resist"])
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
            target['agility'] += 2
            console.print(vars.message["status_effects"]["speed_up"])
        elif effect == 'wisdom':
            target['wisdom'] += 2
            console.print(vars.message["status_effects"]["wisdom_up"])
        elif effect == 'identify':
            identify_item()
        time.sleep(vars.settings["delay_apply_status_effect"])

def handle_status_effects():
    # Handle player status effects
    for effect in vars.player['status_effects'][:]:
        if effect['id'] == 0:
            vars.player['health'] -= vars.effects["effect_damage"]["POISON_DAMAGE"]
            console.print(f"You take {vars.effects['effect_damage']['POISON_DAMAGE']} [bold green]poison damage[/bold green]!")
        elif effect['id'] == 1:
            vars.player['health'] -= vars.effects["effect_damage"]["BURN_DAMAGE"]
            console.print(f"You take {vars.effects['effect_damage']['BURN_DAMAGE']} [bold red]burn damage[/bold red]!")
        elif effect['id'] == 2:
            vars.player['health'] -= vars.effects["effect_damage"]["FROST_DAMAGE"]
            console.print(f"You take {vars.effects['effect_damage']['FROST_DAMAGE']} [bold blue]frost damage[/bold blue]!")
        elif effect['id'] == 3:
            vars.player['health'] -= vars.effects["effect_damage"]["SHOCK_DAMAGE"]
            console.print(f"You take {vars.effects['effect_damage']['SHOCK_DAMAGE']} [bold blue]shock damage[/bold blue]!")
        elif effect['id'] == 4:
            # Enemies stop following player and stop attacking player for duration
            console.print(f"You are now [bold #f2d2fe]invisible[/bold #f2d2fe]!")
        elif effect['id'] == 5:
            # Player can only see his 8 neighbouring tiles
            console.print(f"You are now [bold #4a412f]blind[/bold #4a412f]!")
        elif effect['id'] == 6:
            # Player can't cast spells or use scrolls for duration
            console.print(f"You are now [bold #a020f0]silenced[/bold #a020f0]!")
        effect['duration'] -= 1
        if effect['duration'] <= 0:
            vars.player['status_effects'].remove(effect)
            console.print(f"You are no longer affected by {effect['effect']}.")
        time.sleep(vars.settings["delay_enemy_status_effect"] / 2)

    # Handle enemy status effects
    for enemy in vars.enemies:
        for effect in enemy.status_effects[:]:
            if effect['id'] == 0:
                enemy.health -= vars.effects["effect_damage"]["POISON_DAMAGE"]
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['POISON_DAMAGE']} [bold green]poison damage[/bold green]!")
            elif effect['id'] == 1:
                enemy.health -= vars.effects["effect_damage"]["BURN_DAMAGE"]
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['BURN_DAMAGE']} [bold red]burn damage[/bold red]!")
            elif effect['id'] == 2:
                enemy.health -= vars.effects["effect_damage"]["FROST_DAMAGE"]
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['FROST_DAMAGE']} [bold blue]frost damage[/bold blue]!")
            elif effect['id'] == 3:
                enemy.health -= vars.effects["effect_damage"]["SHOCK_DAMAGE"]
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['SHOCK_DAMAGE']} [bold blue]shock damage[/bold blue]!")
            elif effect['id'] == 4:
                # Enemy icon turns into normal floor icon
                console.print(f"{enemy.type['name']} is now [bold #f2d2fe]invisible[/bold #f2d2fe]!")
            elif effect['id'] == 5:
                # Enemy chance of missing and not pursuing the player is higher
                console.print(f"{enemy.type['name']} is now [bold #4a412f]blind[/bold #4a412f]!")
            elif effect['id'] == 6:
                # Only effect on Dragons and Mages - can't attack for duration
                console.print(f"{enemy.type['name']} is now [bold #a020f0]silenced[/bold #a020f0]!")
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                enemy.status_effects.remove(effect)
                console.print(f"{enemy.type['name']} is no longer affected by {effect['effect']}.")
            time.sleep(vars.settings["delay_enemy_status_effect"] / 2)
    
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