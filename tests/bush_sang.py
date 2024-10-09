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

unit = get_unit("Bush Sang")
unit.sp = 45

total = 0
count = 2000

part_count : int = 1
passive_active : bool = True
sinking : tuple[int, int] = (99,99)


ignore_deluge_damage : bool = True
for tremor in [0, 3, 6, 9, 12, 99]:
    for _ in range(count):
        total += rotations.bush_sang_rotation(unit, enemy, False, tremor, sinking, ignore_deluge_damage, passive_active, part_count)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0