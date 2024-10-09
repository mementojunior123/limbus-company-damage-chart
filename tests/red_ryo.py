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

unit = get_unit("Red Ryo")
unit.sp = 45

total = 0
count = 2000

passive_active : bool = False
infinite_bleed : bool = True
speed_diff : int = 0
enemy_sp : int = 45

bleed : tuple[int, int] = (99,99) if infinite_bleed else (0,0)
bleed_drain : int = 0 if infinite_bleed else 10

for charge in range(0, 21, 5):
    for _ in range(count):
        total += rotations.red_ryo_rotation(unit, enemy, False, charge, charge, passive_active, bleed, bleed_drain, speed_diff, enemy_sp)
    print(f'{unit.name} average : {total/count:0.0f}(eyes and skull = {charge})')
    total = 0