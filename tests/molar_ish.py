from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import molar_ish_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Molar Ish")
unit.sp = 45

total = 0
count = 2000

sinkings : list[tuple[int, int]] = [(0,0), (4,3), (8,6), (10, 8), (99,99)]
passive_active : bool = False

for sinking in sinkings:
    for _ in range(count):
        total += molar_ish_rotation(unit, enemy, False, 0, sinking, passive_active)
    print(f'{unit.name} average : {total/count:0.0f}({sinking = })')
    total = 0