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

unit = get_unit("Cinq Meur")
unit.sp = 45

total = 0
count = 2000



passive : bool = False
focusing : bool = False
start_focus : int = 0

rupture : tuple[int, int] = (0,0)
reuse_s3 : bool = True


unit_speed : tuple[int, int] = (4,7)
enemy_speed : tuple[int, int] = (2,4)

poises : list[tuple[int, int]] = [(0,0), (5,3), (8,5), (12, 7), (15, 8), (99,99)]
for poise in poises:
    for _ in range(count):
        total += rotations.cinq_meur_rotation(unit, enemy, False, poise, rupture, unit_speed, enemy_speed, passive, focusing, start_focus, reuse_s3)
    print(f'{unit.name} average : {total/count:0.0f}({poise = })')
    total = 0