from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Dead Meur")
unit.sp = 45

total : int = 0
count : int = 2000

clashing : bool = True
unit.skill_2.set_conds([clashing])

ruptures = [(0,0), (3,3), (6,6), (15, 6), (99,99)]
for rupture in ruptures:
    for _ in range(count):
        total += rotations.effects_rotation(unit, enemy, False, {"Rupture" : rupture})
    print(f'{unit.name} average : {total/count:0.0f}({rupture = })')
    total = 0

