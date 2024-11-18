from vars import console
from threading import Thread
import platform
import os
import random
import vars
import time
import sys
import json

# Helper function to stop FFmpeg
def stop_music():
    if platform.system() == "Windows":
        os.system("taskkill /IM ffmpeg.exe /F")
    else:
        os.system("pkill ffmpeg")
        
# Function to play music using FFmpeg
def play_music(file):
    if platform.system() == "Windows":
        os.system(f'ffplay -nodisp -autoexit -loop 0 "{file}" > nul 2>&1')
    else:
        os.system(f'ffplay -nodisp -autoexit -loop 0 "{file}" > /dev/null 2>&1')

def game_over():
    console.print()
    console.print(vars.message["game_over"]["game_over"])
    choice = console.input(vars.message["input"]["restart_or_quit"]).upper()
    if choice == "R":
        reset_game()
        main_game_loop()
    elif choice == "Q":
        console.print()
        console.print(vars.message["game_over"]["thank_you"])
        stop_music()
        sys.exit()
    else:
        console.print()
        console.print(vars.message["game_over"]["thank_you"])
        stop_music()
        sys.exit()

def reset_game():
    try:
        with open("data/player_base.json", encoding="utf-8") as f:
            vars.player = json.load(f)
    except FileNotFoundError:
        console.print("Error: player_base.json not found.")
        sys.exit()

# Main game loop
def main_game_loop():
    
    from battle import (
        apply_status_effect,
        handle_loot,
        handle_status_effects,
        encounter_enemies
    )
    from menus import (
        show_menu,
        show_inventory
    )
    from utils import display_dungeon, is_adjacent
    from player import move_player, check_level_up
    from dungeon import generate_dungeon
    
    generate_dungeon(vars.player)
    while vars.player['health'] > 0:
        display_dungeon()
        console.print(vars.message["ui"]['bottom_lines']['instructions']["play_options"])
        move = console.input(vars.message["input"]["cursor"]).lower()
        
        # Handle multi-step movement
        i = 0
        while i < len(move):
            current_move = move[i:i+2] if i+1 < len(move) else move[i]
            
            # Handle diagonal movement
            if len(current_move) == 2:
                if current_move in ['wa', 'aw']:
                    move_player("NW")
                    i += 2
                elif current_move in ['wd', 'dw']:
                    move_player("NE")
                    i += 2
                elif current_move in ['sa', 'as']:
                    move_player("SW")
                    i += 2
                elif current_move in ['sd', 'ds']:
                    move_player("SE")
                    i += 2
                else:
                    # If not a valid diagonal move, process first character only
                    current_move = move[i]
                    i += 1
            else:
                i += 1
                # Handle regular movement
                if current_move == "w":
                    move_player("N")
                elif current_move == "s":
                    move_player("S")
                elif current_move == "a":
                    move_player("W")
                elif current_move == "d":
                    move_player("E")
                elif current_move == "i":
                    show_inventory()
                elif current_move == "m":
                    show_menu()

        # Enemies take their turn
        for enemy in vars.enemies:
            enemy.move(vars.player['pos'])
        # Enemies attack player if adjacent
        adjacent_enemies = [enemy for enemy in vars.enemies if is_adjacent(enemy.pos, vars.player['pos'])]
        if adjacent_enemies:
            encounter_enemies(adjacent_enemies)
            if vars.player['health'] <= 0:
                game_over()
                return

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
                    console.print(vars.message["battle"]["notifications"]["player_hit_by_projectile"].format(damage=damage))
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
                    console.print(vars.message["battle"]["notifications"]["enemy_hit_by_projectile"].format(enemy=enemy_hit.type['name'], damage=damage))
                    if weapon and 'effect' in weapon and damage > 0:
                        apply_status_effect(enemy_hit, weapon['effect'])
                    vars.projectiles.remove(p)
                    if enemy_hit.health <= 0:
                        time.sleep(vars.settings["delay_defeated_enemy"] / 2)
                        console.print(vars.message["battle"]["notifications"]["enemy_defeated"].format(type=enemy_hit.type['name'], killed=random.choice(vars.message['battle']['word_variety']['killed'])))
                        rnd1 = random.randint(4, 7)
                        rnd2 = random.randint(4, 7)
                        vars.dungeon[enemy_hit.pos[0]][enemy_hit.pos[1]] = vars.graphic['bloody_floor_char'].format(color=f"[#{rnd1}{rnd2}0000]")
                        vars.player['exp'] += enemy_hit.exp
                        vars.player['enemies_killed'] += 1
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
            encounter_enemies([enemy_at_player])
            if enemy_at_player.health <= 0:
                vars.enemies.remove(enemy_at_player)

        handle_status_effects()

        # Remove dead enemies
        vars.enemies[:] = [e for e in vars.enemies if e.health > 0]

        if vars.player['health'] <= 0:
            break
        
if __name__ == "__main__":
    # Start music playback in a background thread
    music_thread = Thread(target=play_music, args=("music/music1.mp3",), daemon=True)
    music_thread.start()
    main_game_loop()