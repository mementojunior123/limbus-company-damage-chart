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

unit = get_unit("Oufi Heath")
unit.sp = 45

total = 0
count = 2000

passive : bool = True
decay : bool =  False
tremors = [(0,0), (3,3), (6,4), (9, 4), (12, 6), (32, 6), (99,99)]
for tremor in tremors:
    for _ in range(count):
        total += rotations.oufi_heathcliff_rotation(unit, enemy, False, tremor, passive, decay)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0

#rotations.oufi_heathcliff_rotation(unit, enemy, True, tremor, passive, decay)
