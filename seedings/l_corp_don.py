from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("L Don")
unit.sp = 45

total = 0
count = 2000
ruptures = [(0,0), (3,3), (6,3), (10, 6), (99,99)]
does_reuse : bool = False
for rupture in ruptures:
    for _ in range(count):
        total += rotations.l_don_rotation(unit, enemy, False, rupture, does_reuse)
    print(f'{unit.name} average : {total/count:0.0f}({rupture = })')
    total = 0
