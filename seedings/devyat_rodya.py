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

unit = get_unit("Devyat Rodya")
unit.sp = 45

total = 0
count = 2000
trunk : int = 0
ruptures : list[tuple[int, int]] = [(0,0), (3,3), (15,3), (6,6), (15, 6), (99,99)]
rupture : tuple[int, int] = ruptures[5]

for trunk in range(0, 31, 6):
    for _ in range(count):
        total += rotations.devyat_rodya_rotation(unit, enemy, False, trunk, rupture)
    print(f'{unit.name} average : {total/count:0.0f}({trunk=})')
    total = 0