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

unit = get_unit("Barber Outis")
unit.sp = 45

total = 0
count = 2000

bleed_seed : int = 4
part_count : int = 3
bleed : tuple[int, int]
bleed_drain : int
bloodfeast_start : int
passive_frequency : float
match bleed_seed:
    case 0:
        passive_frequency = -1
        bleed_drain = 6
        bleed = (0,0)
        bloodfeast_start = 0
    case 1:
        passive_frequency = 2
        bleed_drain = 6
        bleed = (3,3)
        bloodfeast_start = 0
    case 2:
        passive_frequency = 2
        bleed_drain = 4
        bleed = (6,6)
        bloodfeast_start = 0
    case 3:
        passive_frequency = 2
        bleed_drain = 2
        bleed = (12,8)
        bloodfeast_start = 0
    case 4:
        passive_frequency = 2
        bleed_drain = 0
        bleed = (99,99)
        bloodfeast_start = 999




blood_tinged_blades_start : int = 30#unused
total_bloodfeast_consumed : int = 0
bloodfeast_income : int|None = None

for blades in range(0, 31, 10):
    continue
    for _ in range(count):
        total += rotations.barber_outis_rotation(unit, enemy, False, bleed, passive_frequency, part_count, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, blades, bloodfeast_income)
    print(f'{unit.name} average : {total/count:0.0f}({blades = })')
    total = 0

print(rotations.barber_outis_rotation(unit, enemy, True, bleed, passive_frequency, part_count, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, blades, bloodfeast_income))