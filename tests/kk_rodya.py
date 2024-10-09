from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("KK Rodya")
unit.sp = 45

total = 0
count = 2000
poise : tuple[int, int] = (0,0)
bleed : int = 99
passive_active : bool = False

for _ in range(count):
    total += rotations.kk_rodya_rotation(unit, enemy, False, poise, passive_active, bleed)
print(f'{unit.name} average : {total/count:0.0f}')
