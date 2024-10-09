from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Molar Sinclair")
unit.sp = 45

total : int = 0
count : int = 2000



tremors = [0, 5, 10, 15, 20]
for tremor in tremors:
    for _ in range(count):
        total += rotations.molar_clair_rotation(unit, enemy, False, tremor)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0

