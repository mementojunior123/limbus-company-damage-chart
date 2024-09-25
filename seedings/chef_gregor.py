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

unit = get_unit("Chef Gregor")
unit.sp = 45

total = 0
count = 2000

s1bind : bool = True
s2speed : bool = False

s3bleed : bool = True

unit.skill_1.set_conds([s1bind])
unit.skill_2.set_conds([s2speed])
unit.skill_3.set_conds([s3bleed])

for _ in range(count):
    total += rotations.normal_rotation(unit, enemy, False)
print(f'{unit.name} average : {total/count:0.0f}')

