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

unit = get_unit("Rose Rodya")
unit.sp = 45

total = 0
count = 2000

passive_active : bool = True
enemy_tremor_count : int = 10

for charge in range(0, 21, 5):
    for _ in range(count):
        total += rotations.rose_rodya_rotation(unit, enemy, False, charge, enemy_tremor_count, passive_active)
    print(f'{unit.name} average : {total/count:0.0f}({charge = })')
    total = 0

