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

unit = get_unit("Mid Meur")
unit.sp = 45

total = 0
count = 2000

mark : bool = True
passive : bool = True

res_4 : bool = False
res_6 : bool = False

for _ in range(count):
    total += rotations.mid_meur_rotation(unit, enemy, False, mark, passive, res_4, res_6)
print(f'{unit.name} average : {total/count:0.0f}')

