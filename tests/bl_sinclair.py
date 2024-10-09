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

unit = get_unit("Bl Sinclair")
unit.sp = 45

total = 0
count = 2000

passive_poise : int = 0
bl_meur : int = 2

poises = [(0,0), (5,3), (8,4), (12, 6), (15, 7), (99,99)]
for poise in poises:
    for _ in range(count):
        total += rotations.bl_sinclair_rotation(unit, enemy, False, poise, passive_poise, bl_meur)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0

