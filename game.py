from vars import console
from threading import Thread
import platform
import os
import random
import vars
import time
import sys
import json
import subprocess

# Helper function to stop FFmpeg
def stop_music():
    try:
        if platform.system() == "Windows":
            # Redirect error output to null to suppress error messages
            os.system("taskkill /IM ffmpeg.exe /F >nul 2>&1")
        else:
            os.system("pkill ffmpeg >/dev/null 2>&1")
    except Exception:
        pass  # Ignore any errors during music stopping
        
class MusicPlayer:
    def __init__(self):
        self.process = None
        self.is_playing = False

    def play(self, file):
        """Start playing music file using FFplay"""
        if self.is_playing:
            self.stop()
            
        try:
            if platform.system() == "Windows":
                # Hide the console window on Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loop", "0", file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo
                )
            else:
                self.process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loop", "0", file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            self.is_playing = True
        except FileNotFoundError:
            console.print("[yellow]Warning: FFplay not found. Music will be disabled.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not play music: {str(e)}[/yellow]")

    def stop(self):
        """Gracefully stop the music"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)  # Wait up to 1 second for graceful termination
            except subprocess.TimeoutExpired:
                self.process.kill()  # Force kill if it doesn't terminate
            finally:
                self.process = None
                self.is_playing = False

# Global music player instance
music_player = MusicPlayer()

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
        music_player.stop()
        sys.exit()
    else:
        console.print()
        console.print(vars.message["game_over"]["thank_you"])
        music_player.stop()
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
    try:
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
                # First check for diagonal movement
                if i + 1 < len(move):
                    current_move = move[i:i+2]
                    if current_move in ['wa', 'aw']:
                        move_player("NW")
                        i += 2
                        # Advance world after movement
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
                                    owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                                    if owner_enemy:
                                        damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                                    else:
                                        damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))
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
                                    vars.projectiles.remove(p)
                                else:
                                    p['pos'] = [new_y, new_x]
                        display_dungeon()  # Redisplay after movement
                        time.sleep(vars.settings["delay_movement_tick"])  # Add delay
                        continue
                    elif current_move in ['wd', 'dw']:
                        move_player("NE")
                        i += 2
                        # Advance world after movement
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
                                    owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                                    if owner_enemy:
                                        damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                                    else:
                                        damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))
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
                                    vars.projectiles.remove(p)
                                else:
                                    p['pos'] = [new_y, new_x]
                        display_dungeon()  # Redisplay after movement
                        time.sleep(vars.settings["delay_movement_tick"])  # Add delay
                        continue
                    elif current_move in ['sa', 'as']:
                        move_player("SW")
                        i += 2
                        # Advance world after movement
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
                                    owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                                    if owner_enemy:
                                        damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                                    else:
                                        damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))
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
                                    vars.projectiles.remove(p)
                                else:
                                    p['pos'] = [new_y, new_x]
                        display_dungeon()  # Redisplay after movement
                        time.sleep(vars.settings["delay_movement_tick"])  # Add delay
                        continue
                    elif current_move in ['sd', 'ds']:
                        move_player("SE")
                        i += 2
                        # Advance world after movement
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
                                    owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                                    if owner_enemy:
                                        damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                                    else:
                                        damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))
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
                                    vars.projectiles.remove(p)
                                else:
                                    p['pos'] = [new_y, new_x]
                        display_dungeon()  # Redisplay after movement
                        time.sleep(vars.settings["delay_movement_tick"])  # Add delay
                        continue

                # If not a diagonal move, handle single character movement
                current_move = move[i]
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
                
                # For non-diagonal moves, advance world after movement
                if current_move in ['w', 's', 'a', 'd']:
                    # Advance world after movement
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
                                owner_enemy = next((e for e in vars.enemies if e.id == p.get('owner_id')), None)
                                if owner_enemy:
                                    damage = max(0, owner_enemy.attack - vars.player['defense'] + random.randint(-2, 2))
                                else:
                                    damage = max(0, 5 - vars.player['defense'] + random.randint(-2, 2))
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
                                vars.projectiles.remove(p)
                            else:
                                p['pos'] = [new_y, new_x]
                    display_dungeon()  # Redisplay after movement
                    time.sleep(vars.settings["delay_movement_tick"])  # Add delay
                i += 1

            # Check for adjacent enemies after all movement is complete
            adjacent_enemies = [enemy for enemy in vars.enemies if is_adjacent(enemy.pos, vars.player['pos'])]
            if adjacent_enemies:
                encounter_enemies(adjacent_enemies)
                if vars.player['health'] <= 0:
                    game_over()
                    return

            # Enemies attack player if adjacent
            adjacent_enemies = [enemy for enemy in vars.enemies if is_adjacent(enemy.pos, vars.player['pos'])]
            if adjacent_enemies:
                encounter_enemies(adjacent_enemies)
                if vars.player['health'] <= 0:
                    game_over()
                    return

            handle_status_effects()

            # Remove dead enemies
            vars.enemies[:] = [e for e in vars.enemies if e.health > 0]

            if vars.player['health'] <= 0:
                break
    except Exception as e:
        console.print(f"\n[red]An error occurred: {str(e)}[/red]")
        console.print("[yellow]The game will now exit safely.[/yellow]")
    finally:
        music_player.stop()
        sys.exit()

if __name__ == "__main__":
    try:
        # Start music playback in a background thread
        music_thread = Thread(target=lambda: music_player.play("music/music.mp3"), daemon=True)
        music_thread.start()
        main_game_loop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Game interrupted by user. Exiting safely...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {str(e)}[/red]")
        console.print("[yellow]The game will now exit safely.[/yellow]")
    finally:
        music_player.stop()
        sys.exit()