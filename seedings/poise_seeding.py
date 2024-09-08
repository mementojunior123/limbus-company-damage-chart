from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Shi Heath")
unit.sp = 45

total = 0
count = 2000

poises = [(0,0), (5,3), (8,5), (12, 7), (15, 8), (99,99)]
for poise in poises:
    for _ in range(count):
        total += rotations.simple_poise_rotation(unit, enemy, False, poise)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0
