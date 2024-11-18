
from utils import display_dungeon
from vars import console
import random
import time
import vars

def find_treasure():
    display_dungeon()
    console.print(vars.message["ui"]['bottom_lines']['instructions']["play_options"])
    loot = random.choice([item for item in vars.items if item['type'] == 'money'])
    amount = loot['amount'] + random.randint(-5, 5)
    amount = max(1, amount)  # Ensure at least 1 gold
    vars.player['gold'] += amount
    vars.player['gold_collected'] += amount
    console.print(vars.message["notification"]["found_loot"].format(loot=loot['name'], amount=amount))
    time.sleep(vars.settings["delay_find_treasure"])

def find_item(y, x):
    display_dungeon()
    console.print(vars.message["ui"]['bottom_lines']['instructions']["play_options"])
    item = vars.items_on_floor.get((y, x))
    if item:
        item = item.copy()  # Create a copy to avoid modifying the original
        if item['type'] in ['weapon', 'armor', 'accessory']:
            item['identified'] = False
            item['name'] = f"Shrouded {item['type'].capitalize()}"
        vars.player['items_collected'] += 1
        vars.player['inventory'].append(item)
        console.print(vars.message["notification"]["found_item"].format(item=item['name']))
    else:
        console.print("You found nothing.")
    time.sleep(vars.settings["delay_find_item"])

def equip_item(item):
    
    from player import update_player_stats
    
    """Equip an item (weapon, armor, or accessory). The old item is re-added to the inventory."""
    # Check if the item is equipable
    if item['type'] not in ['weapon', 'armor', 'accessory']:
        console.print(f"{item['name']} cannot be equipped.")
        return

    # Determine the slot (weapon, armor, or accessory)
    slot = item['type']

    # Unequip the currently equipped item in the slot, if any
    if vars.player['equipped'][slot]:
        old_item = vars.player['equipped'][slot]
        vars.player['inventory'].append(old_item)  # Add the old item back to the inventory
        console.print(f"Unequipped {old_item['name']} and returned it to your inventory.")

    # Equip the new item
    vars.player['equipped'][slot] = item
    vars.player['inventory'].remove(item)  # Remove the new item from the inventory
    console.print(f"Equipped {item['name']}.")

    # Optional: Update player stats if the item has specific effects
    update_player_stats()

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