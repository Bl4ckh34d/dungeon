import time
import random
import vars
from vars import console

def encounter_enemies(enemies):
    
    from menus import use_item_screen
    from game import game_over
    from utils import (
        format_encounter_line,
        format_status_bar,
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
    console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
    time.sleep(vars.settings["delay_enemy_encounter"] / 2)
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
        console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
        handle_status_effects()
        action = console.input(vars.message["notification"]["cursor"]).upper()
        time.sleep(vars.settings["delay_player_action"] / 2)
        if action == 'A' or action == '':
            display_dungeon()
            console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
            if len(enemies) > 1:
                console.print(vars.message["battle"]["choose_enemy"])
                for idx, enemy in enumerate(enemies):
                    console.print(f"{idx + 1}. {enemy.type['name']}")
                choice = console.input(vars.message["notification"]["cursor"]).strip()
                if not choice.isdigit() or not (1 <= int(choice) <= len(enemies)):
                    target_enemy = enemies[0]
                else:
                    target_enemy = enemies[int(choice) - 1]
            else:
                target_enemy = enemies[0]
            display_dungeon()
            console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
            weapon = vars.player['equipped']['weapon']
            weapon_attack = weapon['attack'] if weapon and 'attack' in weapon else 0
            damage_to_enemy = max(0, vars.player['attack'] + weapon_attack - target_enemy.defense + random.randint(-2, 2))
            
            max_possible_damage = vars.player['attack'] + weapon_attack - target_enemy.defense + 2
            damage_outcome = damage_to_enemy / max_possible_damage
            
            target_enemy.health -= damage_to_enemy
            time.sleep(vars.settings["delay_battle_messages"])
            if damage_to_enemy > 0 and target_enemy.type['key'] in ['g', 'c', 'r', 'g', 'k', 'f']:
                if damage_outcome > 0.75:
                    console.print(vars.message["battle"]["small_enemy_hit_hard_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
                else:
                    console.print(vars.message["battle"]["small_enemy_hit_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
            elif damage_to_enemy > 0 and target_enemy.type['key'] in ['o', 't', 'd', 's', 'm', 'z', 'h']:
                if damage_outcome > 0.75:
                    console.print(vars.message["battle"]["medium_enemy_hit_hard_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
                else:
                    console.print(vars.message["battle"]["medium_enemy_hit_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
            elif damage_to_enemy > 0 and target_enemy.type['key'] in ['t', 'd']:
                if damage_outcome > 0.75:
                    console.print(vars.message["battle"]["big_enemy_hit_hard_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
                else:
                    console.print(vars.message["battle"]["big_enemy_hit_by_player"].format(damage=damage_to_enemy, type=target_enemy.type['name']))
            elif target_enemy.type['key'] in ['g', 'c', 'r', 'g', 'k', 'f']:
                console.print(vars.message["battle"]["enemy_missed_by_player"].format(type=target_enemy.type['name']))
            elif target_enemy.type['key'] in ['o', 't', 'd', 's', 'm', 'z', 'h']:
                console.print(vars.message["battle"]["enemy_blocked_player"].format(type=target_enemy.type['name']))
            elif target_enemy.type['key'] in ['t', 'd']:
                console.print(vars.message["battle"]["enemy_bounced_player"].format(type=target_enemy.type['name']))
            time.sleep(vars.settings["delay_battle_messages"])
            if weapon and 'effect' in weapon and random.random() < 0.2 and damage_to_enemy > 0:
                time.sleep(vars.settings["delay_battle_messages"])
                apply_status_effect(target_enemy, weapon['effect'])
                time.sleep(vars.settings["delay_battle_messages"])
            if target_enemy.health <= 0:
                time.sleep(vars.settings["delay_enemy_defeated"])
                console.print(vars.message["battle"]["enemy_defeated"].format(type=target_enemy.type['name'], killed=random.choice(vars.message["killed"])))
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
            use_item_screen()
        elif action == 'R':
            display_dungeon()
            success = attempt_run_away(enemy)
            if success:
                console.print(vars.message["notification"]["escape_line"])
                console.print(vars.message["battle"]["ran_away"])
                time.sleep(vars.settings["delay_flee_success"])
                return
            else:
                console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
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
            console.print(format_status_bar(vars.player['health'], vars.player['max_health'], vars.player['mana'], vars.player['max_mana']))
            for enemy in enemies:
                enemy_attack(enemy)
                if vars.player['health'] <= 0:
                    game_over()
                    return
            time.sleep(vars.settings["delay_invalid_action"])

def attempt_run_away(enemy):
    run_chance = max(0.1, (vars.player['agility'] - enemy['base_agility']) / 10)
    return random.random() < run_chance

def enemy_attack(enemy):
    damage_to_player = max(0, enemy.attack - vars.player['defense'] + random.randint(-2, 2))
    vars.player['health'] -= damage_to_player
    time.sleep(vars.settings["delay_enemy_attack"])
    if damage_to_player > 0:
        console.print(vars.message["battle"]["player_hit_by_enemy"].format(type=enemy.type['name'], damage=damage_to_player))
    else:
        console.print(vars.message["battle"]["player_missed_by_enemy"].format(type=enemy.type['name']))
    time.sleep(vars.settings["delay_enemy_attack"])
    # Chance to apply poison effect
    if enemy.type['key'].lower() in ['r', 'b', 'k', 'g']:
        if random.random() < 0.2 and damage_to_player > 0:
            apply_status_effect(vars.player, 'poison')
    if enemy.type['key'].lower() in ['c', 'h']:
        if random.random() < 0.2 and int(enemy.type['base_attack'] / vars.player['defense']) >= 1:
            #HP Transfer from Player to Enemy
            blood_amount = int(enemy.type['base_attack'] / (vars.player['defense'] * random.random(0.5, 1.5)))
            vars.player['health'] - blood_amount
            enemy.type['health'] + blood_amount
            console.print(vars.message["battle"]["life_steal"].format(enemy=enemy.type['name'], damage=blood_amount))
    if enemy.type['key'].lower() in ['m', 'd']:
        if random.random() < 0.2 and damage_to_player > 0:
            apply_status_effect(vars.player, 'burn')
    if enemy.type['key'].lower() in ['m']:
        if random.random() < 0.2 and damage_to_player > 0:
            apply_status_effect(vars.player, 'freeze')
    if enemy.type['key'].lower() in ['m']:
        if random.random() < 0.2 and damage_to_player > 0:
            apply_status_effect(vars.player, 'shock')
    time.sleep(vars.settings["delay_enemy_attack"])

def apply_status_effect(target, effect):
    
    from enemy import Enemy
    from menus import identify_item
    
    def has_status_effect(target, effect):
        """Check if the target already has the status effect."""
        if isinstance(target, Enemy):
            return any(e['effect'] == effect for e in target.type['status_effects'])
        else:
            return any(e['effect'] == effect for e in target['status_effects'])
    
    if isinstance(target, Enemy):
        # Check if the enemy already has the effect
        if has_status_effect(target, effect):
            return
        # Check if enemy is immune to the effect
        if 'immunities' in target.type and effect in target.type['immunities']:
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["battle"]["enemy_immune"].format(type=target.type['name'], effect=effect))
            time.sleep(vars.settings["delay_apply_status_effect"])
            return
        # Check if enemy has weakness to the effect
        if 'weaknesses' in target.type and effect in target.type['weaknesses']:
            # Apply enhanced effect or additional damage
            duration_multiplier = 2
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["battle"]["enemy_weak"].format(type=target.type['name'], effect=effect))
            time.sleep(vars.settings["delay_apply_status_effect"])
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
        time.sleep(vars.settings["delay_apply_status_effect"])
        console.print(vars.message["battle"]["enemy_effect"].format(effect=effect, enemy=target.type['name']))
        time.sleep(vars.settings["delay_apply_status_effect"])
    else:
        # Check if the player already has the effect
        if has_status_effect(target, effect):
            return
        # Handle player status effects
        if effect == 'poison':
            target['status_effects'].append(vars.effects["effect"][0])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["poison"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'burn':
            target['status_effects'].append(vars.effects["effect"][1])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["fire"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'freeze':
            target['status_effects'].append(vars.effects["effect"][2])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["ice"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'shock':
            target['status_effects'].append(vars.effects["effect"][3])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["shock"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'invisibility':
            target['status_effects'].append(vars.effects["effect"][4])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["invisible"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'blindness':
            target['status_effects'].append(vars.effects["effect"][5])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["blindness"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'silence':
            target['status_effects'].append(vars.effects["effect"][6])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["silence"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'poison_resist':
            target['status_effects'].append(vars.effects["effect"][7])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["poison_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'fire_resist':
            target['status_effects'].append(vars.effects["effect"][8])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["fire_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'ice_resist':
            target['status_effects'].append(vars.effects["effect"][9])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["ice_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'shock_resist':
            target['status_effects'].append(vars.effects["effect"][10])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["shock_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'blind_resist':
            target['status_effects'].append(vars.effects["effect"][11])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["blind_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'silence_resist':
            target['status_effects'].append(vars.effects["effect"][12])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["silence_resist"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'heal':
            target['health'] = min(target['health'] + 10, target['max_health'])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["heal"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'charge':
            target['mana'] = min(target['mana'] + 10, target['max_mana'])
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["charge"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'cure_poison':
            target['status_effects'] = [e for e in target['status_effects'] if e['effect'] != 'poison']
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["cure"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'cure_burn':
            target['status_effects'] = [e for e in target['status_effects'] if e['effect'] != 'burn']
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["extinguished"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'strength':
            target['attack'] += 2
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["strength_up"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'defense':
            target['defense'] += 2
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["defense_up"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'speed':
            target['agility'] += 2
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["speed_up"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'wisdom':
            target['wisdom'] += 2
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(vars.message["status_effects"]["wisdom_up"])
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect == 'identify':
            time.sleep(vars.settings["delay_apply_status_effect"])
            identify_item()
            time.sleep(vars.settings["delay_apply_status_effect"])
        

def handle_status_effects():
    # Handle player status effects
    for effect in vars.player['status_effects'][:]:
        if effect['id'] == 0:
            vars.player['health'] -= vars.effects["effect_damage"]["POISON_DAMAGE"]
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You take {vars.effects['effect_damage']['POISON_DAMAGE']} [bold green]poison damage[/bold green]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 1:
            vars.player['health'] -= vars.effects["effect_damage"]["BURN_DAMAGE"]
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You take {vars.effects['effect_damage']['BURN_DAMAGE']} [bold red]burn damage[/bold red]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 2:
            vars.player['health'] -= vars.effects["effect_damage"]["FROST_DAMAGE"]
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You take {vars.effects['effect_damage']['FROST_DAMAGE']} [bold blue]frost damage[/bold blue]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 3:
            vars.player['health'] -= vars.effects["effect_damage"]["SHOCK_DAMAGE"]
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You take {vars.effects['effect_damage']['SHOCK_DAMAGE']} [bold blue]shock damage[/bold blue]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 4:
            # Enemies stop following player and stop attacking player for duration
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You are now [bold #f2d2fe]invisible[/bold #f2d2fe]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 5:
            # Player can only see his 8 neighbouring tiles
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You are now [bold #4a412f]blind[/bold #4a412f]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        elif effect['id'] == 6:
            # Player can't cast spells or use scrolls for duration
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You are now [bold #a020f0]silenced[/bold #a020f0]!")
            time.sleep(vars.settings["delay_apply_status_effect"])
        effect['duration'] -= 1
        if effect['duration'] <= 0:
            vars.player['status_effects'].remove(effect)
            time.sleep(vars.settings["delay_apply_status_effect"])
            console.print(f"You are no longer affected by {effect['effect']}.")
            time.sleep(vars.settings["delay_apply_status_effect"] * 2)

    # Handle enemy status effects
    for enemy in vars.enemies:
        for effect in enemy.status_effects[:]:
            if effect['id'] == 0:
                enemy.health -= vars.effects["effect_damage"]["POISON_DAMAGE"]
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['POISON_DAMAGE']} [bold green]poison damage[/bold green]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 1:
                enemy.health -= vars.effects["effect_damage"]["BURN_DAMAGE"]
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['BURN_DAMAGE']} [bold red]burn damage[/bold red]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 2:
                enemy.health -= vars.effects["effect_damage"]["FROST_DAMAGE"]
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['FROST_DAMAGE']} [bold blue]frost damage[/bold blue]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 3:
                enemy.health -= vars.effects["effect_damage"]["SHOCK_DAMAGE"]
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} takes {vars.effects['effect_damage']['SHOCK_DAMAGE']} [bold blue]shock damage[/bold blue]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 4:
                # Enemy icon turns into normal floor icon
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} is now [bold #f2d2fe]invisible[/bold #f2d2fe]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 5:
                # Enemy chance of missing and not pursuing the player is higher
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} is now [bold #4a412f]blind[/bold #4a412f]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            elif effect['id'] == 6:
                # Only effect on Dragons and Mages - can't attack for duration
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} is now [bold #a020f0]silenced[/bold #a020f0]!")
                time.sleep(vars.settings["delay_enemy_status_effect"])
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                enemy.status_effects.remove(effect)
                time.sleep(vars.settings["delay_enemy_status_effect"])
                console.print(f"{enemy.type['name']} is no longer affected by {effect['effect']}.")
                time.sleep(vars.settings["delay_enemy_status_effect"])
    
def handle_loot(enemy):
    if enemy.loot_type == 'weapon':
        if enemy.weapon:
            time.sleep(vars.settings["delay_enemy_drop_loot"])
            console.print(f"The {enemy.type['name']} dropped a weapon and you pick it up!")
            time.sleep(vars.settings["delay_enemy_drop_loot"])
            # Ensure the weapon is marked as identified when dropped by enemies
            enemy.weapon['identified'] = False
            enemy.weapon['name'] = f"Shrouded {enemy.weapon['type'].capitalize()}"

            vars.player['inventory'].append(enemy.weapon)
    elif enemy.loot_type == 'magical':
        magical_items = [item for item in vars.items if item['type'] in ['weapon', 'accessory'] and 'magic' in item.get('effect', '')]
        if magical_items:
            drop = random.choice(magical_items)
            drop = drop.copy()
            drop['identified'] = False
            drop['name'] = f"Shrouded {drop['type'].capitalize()}"
            vars.player['inventory'].append(drop)
            time.sleep(vars.settings["delay_enemy_drop_loot"])
            console.print(f"The {enemy.type['name']} dropped a mysterious {drop['type']} and you pick it up!")
            time.sleep(vars.settings["delay_enemy_drop_loot"])
    elif enemy.loot_type == 'treasure':
        loot = random.choice([item for item in vars.items if item['type'] in ['money', 'potion']])
        if loot['type'] == 'money':
            amount = loot['amount'] + random.randint(-10, 10)
            amount = max(5, amount)
            vars.player['gold'] += amount
            time.sleep(vars.settings["delay_enemy_drop_loot"])
            console.print(f"The {enemy.type['name']} dropped something valuable and you pick it up!")
            time.sleep(vars.settings["delay_enemy_drop_loot"])
        else:
            loot = loot.copy()
            if loot['type'] in ['tool']:
                loot['identified'] = False
                loot['name'] = f"Shrouded {loot['type'].capitalize()}"
            vars.player['inventory'].append(loot)
            time.sleep(vars.settings["delay_enemy_drop_loot"])
            console.print(f"The {enemy.type['name']} dropped something and you pick it up!")
            time.sleep(vars.settings["delay_enemy_drop_loot"])
    time.sleep(vars.settings["delay_enemy_drop_loot"])