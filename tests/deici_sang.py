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

unit = get_unit("Deici Sang")
unit.sp = 45

total = 0
count = 2000
sinkings : list[tuple[int, int]] = [(0,0), (4,3), (8,5), (12, 7), (99,99)]
below_50 : bool = True
perfect_rng : bool = True

for sinking in sinkings:
    for _ in range(count):
        total += rotations.deici_sang_rotation(unit, enemy, False, sinking, below_50, perfect_rng)
    print(f'{unit.name} average : {total/count:0.0f}({sinking = })')
    total = 0

