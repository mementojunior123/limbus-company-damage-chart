from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import mb_outis_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("MB Outis")
unit.sp = 45

total = 0
count = 2000
burns : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (9, 9), (99,99)]

bullets : int = 7
aoe_count : int = 1

dark_flame_count : int = 0
passive_active : bool = True

for burn in burns:
    for _ in range(count):
        total += mb_outis_rotation(unit, enemy, False, burn, bullets, aoe_count, dark_flame_count, passive_active)
    print(f'{unit.name} average : {total/count:0.0f}({burn = })')
    total = 0