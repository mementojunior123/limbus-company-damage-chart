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

unit = get_unit("G Gregor")
unit.sp = 45

total = 0
count = 2000

s1clash_win : bool = False
rupture_potency : int = 5


unit.skill_1.set_conds([s1clash_win])
rupture_counts : list[int] = [i for i in range(0, 12, 3)] + [15, 99]
for rupture_count in rupture_counts:
    for _ in range(count):
        total += rotations.effects_rotation(unit, enemy, False, {'Rupture' : (rupture_potency if rupture_count else 0, rupture_count)})
    print(f'{unit.name} average : {total/count:0.0f}({rupture_count = })')
    total = 0
