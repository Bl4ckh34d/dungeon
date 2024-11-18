import math
import uuid
import random
import vars
from vars import console

# Enemy class
class Enemy:
    def __init__(self, enemy_type, y, x):
        self.rand = random.randint(0, vars.player['level'])
        self.type = enemy_type
        self.health = enemy_type['base_max_health'] + self.rand * 2
        self.max_health = self.health
        self.attack = enemy_type['base_attack'] + self.rand * 2
        self.defense = enemy_type['base_defense'] + self.rand * 2
        self.pos = [y, x]
        self.symbol = enemy_type['symbol']
        self.status_effects = []
        self.exp = self.health + self.attack + self.defense
        self.gold = self.rand * random.randint(1,15)
        self.loot_type = enemy_type['loot']
        self.weapon = assign_enemy_weapon(enemy_type)
        self.movement_cooldown = enemy_type.get('movement_cooldown', 1)
        self.turns_since_move = 0
        self.shooting_cooldown = enemy_type.get('shooting_cooldown', 1)
        self.turns_since_shot = 0
        self.id = str(uuid.uuid4())
        self.flee_delay = 0  # New attribute to track flee delay

    def delay_after_flee(self):
        """Add a movement delay after player flees."""
        self.flee_delay = 1  # Delay for 1 turn

    def move(self, player_pos):
        # Handle flee delay
        if self.flee_delay > 0:
            self.flee_delay -= 1
            return

        # Handle movement cooldown for slow enemies like Zombies
        if self.movement_cooldown > 1:
            self.turns_since_move += 1
            if self.turns_since_move < self.movement_cooldown:
                return  # Skip movement this turn
            else:
                self.turns_since_move = 0

        # Check if player is invisible
        if any(effect['effect'] == 'invisibility' for effect in vars.player['status_effects']):
            # Player is invisible, enemy moves randomly
            direction = random.choice(list(vars.directions.values()))
            new_y = self.pos[0] + direction[0]
            new_x = self.pos[1] + direction[1]
            if (0 < new_y < vars.settings["dungeon_height"] - 1 and 0 < new_x < vars.settings["dungeon_width"] - 1 and
                vars.dungeon[new_y][new_x] != vars.graphic["wall_char"] and
                vars.dungeon[new_y][new_x] != vars.graphic["secret_wall_char"] and
                not any(e.pos == [new_y, new_x] for e in vars.enemies) and
                [new_y, new_x] != vars.player['pos']):
                self.pos = [new_y, new_x]
        else:
            # Simple AI: if player is in line of sight, move towards player or shoot
            if self.in_line_of_sight(player_pos):
                if self.type['ranged']:
                    self.shoot_projectile(player_pos)
                else:
                    self.move_towards_player(player_pos)
            else:
                # Random movement
                direction = random.choice(list(vars.directions.values()))
                new_y = self.pos[0] + direction[0]
                new_x = self.pos[1] + direction[1]
                if (0 < new_y < vars.settings["dungeon_height"] - 1 and 0 < new_x < vars.settings["dungeon_width"] - 1 and
                    vars.dungeon[new_y][new_x] != vars.graphic["wall_char"] and
                    vars.dungeon[new_y][new_x] != vars.graphic["secret_wall_char"] and
                    not any(e.pos == [new_y, new_x] for e in vars.enemies) and
                    [new_y, new_x] != vars.player['pos']):
                    self.pos = [new_y, new_x]

    def move_towards_player(self, player_pos):
        dy = player_pos[0] - self.pos[0]
        dx = player_pos[1] - self.pos[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        step_y = int(round(dy / distance))
        step_x = int(round(dx / distance))

        new_y = self.pos[0] + step_y
        new_x = self.pos[1] + step_x
        if (0 < new_y < vars.settings["dungeon_height"] - 1 and 0 < new_x < vars.settings["dungeon_width"] - 1 and
            vars.dungeon[new_y][new_x] != vars.graphic["wall_char"] and
            vars.dungeon[new_y][new_x] != vars.graphic["secret_wall_char"] and
            not any(e.pos == [new_y, new_x] for e in vars.enemies) and
            [new_y, new_x] != vars.player['pos']):
            self.pos = [new_y, new_x]

    def in_line_of_sight(self, player_pos):
        
        from utils import get_line
        
        # Line of sight in 360 degrees
        path = get_line(self.pos[1], self.pos[0], player_pos[1], player_pos[0])
        for x, y in path:
            if vars.dungeon[y][x] == vars.graphic["wall_char"] or vars.dungeon[y][x] == vars.graphic["secret_wall_char"]:
                return False
            if [y, x] == player_pos:
                return True
        return False

    def shoot_projectile(self, player_pos):
        # Handle shooting cooldown
        self.turns_since_shot += 1
        if self.turns_since_shot < self.shooting_cooldown:
            return
        else:
            self.turns_since_shot = 0

        dy = player_pos[0] - self.pos[0]
        dx = player_pos[1] - self.pos[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        direction = (int(round(dy / distance)), int(round(dx / distance)))

        # Assign projectile symbol based on enemy or weapon
        if self.type['name'] == 'Orc':
            symbol = '[yellow]➹[/yellow]'  # Arrow symbol
        elif self.type['name'] == 'Dragon':
            symbol = '[red]🔥[/red]'  # Fire symbol
        elif self.type['name'] == 'Mage':
            symbol = '[cyan]✨[/cyan]'  # Magic symbol
        else:
            symbol = '[grey]•[/grey]'  # Default projectile symbol

        projectile = {
            'pos': self.pos.copy(),
            'direction': direction,
            'symbol': symbol,
            'owner_type': 'enemy',
            'owner_id': self.id
        }
        vars.projectiles.append(projectile)

    def to_dict(self):
        return {
            'type_name': self.type['name'],
            'health': self.health,
            'max_health': self.max_health,
            'attack': self.attack,
            'defense': self.defense,
            'pos': self.pos,
            'status_effects': self.status_effects,
            'exp': self.exp,
            'gold': self.gold,
            'loot_type': self.loot_type,
            'weapon': self.weapon,
            'movement_cooldown': self.movement_cooldown,
            'turns_since_move': self.turns_since_move,
            'shooting_cooldown': self.shooting_cooldown,
            'turns_since_shot': self.turns_since_shot,
            'id': self.id
        }

    @classmethod
    def from_dict(cls, enemy_dict):
        # Find the enemy type from the list based on name
        enemy_type = next((et for et in vars.enemy_types_list if et['name'] == enemy_dict['type_name']), None)
        if not enemy_type:
            console.print(vars.message["warning"]["unknown_enemy_type"].format(type=enemy_dict['type_name']))
            return None
        enemy = cls(enemy_type, enemy_dict['pos'][0], enemy_dict['pos'][1])
        enemy.health = enemy_dict['health']
        enemy.max_health = enemy_dict['max_health']
        enemy.attack = enemy_dict['attack']
        enemy.defense = enemy_dict['defense']
        enemy.status_effects = enemy_dict['status_effects']
        enemy.exp = enemy_dict['exp']
        enemy.gold = enemy_dict['gold']
        enemy.loot_type = enemy_dict['loot_type']
        enemy.weapon = enemy_dict['weapon']
        enemy.movement_cooldown = enemy_dict['movement_cooldown']
        enemy.turns_since_move = enemy_dict['turns_since_move']
        enemy.shooting_cooldown = enemy_dict.get('shooting_cooldown', 1)
        enemy.turns_since_shot = enemy_dict.get('turns_since_shot', 0)
        enemy.id = enemy_dict.get('id', str(uuid.uuid4()))
        return enemy

def assign_enemy_weapon(enemy_type):
    # Only assign weapons to enemies that can have weapons
    if enemy_type['loot'] not in ['weapon', 'magical']:
        return None

    # Random chance to not have a weapon (50% for most enemies)
    weapon_chance = {
        'm': 0.8,  # Mages have 80% chance to have a weapon (staff/wand)
        's': 0.7,  # Skeletons have 70% chance to have a weapon
        'b': 0.6,  # Goblins have 60% chance to have a weapon
        'o': 0.6,  # Orcs have 60% chance to have a weapon
        'k': 0.5,  # Kobolds have 50% chance
    }.get(enemy_type['key'], 0)  # Default 0% chance for other enemies
    
    if random.random() > weapon_chance:
        return None

    # Calculate enemy power level based on stats to determine appropriate weapon rarity
    power_level = (enemy_type['base_max_health'] + enemy_type['base_attack'] + enemy_type['base_defense']) / 20
    min_rarity = max(1, min(round(power_level), 8))

    # Get all weapons that match the minimum rarity criteria
    possible_weapons = [item for item in vars.items if item['type'] == 'weapon' 
                       and item.get('rarity', 1) >= min_rarity 
                       and item.get('rarity', 1) <= min_rarity + 2]
    
    # Filter based on ranged vs melee preference
    if enemy_type.get('ranged', False):
        # Ranged enemies can use both, but prefer ranged weapons (70% chance for ranged)
        if random.random() < 0.7:
            ranged_weapons = [w for w in possible_weapons if w.get('range', False)]
            if ranged_weapons:  # If we found ranged weapons, use those
                possible_weapons = ranged_weapons
    else:
        # Melee enemies only use melee weapons
        possible_weapons = [w for w in possible_weapons if not w.get('range', False)]
    
    # Special handling for specific enemy types
    if enemy_type['key'] == 'm':  # Mage prefers elemental weapons and staffs
        elemental_weapons = [w for w in possible_weapons if w.get('effect') in ['burn', 'freeze', 'shock'] 
                           or w.get('name', '').lower() in ['staff', 'wand']]
        if elemental_weapons:
            possible_weapons = elemental_weapons
    elif enemy_type['key'] == 's':  # Skeleton prefers bows and physical weapons
        preferred_weapons = [w for w in possible_weapons if 'bow' in w.get('name', '').lower() 
                           or (not w.get('effect') and not w.get('range', False))]
        if preferred_weapons:
            possible_weapons = preferred_weapons
    elif enemy_type['key'] == 'b':  # Goblins prefer bows if ranged
        if enemy_type.get('ranged', False):
            bow_weapons = [w for w in possible_weapons if 'bow' in w.get('name', '').lower()]
            if bow_weapons:
                possible_weapons = bow_weapons
    elif enemy_type['key'] == 'd':  # Dragons always use fire-based attacks
        fire_weapons = [w for w in possible_weapons if w.get('effect') == 'burn']
        if fire_weapons:
            possible_weapons = fire_weapons
            
    # If we have possible weapons, choose one randomly
    if possible_weapons:
        return random.choice(possible_weapons).copy()
    
    # Fallback to basic weapons if no suitable weapons found
    basic_weapons = [item for item in vars.items if item['type'] == 'weapon' and item.get('rarity', 1) == 1]
    return random.choice(basic_weapons).copy() if basic_weapons else None