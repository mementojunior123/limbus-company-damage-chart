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

unit = get_unit("Cap Ish")
unit.sp = 45

total = 0
count = 2000

poises : list[tuple[int, int]] = [(0,0), (5,3), (8,4), (12, 6), (15, 7), (99,99)]
pride_res : int = 6
missing_hp : float = 1

bleed : int = 10
passive_active : bool = True

for poise in poises:

    for _ in range(count):
        total += rotations.cap_ish_rotation(unit, enemy, False, poise, pride_res, bleed, passive_active, missing_hp)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0
