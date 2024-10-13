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

unit = get_unit("Yuro Lu")
unit.sp = 45

total = 0
count = 2000


enemy_tremor : tuple[int, int] = (99, 99)
passive_active : bool = True

reverb_start : bool = False
ignore_reverb : bool = True
for tremor in [0, 5, 10, 15, 99]:
    for _ in range(count):
        total += rotations.tcorp_lu_rotation(unit, enemy, False, tremor, enemy_tremor, passive_active, reverb_start, ignore_reverb)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0


rotations.tcorp_lu_rotation(unit, enemy, False, tremor, enemy_tremor, passive_active, reverb_start, ignore_reverb)