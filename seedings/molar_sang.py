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

unit = get_unit("Molar Sang")
unit.sp = 45

total = 0
count = 2000

enemy_tremor : int = 20

for tremor in range(0, 21, 5):
    for _ in range(count):
        total += rotations.molar_sang_rotation(unit, enemy, False, tremor, enemy_tremor)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0

#rotations.molar_sang_rotation(unit, enemy, True, tremor, enemy_tremor)