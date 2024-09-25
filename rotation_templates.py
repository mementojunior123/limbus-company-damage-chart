from backend import Unit, Enemy
import backend
from random import choice, shuffle, randint, random
from math import ceil

def get_bag():
    bag = [1, 1, 1, 2, 2, 3]
    shuffle(bag)
    
    return bag

def normal_rotation(unit : Unit, enemy : Enemy, debug : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def simple_poise_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0)):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)

    for i in range(6):
        unit.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total
        
        
def simple_charge_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.charge = start_charge
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result} (After attack : {unit.charge} charge)')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.charge > 0: unit.charge -= 1

    
    if debug: print("-".join(sequence))
    return total
    

def charge_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_active : bool = True,
                        start_charge : int = 0, start_charge_potency : int = 0, start_charge_consumed : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.charge = start_charge
    unit.charge_potency = start_charge_potency
    unit.charge_consumed = start_charge_consumed
    if passive_active: unit.apply_unique_effect('passive', backend.skc.ChargePotencyConversionPassive(10), True)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if debug: print(f'Before attack: {unit.charge} charge count and {unit.charge_potency} charge potency, {unit.charge_consumed} charge consumed')
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.charge -= 1
        if unit.charge < 0: unit.charge = 0
        
    if debug: print("-".join(sequence))
    return total

def effects_rotation(unit : Unit, enemy : Enemy, debug : bool = False, statuses : dict[str, tuple[int, int]]|None = None, debug_effects : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.clear_effects()
    if statuses is not None:
        for status in statuses:
            enemy.apply_status(status, *statuses[status])
    for i in range(6):
        unit.on_turn_start()
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        if debug_effects:
            for effect_name in enemy.statuses:
                effect : backend.StatusEffect = enemy.statuses[effect_name]
                print(f'({effect_name} : ({effect.potency}, {effect.count}))')
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total