import sys
sys.path.append(".")


from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("T Don")
unit.sp = 45

total = 0
count = 2000


enemy_tremor : int = 10
start_mora : int = 2

unit_tremors : list[int] = [i * 5 for i in range(4)] + [99]
for unit_tremor in unit_tremors:
    for _ in range(count):
        total += rotations.t_don_rotation(unit, enemy, False, unit_tremor, enemy_tremor, start_mora)
    print(f'{unit.name} average : {total/count:0.0f}({unit_tremor = })')
    total = 0