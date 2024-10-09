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

unit = get_unit("Yuro Ryo")
unit.sp = 45

total = 0
count = 2000
enemy_pot : int = 6
enemy_count : int = 1


enemy_tremor = (enemy_pot, enemy_count)
for tremor in range(0, 21, 5):
    for _ in range(count):
        total += rotations.yuro_ryo_rotation(unit, enemy, False, tremor, enemy_tremor)
    print(f'{unit.name} average : {total/count:0.0f}({tremor = })')
    total = 0

