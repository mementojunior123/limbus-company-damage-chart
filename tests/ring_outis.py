from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Ring Outis")
unit.sp = 45

total = 0
count = 2000
bleed : tuple[int, int] = (99,99)
bleed_drain : int = 0
passive_active : bool = True

for effect_count in range(5):
    for _ in range(count):
        total += rotations.ring_outis_rotation(unit, enemy, False, bleed, effect_count, passive_active, (bleed_drain, bleed_drain))
    print(f'{unit.name} average : {total/count:0.0f}({effect_count = })')
    total = 0

