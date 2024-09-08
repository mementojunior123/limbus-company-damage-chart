from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import bl_faust_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Bl Faust")
unit.sp = 45

total = 0
count = 2000
poises : list[tuple[int, int]] = [(0,0), (5,3), (8,6), (12, 8), (15, 10), (99,99)]
bl_meur : int = 2
plum : int = 10
for poise in poises:
    for _ in range(count):
        total += bl_faust_rotation(unit, enemy, False, poise, True, plum, bl_meur)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0