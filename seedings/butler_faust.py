import sys
sys.path.append(".")


from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import molar_ish_rotation
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Butler Faust")
unit.sp = 45

total = 0
count = 2000

sinkings : list[tuple[int, int]] = [(0,0), (5,3), (0,0), (5, 3), (10,8), (99,99)]
echoes : list[int] = [0, 0, 2, 2, 0, 2]
passive_active : bool = True

for i, sinking in enumerate(sinkings):
    echo = echoes[i]
    for _ in range(count):
        total += rotations.butler_faust_rotation(unit, enemy, False, sinking, echo, passive_active)
    print(f'{unit.name} average : {total/count:0.0f}({sinking = }, {echo = })')
    total = 0