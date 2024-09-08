from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import bl_sang_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Bl Sang")
unit.sp = 45

total = 0
count = 2000
poises : list[tuple[int, int]] = [(0,0), (5,5), (10,8), (15, 10), (20, 12), (99,99)]

for poise in poises:

    for _ in range(count):
        total += bl_sang_rotation(unit, enemy, False, poise, True, 2)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0

