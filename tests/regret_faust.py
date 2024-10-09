from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Regret Faust")
unit.sp = 45

total = 0
count = 2000

max_AOE : int = 3
enemy_tremor : int = 67
status_count : int = 0

for tremor in range(0, 21, 5):
    for _ in range(count):
        total += rotations.regret_rotation(unit, enemy, False, tremor, max_AOE, enemy_tremor, status_count)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0

