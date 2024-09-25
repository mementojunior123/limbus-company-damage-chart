import sys
sys.path.append(".")

from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import bl_outis_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Bl Outis")
unit.sp = 45

total = 0
count = 2000

poises : list[tuple[int, int]] = [(0,0), (5,3), (8,4), (12, 6), (15, 7), (99,99)]
bl_meur : int = 2
missing_hp : float = 0.8
passive_active : bool = True

for poise in poises:
    continue
    for _ in range(count):
        total += bl_outis_rotation(unit, enemy, False, poise, passive_active, missing_hp, bl_meur)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0

print(bl_outis_rotation(unit, enemy, True, poise, passive_active, missing_hp, bl_meur))