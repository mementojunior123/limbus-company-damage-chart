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

unit = get_unit("Zwei Sinclair West")
unit.sp = 45

total = 0
count = 2000

tremors : list[int] = [0, 5, 10, 15, 99]
passive_active : bool = False
start_dl : int = 0

for tremor in tremors:
    for _ in range(count):
        total += rotations.zwei_sinclair_west_rotation(unit, enemy, False, tremor, start_dl, passive_active)
    print(f'{unit.name} average : {total/count:0.0f}({tremor=})')
    total = 0