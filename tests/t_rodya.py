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

unit = get_unit("T Rodya")
unit.sp = 45

total = 0
count = 2000


enemy_tremor : int = 6
start_mora : int = 2

unit_tremors : list[int] = [i * 5 for i in range(5)] + [99]
start_bind : int = 0
for unit_tremor in unit_tremors:
    for _ in range(count):
        total += rotations.t_rodya_rotation(unit, enemy, False, unit_tremor, enemy_tremor, start_mora, start_bind)
    print(f'{unit.name} average : {total/count:0.0f}({unit_tremor = })')
    total = 0

print()