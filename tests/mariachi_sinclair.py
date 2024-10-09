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

unit = get_unit("Mariachi Sinclair")
unit.sp = 45

total = 0
count = 2000
poises : list[tuple[int, int]] = [(0,0), (5,3), (8, 4), (12, 6), (15, 7), (99,99)]

poise : tuple[int, int] = poises[5]
enemy_sp : int = 0

sinkings : list[tuple[int, int]] = [(0,0), (4,3), (8,5), (12, 7), (99,99)]
for sinking in sinkings:
    for _ in range(count):
        total += rotations.mariachi_rotation(unit, enemy, False, poise, sinking, enemy_sp)
    print(f'{unit.name} average : {total/count:0.0f}({sinking=})')
    total = 0

