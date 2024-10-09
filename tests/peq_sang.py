from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import simple_poise_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Peq Sang")
unit.sp = 45

total = 0
count = 2000
p_counts : list[tuple[int, int]] = [1, 2, 4, 7, 10, 99]

for p_count in p_counts:
    poise = (20, p_count)
    for _ in range(count):
        total += simple_poise_rotation(unit, enemy, False, poise)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0