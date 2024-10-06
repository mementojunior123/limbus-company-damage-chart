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

unit = get_unit("Deici Lu")
unit.sp = 45

total = 0
count = 2000
insight : int = 1
for _ in range(count):
    total += rotations.deici_lu_rotation(unit, enemy, False, insight)
print(f'{unit.name} average : {total/count:0.0f}')
