from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Hook Lu")
unit.sp = 45

total = 0
count = 2000

speed_rng : tuple[int, int] = (4, 7)

missings : list[float] = [0, 0.5, 1]
for missing in missings:
    for _ in range(count):
        total += rotations.hook_lu_rotation(unit, enemy, False, speed_rng, missing)
    print(f'{unit.name} average : {total/count:0.0f}({missing = })')
    total = 0
