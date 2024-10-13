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

unit = get_unit("Butterfly Sang")
unit.sp = 45

total = 0
count = 2000

butterflies : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (10,10), (15,15)]
butterfly : tuple[int, int] = butterflies[0]

highest_res : int = 0
isares : bool = False

ammo : tuple[int, int] = (10,10)
clash_count : int = 2
sinkings : list[tuple[int, int]] = [(0,0), (4,3), (8,6), (10, 8), (99,99)]
for sinking in sinkings:
    for _ in range(count):
        total += rotations.butterfly_sang_rotation(unit, enemy, False, sinking, butterfly, ammo, clash_count, highest_res, isares, exclude_butterfly_damage=True)
    print(f'{unit.name} average : {total/count:0.0f}({sinking = })')
    total = 0

#rotations.butterfly_sang_rotation(unit, enemy, True)