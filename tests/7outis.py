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

unit = get_unit("7 Outis")
unit.sp = 45

total = 0
count = 2000

passive_frequency : float = 2

ruptures : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (15,6), (99,99)]
for rupture in ruptures:
    for _ in range(count):
        total += rotations.seven_outis_rotation(unit, enemy, False, rupture, passive_frequency)
    print(f'{unit.name} average : {total/count:0.0f}({rupture = })')
    total = 0

