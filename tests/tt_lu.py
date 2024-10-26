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

unit = get_unit("TT Lu")
unit.sp = 45

total = 0
count = 2000
mutilate_reuse : float = 1
for shank_reuse in [0, 0.25, 0.5, 0.75, 1]:
    for _ in range(count):
        total += rotations.ttlu_rotation(unit, enemy, False, shank_reuse, 3, mutilate_reuse, False)
    print(f'{unit.name} average : {total/count:0.0f}({shank_reuse = })')
    total = 0
