from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("LCCB Ryo")
unit.sp = 45

total : int = 0
count : int = 2000
poises = [(0,0), (5,3), (8,4), (12, 6), (15, 7), (99,99)]
for poise in poises:
    for _ in range(count):
        total += rotations.lccb_ryo_rotation(unit, enemy, False, poise, False)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0

