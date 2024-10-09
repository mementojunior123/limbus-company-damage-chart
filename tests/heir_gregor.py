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

unit = get_unit("Heir Gregor")
unit.sp = 45

total = 0
count = 2000

passive_frequency : float = 1
start_sp : int = 45
sp_difference : int = 35

sinkings : list[tuple[int, int]] = [(0,0), (4,3), (8,6), (12, 7), (99,99)]
for sinking in sinkings:
    for _ in range(count):
        total += rotations.heir_gregor_rotation(unit, enemy, False, sinking, passive_frequency, sp_difference, start_sp)
    print(f'{unit.name} average : {total/count:0.0f}({sinking=})')
    total = 0

