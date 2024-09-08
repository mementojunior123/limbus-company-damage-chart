from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import hunt_cliff_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit('Wild Cliff')
unit.sp = 45

total = 0
count = 2000

sinking_seeds : list[tuple[int, int]] = [(0,0), (5,3), (10, 8), (99, 99)]
sinking_index : int = 0

coffin_seeds : list[int] = [i * 2 for i in range(6)]
start_sp : int = 45
part_count : int = 1

playstyles : list[str] = ['Coffin Spam', 'Mixed', "No Horse"]
playstyle_index : int = 0

for coffin_seed in coffin_seeds:
    for _ in range(count):
        total += hunt_cliff_rotation(unit, enemy, False, coffin_seed, 0, sinking_seeds[sinking_index], start_sp, part_count, True, playstyles[playstyle_index])

    print(f'{unit.name} average : {total/count:0.2f}(start_coffins = {coffin_seed})')
    total = 0

'''
unit.clear_effects()
unit.clear_statuses()
effects = []

unit.coffin = 10
unit.horse = 3
sinking : backend.StatusEffect = enemy.statuses.get('Sinking')
sinking.potency = 99
sinking.count = 99
effects.append(backend.skc.DynamicBonus(0.6))
effects.append(backend.skc.OffenseLevelUp(3))
effects.append(backend.skc.DynamicBonus(0.15))
unit.sp = 45
print(unit.extra_skills[1].calculate_damage(unit, enemy, True, entry_effects=effects))
'''