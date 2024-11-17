from utils import clear_screen
from rich.table import Table
from vars import console
import random
import json
import time
import vars
import sys
import os

# Show menu with Save and Load options
def show_menu():
    
    from player import check_level_up
    
    
    while True:
        clear_screen()
        console.print(vars.message["notification"]["menu_line"])
        console.print()
        console.print(vars.message["notification"]["player_stats"])
        console.print()
        
        weapon = vars.player['equipped']['weapon']
        armor = vars.player['equipped']['armor']
        accessory = vars.player['equipped']['accessory']
        weapon_attack = weapon['attack'] if weapon and 'attack' in weapon else 0
        armor_defense = armor['defense'] if armor and 'defense' in armor else 0
        level = vars.message["notification"]["level"].format(level=vars.player['level'], remaining_exp=check_level_up())
        if (vars.player['health'] > vars.player['max_health'] * (4/5)):
            health = vars.message["notification"]["health1"].format(health=vars.player['health'], max_health=vars.player['max_health'])
        elif (vars.player['health'] < vars.player['max_health'] * (4/5) and vars.player['health'] > vars.player['max_health'] * (3/5)):
            health = vars.message["notification"]["health2"].format(health=vars.player['health'], max_health=vars.player['max_health'])
        elif (vars.player['health'] < vars.player['max_health'] * (3/5) and vars.player['health'] > vars.player['max_health'] * (2/5)):
            health = vars.message["notification"]["health3"].format(health=vars.player['health'], max_health=vars.player['max_health'])
        elif (vars.player['health'] < vars.player['max_health'] * (2/5) and vars.player['health'] > vars.player['max_health'] * (1/5)):
            health = vars.message["notification"]["health4"].format(health=vars.player['health'], max_health=vars.player['max_health'])
        else:
            health = vars.message["notification"]["health1"].format(health=vars.player['health'], max_health=vars.player['max_health'])
        attack = vars.message["notification"]["attack1"].format(attack=vars.player['attack'], weapon_attack=weapon_attack)
        defense = vars.message["notification"]["defense1"].format(defense=vars.player['defense'], armor_defense=armor_defense)
        agility = vars.message["notification"]["agility1"].format(agility=vars.player['agility'])
        wisdom = vars.message["notification"]["wisdom1"].format(wisdom=vars.player['wisdom'])
        awareness = vars.message["notification"]["awareness1"].format(awareness=vars.player['awareness'])
        gold = vars.message["notification"]["gold"].format(gold=vars.player['gold'])
        exp = vars.message["notification"]["exp"].format(exp=vars.player['exp'])
        equipped_weapon = vars.message["notification"]["equipped_weapon"].format(weapon=weapon["name"] if weapon else "")
        equipped_armor = vars.message["notification"]["equipped_armor"].format(armor=armor["name"] if armor else "")
        equipped_accessory = vars.message["notification"]["equipped_accessory"].format(accessory=accessory["name"] if accessory else "")
        status_title = vars.message["notification"]["player_status"].format(
            status=", ".join(
                f"  "+f"{effect['effect']} (Duration: {effect['duration']})"
                for effect in vars.player['status_effects']
            ) if vars.player['status_effects'] else "  No status effects"
        )

        # Limit to the first 5 effects and pad with empty strings
        status_fields = [
            f"{effect['effect']} (Duration: {effect['duration']})"
            for effect in vars.player['status_effects'][:5]
        ]
        status_fields += [""] * (5 - len(status_fields))
        
        enemies_killed = vars.message["notification"]["enemies_killed"].format(count=0)
        items_found = vars.message["notification"]["items_found"].format(count=0)
        shops_visited = vars.message["notification"]["shops_visited"].format(count=0)
        gold_found = vars.message["notification"]["gold_found"].format(count=0)
        items_purchased = vars.message["notification"]["items_purchased"].format(count=0)
        
        element_array = [
            level,
            health,
            "",
            attack,
            defense,
            agility,
            wisdom,
            awareness,
            "",
            gold,
            exp,
            "",
            status_title,
            *status_fields,
            enemies_killed,
            items_found,
            shops_visited,
            gold_found,
            items_purchased 
        ]

        first_column = element_array[:12]
        second_column = element_array[12:]

        # Create a table with two columns
        table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))

        # Define two columns with specified widths
        table.add_column("First Column", width=int(vars.settings["dungeon_width"] / 1.75 ))
        table.add_column("Second Column", width=int(vars.settings["dungeon_width"] / 2 ))

        # Calculate the number of rows needed based on the minimum
        rows = max(vars.settings["min_rows"] - 4, len(first_column), len(second_column))

        # Add rows to the table, including padding if necessary
        for row in range(rows):
            # Get the item from each column if it exists; otherwise, use an empty string
            first_item = first_column[row] if row < len(first_column) else ""
            second_item = second_column[row] if row < len(second_column) else ""
            
            # Add a row to the table
            table.add_row(first_item, second_item)
        
        

        # Print the table (assumes you have a console object)
        console.print(table)
        console.print(equipped_weapon)
        console.print(equipped_armor)
        console.print(equipped_accessory)
        console.print()
        console.print(vars.message["notification"]["menu_control_line"])

        # Input handling code
        choice = console.input(vars.message["notification"]["cursor"]).upper()
        if choice == 'S':
            save_game()
        elif choice == 'L':
            load_game()
        elif choice == 'Q':
            confirm = console.input(vars.message["input"]["sure_quit"]).upper()
            if confirm == 'Y':
                console.print*()
                console.print(vars.message["game_over"]["thank_you"])
                sys.exit()
            else:
                continue
        elif choice == '':
            break
        else:
            console.print(vars.message["warning"]["invalid_choice"])
            time.sleep(vars.settings["delay_invalid_choice"])

# Save game state to a JSON file
def save_game():
    
    from utils import get_limited_input
    
    clear_screen()
    console.print(vars.message["notification"]["save_title"])
    console.print()
    console.print(vars.message['input']['save_name'])
    save_name = get_limited_input(f"{vars.message['notification']['cursor']}", 12).strip()
    if not save_name:
        return
    # Define the directory where you want to save the file
    save_directory = "saves"
    save_name = ''.join(c for c in save_name if c.isalnum() or c in (' ', '_', '-')).rstrip()

    # Ensure the directory exists
    os.makedirs(save_directory, exist_ok=True)

    # Combine the directory path with the filename
    save_filename = os.path.join(save_directory, f"{save_name}.json")

    if os.path.exists(save_filename):
        overwrite = console.input(vars.message["input"]["override_save"]).upper()
        if overwrite != 'Y':
            console.print(vars.message["notification"]["save_canceled"])
            time.sleep(vars.settings["delay_save_game"])
            return
    
    # Convert shops_visited to a list for JSON serialization
    player_copy = vars.player.copy()
    player_copy['shops_visited'] = list(vars.player['shops_visited'])
    
    # Convert items_on_floor keys to strings
    items_on_floor_serializable = {f"{k[0]},{k[1]}": v for k, v in vars.items_on_floor.items()}
    
    game_state = {
        'player': player_copy,
        'dungeon': vars.dungeon,
        'enemies': [enemy.to_dict() for enemy in vars.enemies],
        'projectiles': vars.projectiles,
        'rooms': vars.rooms,
        'secret_rooms': vars.secret_rooms,
        'items_on_floor': items_on_floor_serializable
    }
    
    try:
        with open(save_filename, 'w') as f:
            json.dump(game_state, f, indent=4)
        console.print(vars.message["notification"]["save_successful"].format(filename=save_filename))
    except Exception as e:
        console.print(vars.message["error"]["save_error"].format(error=e))
    time.sleep(vars.settings["delay_save_game"])

def load_game():
    
    from enemy import Enemy
    from utils import clear_screen
    
    clear_screen()
    console.print(vars.message["notification"]["load_game"])
    console.print()
    
    # Define the directory where save files are located
    save_directory = './saves'
    save_files = [f for f in os.listdir(save_directory) if f.endswith('.json')]
    if not save_files:
        console.print(vars.message["notification"]["no_save_file_found"])
        #time.sleep(vars.settings["delay_load_game"])
        #return
    else:
        console.print(vars.message["notification"]["available_save_files"])
    console.print()

    # Create a table with three columns for the save files
    table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))
    table.add_column("Save Files 1", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Save Files 2", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Save Files 3", width=int(vars.settings["dungeon_width"] / 3))

    # Populate the table with save files in three-column format
    save_rows = [
        f"[bold cyan]{idx + 1}.{' ' if idx + 1 < 10 else ''}[/bold cyan] {file}"
        for idx, file in enumerate(save_files)
    ]
    
    # Calculate the number of rows needed for three columns
    rows = max(vars.settings["min_rows"], (len(save_rows) + 2) // 3)

    # Add rows to the table
    for i in range(rows):
        col1 = save_rows[i * 3] if i * 3 < len(save_rows) else ""
        col2 = save_rows[i * 3 + 1] if i * 3 + 1 < len(save_rows) else ""
        col3 = save_rows[i * 3 + 2] if i * 3 + 2 < len(save_rows) else ""
        table.add_row(col1, col2, col3)

    # Print the table and prompt for choice
    console.print(table)
    console.print(vars.message["notification"]["load_game_options"])

    # Get user input
    choice = console.input(vars.message["notification"]["cursor"])

    if choice.isdigit():
        choice = int(choice)
        if 1 <= choice <= len(save_files):
            selected_file = save_files[choice - 1]
            full_path = os.path.join(save_directory, selected_file)  # Full path to load
            
            try:
                with open(full_path, 'r') as f:
                    game_state = json.load(f)
                vars.player = game_state['player']
                
                # Convert shops_visited back to a set
                vars.player['shops_visited'] = set(vars.player['shops_visited'])
                
                vars.dungeon = game_state['dungeon']
                vars.enemies = [Enemy.from_dict(e) for e in game_state['enemies']]
                vars.enemies = [e for e in vars.enemies if e is not None]
                vars.projectiles = game_state['projectiles']
                vars.rooms = game_state['rooms']
                vars.secret_rooms = game_state.get('secret_rooms', [])
                
                # Convert items_on_floor keys back to tuples
                vars.items_on_floor = {tuple(map(int, k.split(','))): v for k, v in game_state.get('items_on_floor', {}).items()}
                
                clear_screen()
                console.print(vars.message["notification"]["load_game"])
                console.print()
                console.print(vars.message["notification"]["available_save_files"])
                console.print()
                console.print(table)
                console.print(vars.message["notification"]["load_game_options"])
                console.print(vars.message["notification"]["load_successful"].format(file=selected_file))
            except Exception as e:
                console.print(vars.message["error"]["load_error"].format(error=e))
            time.sleep(vars.settings["delay_load_game"])

    elif choice.upper() == 'D':
        delete_save()
    elif choice == "":
        time.sleep(vars.settings["delay_load_game"])
        return
    else:
        console.print(vars.message["warning"]["invalid_choice"])
        time.sleep(vars.settings["delay_invalid_choice"])

def delete_save():
    clear_screen()
    console.print(vars.message["notification"]["title_delete"])
    console.print()
    
    # List save files in the "./saves" directory
    save_directory = './saves'
    save_files = [f for f in os.listdir(save_directory) if f.endswith('.json')]
    
    if not save_files:
        console.print(vars.message["notification"]["no_save_file"])
        #time.sleep(vars.settings["delay_delete_save"])
        #return
    else:
        console.print(vars.message["notification"]["which_file_to_delete"])
    console.print()

    # Create a table with three columns for the save files
    table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))
    table.add_column("Save Files 1", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Save Files 2", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Save Files 3", width=int(vars.settings["dungeon_width"] / 3))

    # Populate the table with save files in three-column format
    save_rows = [
        f"[bold cyan]{idx + 1}.{' ' if idx + 1 < 10 else ''}[/bold cyan] {file}"
        for idx, file in enumerate(save_files)
    ]
    
    # Calculate the number of rows needed for three columns
    rows = max(vars.settings["min_rows"], (len(save_rows) + 2) // 3)

    # Add rows to the table
    for i in range(rows):
        col1 = save_rows[i * 3] if i * 3 < len(save_rows) else ""
        col2 = save_rows[i * 3 + 1] if i * 3 + 1 < len(save_rows) else ""
        col3 = save_rows[i * 3 + 2] if i * 3 + 2 < len(save_rows) else ""
        table.add_row(col1, col2, col3)
    
    console.print(table)
    console.print(vars.message["notification"]["which_to_delete"])
    
    choice = console.input(vars.message["notification"]["cursor"])
    if choice.isdigit():
        choice = int(choice)
        if 1 <= choice <= len(save_files):
            selected_file = save_files[choice - 1]
            full_path = os.path.join(save_directory, selected_file)  # Full path to delete
            
            clear_screen()
            console.print(vars.message["notification"]["title_delete"])
            console.print()
            console.print(vars.message["notification"]["which_file_to_delete"])
            console.print()
            console.print(table)
            console.print(vars.message["notification"]["which_to_delete"])
            confirm = console.input(vars.message["input"]["delete_file"].format(file=selected_file)).upper()
            if confirm == 'Y':
                try:
                    os.remove(full_path)
                    console.print(vars.message["notification"]["file_deleted"].format(file=selected_file))
                    load_game()
                except Exception as e:
                    console.print(vars.message["error"]["delete_error"].format(error=e))
            else:
                console.print(vars.message["warning"]["deletion_canceled"])
        elif choice == len(save_files) + 1:
            console.print()
        else:
            console.print(vars.message["warning"]["invalid_choice"])
    elif choice == "":
        load_game()
    else:
        delete_save()

    time.sleep(vars.settings["delay_delete_save"])

def use_item():
    
    from projectiles import fire_ranged_weapon
    from battle import apply_status_effect
    from items import equip_item
    
    clear_screen()
    console.print(vars.message["notification"]["inventory_line"])
    console.print()

    # Create a table with three columns for the inventory display
    table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))

    # Define three columns with a specified width
    table.add_column("Column 1", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Column 2", width=int(vars.settings["dungeon_width"] / 3))
    table.add_column("Column 3", width=int(vars.settings["dungeon_width"] / 3))

    # Check if the inventory is empty
    if vars.player['inventory']:
        # Populate the table with items from the inventory
        columns = 3
        # Calculate the required rows to either fit the inventory or meet min_rows
        rows = max(vars.settings["min_rows"] + 2, (len(vars.player['inventory']) + columns - 1) // columns)

        for row in range(rows):
            row_data = []
            for col in range(columns):
                idx = row * columns + col
                if idx < len(vars.player['inventory']):
                    item = vars.player['inventory'][idx]
                    # Add formatted string with index and item name
                    row_data.append(f"[bright_cyan]{idx + 1}.[/bright_cyan] {item['name']:<25}")
                else:
                    # If there's no item for this cell, add an empty string
                    row_data.append("")

            # Add the row data to the table
            table.add_row(*row_data)

    else:
        # Populate the table with empty rows to meet the minimum row count
        for _ in range(vars.settings["min_rows"] + 1):
            table.add_row("", "", "")

        # Display "no items" message below the table
        console.print("                       You have no items to use.")
    
    # Print the table and divider
    console.print(table)

    # If there are no items, exit the function after displaying the message
    if not vars.player['inventory']:
        console.print(vars.message["notification"]["player_action"])
        time.sleep(vars.settings["delay_cannot_use"])
        return

    console.print(vars.message["notification"]["use_item"])
    
    # User input for item selection
    choice = console.input(vars.message["notification"]["cursor"]).upper()
    if choice == '':
        return
    elif choice.isdigit() and 1 <= int(choice) <= len(vars.player['inventory']):
        clear_screen()
        console.print(vars.message["notification"]["inventory_line"])
        console.print()
        console.print(table)
        console.print(vars.message["notification"]["use_item"])
        item = vars.player['inventory'][int(choice) - 1]
        if item['type'] in ['weapon', 'armor', 'accessory']:
            if not item.get('identified', True):
                console.print(vars.message["notification"]["need_to_identify"])
                time.sleep(vars.settings["delay_need_to_identify"])
                use_item()
        if item['type'] == 'potion':
            if 'heal' in item:
                vars.player['health'] = min(vars.player['max_health'], vars.player['health'] + item['heal'])
                console.print(vars.message["notification"]["recovered_hp"].format(item=item['heal']))
            if 'effect' in item:
                apply_status_effect(vars.player, item['effect'])
            vars.player['inventory'].pop(int(choice) - 1)
        elif item['type'] == 'weapon' and item.get('range', False):
            fire_ranged_weapon(item)
        elif item['type'] in ['weapon', 'armor', 'accessory']:
            equip_item(item)
            vars.player['inventory'].pop(int(choice) - 1)
        else:
            console.print(vars.message["notification"]["cannot_use_item"])
            time.sleep(vars.settings["delay_cannot_use"])
            use_item()
    else:
        use_item()

def show_item_details(item):
    clear_screen()
    console.print(vars.message["notification"]["item_details"])
    console.print()

    # Determine the initial content to be displayed based on the item type
    if item['type'] in ['weapon', 'armor', 'accessory']:
        if not item.get('identified', True):
            details_text = item['flavor_text_unidentified']
        else:
            details_text = item['flavor_text_identified']
    else:
        details_text = item['flavor_text']

    # Print the item details
    console.print(" " + details_text)
    console.print()
    
    # Calculate the current height based on printed lines and add padding if needed
    content_lines = details_text.count('\n') + 4  # Adjust for title and spacing around it
    padding_needed = max(0, vars.settings["min_rows"] + 4 - content_lines)
    
    # Add padding lines to reach the minimum height
    for _ in range(padding_needed):
        console.print()
        
def use_specific_item(item):
    
    from battle import apply_status_effect
    from items import equip_item
    
    if item['type'] == 'potion':
        if 'heal' in item:
            vars.player['health'] = min(vars.player['max_health'], vars.player['health'] + item['heal'])
            console.print(f"You healed for {item['heal']} health!")
        if 'effect' in item:
            apply_status_effect(vars.player, item['effect'])
        vars.player['inventory'].remove(item)
    elif item['type'] in ['weapon', 'armor', 'accessory']:
        equip_item(item)
        vars.player['inventory'].remove(item)
    else:
        console.print("You cannot use this item.")
    time.sleep(vars.settings["delay_use_item"])
    
def identify_item():
    unidentified_items = [item for item in vars.player['inventory'] if not item.get('identified', True)]
    if not unidentified_items:
        console.print("You have no items to identify.")
        return
    console.print("Unidentified items:")
    for idx, item in enumerate(unidentified_items):
        console.print(f"{idx+1}. {item['name']}")
    choice = console.input("Enter the number of the item to identify or hit enter to go back: ").upper()
    if choice == '':
        return
    elif choice.isdigit() and 1 <= int(choice) <= len(unidentified_items):
        item = unidentified_items[int(choice)-1]
        item['identified'] = True
        # Restore original name
        original_item = next((i for i in vars.items if i['type'] == item['type'] and i.get('effect') == item.get('effect') and i.get('attack') == item.get('attack') and i.get('defense') == item.get('defense') and i.get('heal') == item.get('heal') and i.get('mana') == item.get('mana')), None)
        if original_item:
            item['name'] = original_item['name']
            console.print(f"You have identified the {item['name']}!")
        else:
            console.print("Item identification failed.")
    else:
        console.print(vars.message["warning"]["invalid_choice"])
        
def sell_items():
    while True:
        clear_screen()
        console.print(vars.message["notification"]["inventory_line"])
        console.print()
        
        # Create a table with three columns for the inventory display
        table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))

        # Define three columns with specified widths
        table.add_column("Column 1", width=int(vars.settings["dungeon_width"] / 3))
        table.add_column("Column 2", width=int(vars.settings["dungeon_width"] / 3))
        table.add_column("Column 3", width=int(vars.settings["dungeon_width"] / 3))

        if vars.player['inventory']:
            # Calculate the required rows to either fit the inventory or meet min_rows
            columns = 3
            rows = max(vars.settings["min_rows"], (len(vars.player['inventory']) + columns - 1) // columns)

            # Populate the table rows with items from the inventory
            for row in range(rows):
                row_data = []
                for col in range(columns):
                    idx = row * columns + col
                    if idx < len(vars.player['inventory']):
                        item = vars.player['inventory'][idx]
                        # Add formatted string with index and item name
                        sell_price = item.get('value', 10) // 2
                        row_data.append(f"[bright_cyan]{idx+1}.[/bright_cyan] {item['name']:<5} - Sell for [bold yellow]{sell_price} gold[/bold yellow]")
                    else:
                        # If no item for this cell, add an empty string for alignment
                        row_data.append("")

                # Add the row to the table
                table.add_row(*row_data)

            # Print the table and prompt for input
            console.print(table)
            console.print()
            console.print(vars.message["notification"]["sell_item"])
            choice = console.input(vars.message["notification"]["cursor"]).upper()
            
            if choice == '':
                clear_screen()
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(vars.player['inventory']):
                item = vars.player['inventory'].pop(int(choice)-1)
                sell_price = item.get('value', 10) // 2
                vars.player['gold'] += sell_price
                clear_screen()
                console.print(vars.message["notification"]["inventory_line"])
                console.print()
                console.print(table)
                console.print()
                console.print(vars.message["notification"]["sell_item"])
                console.print(vars.message["notification"]["sold_item"].format(item=item['name'], price=sell_price))
                time.sleep(vars.settings["delay_sold"])
            else:
                clear_screen()
        else:
            # Add empty rows to meet the minimum row count if inventory is empty
            for _ in range(vars.settings["min_rows"]):
                table.add_row("", "", "")
            clear_screen()
            console.print(vars.message["notification"]["inventory_line"])
            console.print()
            console.print(vars.message["notification"]["nothing_to_sell"])
            console.print(table)
            console.print()
            console.print(vars.message["notification"]["type_any_key"])
            console.input(vars.message["notification"]["cursor"]).upper()
            break
        
def identify_service(buffer):
    unidentified_items = [item for item in vars.player['inventory'] if not item.get('identified', True)]
    if not unidentified_items:
        console.print("You have no unidentified items.")
        time.sleep(vars.settings["delay_no_unidentified"])
        return
    # Calculate identification price
    weapon_prices = [item['value'] for item in vars.items if item['type'] == 'weapon']
    average_weapon_price = sum(weapon_prices) / len(weapon_prices)
    identify_price = int(average_weapon_price * 0.75)
    console.print(f"Identification service costs [bold yellow]{identify_price} gold[/bold yellow] per item.")
    console.print("Unidentified items:")
    for idx, item in enumerate(unidentified_items):
        console.print(f"[bright_cyan]{idx+1}.[/bright_cyan] {item['name']}")
    choice = console.input("Enter the number of the item to identify or hit return to cancel: ")
    if choice == '':
        return
    elif choice.isdigit() and 1 <= int(choice) <= len(unidentified_items):
        if vars.player['gold'] >= identify_price:
            vars.player['gold'] -= identify_price
            item = unidentified_items[int(choice)-1]
            item['identified'] = True
            # Restore original name
            original_item = next((i for i in vars.items if i['type'] == item['type'] and i.get('effect') == item.get('effect') and i.get('attack') == item.get('attack') and i.get('defense') == item.get('defense') and i.get('heal') == item.get('heal') and i.get('mana') == item.get('mana')), None)
            if original_item:
                item['name'] = original_item['name']
                console.print(f"You have identified the {item['name']}!")
            else:
                console.print("Item identification failed.")
        else:
            console.print("You don't have enough gold!")
        time.sleep(vars.settings["delay_not_enough_gold"])
        clear_screen()
        console.print(buffer)
        identify_service(buffer)
    else:
        console.print(vars.message["warning"]["invalid_choice"])
        time.sleep(vars.settings["delay_invalid_choice"])
        console.print(buffer)
        identify_service(buffer)
        
# Enter shop
def enter_shop(shop_position):    
    shop_id = f"{vars.player['floor']}_{shop_position}"
    first_visit = shop_id not in vars.player['shops_visited']
    if first_visit:
        vars.player['shops_visited'].add(shop_id)
        # Generate and store random shop items for this shop on first visit
        shop_items = random.sample([item for item in vars.items if item['type'] != 'money'], max(int(random.randint(3,13) / vars.player["level"]), 3))
        vars.player['shops_items'][shop_id] = shop_items
    else:
        # Retrieve the previously stored items for this shop
        shop_items = vars.player['shops_items'].get(shop_id, [])

    # Construct static buffer with shop line and greeting
    buffer = f"{vars.message['notification']['shop_line']}\n\n{greet_player(first_visit)}\n\n"

    # Start the interaction loop
    while True:
        clear_screen()
        console.print(buffer)
        
        # Create a table with two columns
        table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))
        table.add_column("Shop Items", width=int(vars.settings["dungeon_width"]))

        # Prepare shop items for the first column
        shop_rows = [
            f"                 [bold cyan]{idx + 1}.[/bold cyan] {item['name']:<25} - [bold yellow]{item.get('value', 10)} gold[/bold yellow]"
            for idx, item in enumerate(shop_items)
        ]

        # Calculate the number of rows needed based on the minimum
        rows = max(vars.settings["min_rows"] - 5, len(shop_rows))

        # Add rows to the table, including padding if necessary
        for row in range(rows):
            # Get the item from each column if it exists; otherwise, use an empty string
            first_item = shop_rows[row] if row < len(shop_rows) else ""
            
            # Add a row to the table
            table.add_row(first_item)

        # Print the table
        console.print(table)

        # Display player's gold and prompt for choice
        console.print()
        console.print(f" You have [bold yellow]{vars.player['gold']} gold[/bold yellow].")
        console.print()
        console.print(vars.message["notification"]["shop_control_line"])

        # Get player input for buying items or other options
        choice = console.input(vars.message["notification"]["cursor"]).upper()
        if choice == '':  # Exit the shop
            break
        elif choice == 'S':
            clear_screen()
            console.print(buffer)
            console.print(table)
            console.print()
            console.print(f" You have [bold yellow]{vars.player['gold']} gold[/bold yellow].")
            console.print()
            console.print(vars.message["notification"]["==="])
            sell_items()
        elif choice == 'I':
            clear_screen()
            console.print(buffer)
            console.print(table)
            console.print()
            console.print(f" You have [bold yellow]{vars.player['gold']} gold[/bold yellow].")
            console.print()
            console.print(vars.message["notification"]["==="])
            buffer2 = f"{buffer}\n{table}\n\n You have [bold yellow]{vars.player['gold']} gold[/bold yellow].\n\n{vars.message['notification']['===']}"
            identify_service(buffer2)
        elif choice.isdigit() and 1 <= int(choice) <= len(shop_items):
            # Buy item directly if a valid number is entered
            idx = int(choice) - 1
            item = shop_items[idx]
            price = item.get('value', 10)
            if vars.player['gold'] >= price:
                vars.player['gold'] -= price
                item = item.copy()
                if item['type'] in ['weapon', 'armor', 'accessory']:
                    item['identified'] = True
                    item['name'] = f"{item['name'].capitalize()}"
                vars.player['inventory'].append(item)

                # Remove the bought item from shop_items and persist this update
                del shop_items[idx]
                vars.player['shops_items'][shop_id] = shop_items  # Update the shop inventory for persistence
                
                console.print(f"You bought [bold #9127e3]{item['name']}[/bold #9127e3]!")
            else:
                console.print("You don't have enough gold!")
            time.sleep(vars.settings["delay_not_enough_gold"])
        else:
            console.print(vars.message["warning"]["invalid_choice"])
            time.sleep(vars.settings["delay_invalid_choice"])
            
def greet_player(first_visit):
    player_class = determine_player_class()
    if first_visit:
        greeting = f"[bold #9127e3]{random.choice(vars.message['shop']['greeting'].get(player_class, ['Welcome to my shop!']))}[/bold #9127e3]\n"
    else:
        greeting = f"[bold #9127e3]{random.choice(vars.message['shop']['generic'])}[/bold #9127e3]\n"
    greeting += f"[bold #9127e3]{random.choice(vars.message['shop']['look_at_my_wares'])}[/bold #9127e3]"
    return greeting

def determine_player_class():
    weapon = vars.player['equipped']['weapon']
    if weapon:
        name = weapon.get('name', '').lower()
        if 'staff' in name or 'wand' in name:
            vars.player['class'] = 'Mage'
        elif 'sword' in name or 'axe' in name:
            vars.player['class'] = 'Warrior'
        elif 'dagger' in name or 'bow' in name or 'crossbow' in name:
            vars.player['class'] = 'Assassin'
    return vars.player['class']

# Show inventory with flavor text
def show_inventory():
    
    from items import equip_item
    
    while True:
        clear_screen()
        console.print(vars.message["notification"]["inventory_line"])
        console.print()
        
        # Create a table with three columns for the inventory display
        table = Table(show_header=False, box=None, show_lines=False, expand=False, padding=(0, 1))

        # Define three columns with specified widths
        table.add_column("Column 1", width=int(vars.settings["dungeon_width"] / 3))
        table.add_column("Column 2", width=int(vars.settings["dungeon_width"] / 3))
        table.add_column("Column 3", width=int(vars.settings["dungeon_width"] / 3))

        if vars.player['inventory']:
            # Calculate the required rows to either fit the inventory or meet min_rows
            columns = 3
            rows = max(vars.settings["min_rows"] + 1, (len(vars.player['inventory']) + columns - 1) // columns)

            # Populate the table rows with items from the inventory
            for row in range(rows):
                row_data = []
                for col in range(columns):
                    idx = row * columns + col
                    if idx < len(vars.player['inventory']):
                        item = vars.player['inventory'][idx]
                        # Add formatted string with index and item name
                        row_data.append(f"[bright_cyan]{idx+1}.[/bright_cyan] {item['name']:<25}")
                    else:
                        # If no item for this cell, add an empty string for alignment
                        row_data.append("")

                # Add the row to the table
                table.add_row(*row_data)

            # Print the table and prompt for input
            console.print(table)
            console.print()
            console.print(vars.message["notification"]["use_item"])
            choice = console.input(vars.message["notification"]["cursor"]).upper()
            
            if choice == '':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(vars.player['inventory']):
                    item = vars.player['inventory'][idx]
                    show_item_details(item)
                    console.print(vars.message["notification"]["show_inventory_control_line"])
                    action = console.input(vars.message["notification"]["cursor"]).upper()
                    if action == 'E':
                        if not item.get('identified', True):
                            console.print("You need to identify this item before equipping it.")
                            time.sleep(vars.settings["delay_need_to_identify"])
                        else:
                            equip_item(item)
                    elif action == 'U':
                        if not item.get('identified', True):
                            console.print("You need to identify this item before using it.")
                            time.sleep(vars.settings["delay_need_to_identify"])
                        else:
                            use_specific_item(item)
                    elif action == '':
                        continue
                    else:
                        time.sleep(vars.settings["delay_invalid_choice"])
                        clear_screen()
                else:
                    console.print("Invalid choice. Please select a valid item index.")
                    time.sleep(vars.settings["delay_invalid_choice"])
            else:
                console.print("Invalid choice. Please enter a number corresponding to an item.")
                time.sleep(vars.settings["delay_invalid_choice"])
        else:
            # Add empty rows to meet the minimum row count if inventory is empty
            for _ in range(vars.settings["min_rows"]):
                table.add_row("", "", "")
            
            console.print(vars.message["notification"]["inventory_empty"])
            console.print(table)
            console.print()
            console.print(vars.message["notification"]["type_any_key"])
            console.input(vars.message["notification"]["cursor"]).upper()
            break