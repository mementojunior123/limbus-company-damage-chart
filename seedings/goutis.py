from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("G Outis")
unit.sp = 45

total = 0
count = 2000

five_sinking : bool = False
slowest_ally : bool = False

unit.skill_1.set_conds([five_sinking])
unit.skill_2.set_conds([slowest_ally])



for _ in range(count):
    total += rotations.normal_rotation(unit, enemy, False)
print(f'{unit.name} average : {total/count:0.0f}')

