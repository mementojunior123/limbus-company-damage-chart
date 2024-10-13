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

unit = get_unit("SunCliff")
unit.sp = 45

total = 0
count = 2000

start_sp : int = -44

s2_cond : bool = True
for blunt_dmg_up in range(4):
    for _ in range(count):
        total += rotations.suncliff_rotation(unit, enemy, False, blunt_dmg_up, start_sp, s2_cond)
    print(f'{unit.name} average : {total/count:0.0f}({blunt_dmg_up = })')
    total = 0

