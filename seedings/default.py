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

unit = get_unit("LCB Ish")
unit.sp = 45

total = 0
count = 2000

for _ in range(count):
    total += rotations.normal_rotation(unit, enemy, False)
print(f'{unit.name} average : {total/count:0.0f}')

