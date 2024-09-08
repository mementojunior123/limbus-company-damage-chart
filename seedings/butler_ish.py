from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Butler Ish")
unit.sp = 45

total = 0
count = 2000

s2_clash_win : bool = True
passive : bool = True

faster : bool = False

poises = [(0,0), (5,3), (8,5), (12, 7), (15, 8), (99,99)]
for poise in poises:
    for _ in range(count):
        total += rotations.butler_ish_rotation(unit, enemy, False, poise, passive, faster, s2_clash_win)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0
