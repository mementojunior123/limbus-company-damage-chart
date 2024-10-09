from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import pirate_gregor_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Pirate Gregor")
unit.sp = 45

total = 0
count = 2000
poises : list[tuple[int, int]] = [(0,0), (5,3), (8,4), (12, 6), (15, 7), (99,99)]

bleed : tuple[int, int] = (0,0)
bleed_drain : int = 0
coins : int = 4
passive_active : bool = True

for poise in poises:

    for _ in range(count):
        total += pirate_gregor_rotation(unit, enemy, False, poise, bleed, coins, passive_active, bleed_drain)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0

