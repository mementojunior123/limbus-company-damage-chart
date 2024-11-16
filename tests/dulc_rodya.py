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

unit = get_unit("Dulcinea Rodya")
unit.sp = 45

total = 0
count = 2000

bleed : tuple[int, int]
bleed_drain : int
bloodfeast_start : int
def get_vars(seed : int):
    global bleed_drain, bleed, bloodfeast_start
    match seed:
        case 0:
            bleed_drain = 6
            bleed = (0,0)
            bloodfeast_start = 0
        case 1:
            bleed_drain = 6
            bleed = (3,3)
            bloodfeast_start = 0
        case 2:
            bleed_drain = 4
            bleed = (6,6)
            bloodfeast_start = 0
        case 3:
            bleed_drain = 2
            bleed = (12,8)
            bloodfeast_start = 0
        case 4:
            bleed_drain = 0
            bleed = (99,99)
            bloodfeast_start = 999

total_bloodfeast_consumed : int = 0
bloodfeast_income : int|None = None

bleed_seed : int = 1
AOE : int = 1
thorn_income : int = 0
get_vars(bleed_seed)
testing : bool = False

for thorns in range(0, 31, 5):
    if testing: continue
    for _ in range(count):
        total += rotations.dulc_rodya_rotation(unit, enemy, False, bleed, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, thorns, bloodfeast_income, AOE, thorn_income)
    print(f'{unit.name} average : {total/count:0.0f}({thorns = })')
    total = 0

thorns = 30
if testing: print(rotations.dulc_rodya_rotation(unit, enemy, True, bleed, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, thorns, bloodfeast_income, AOE, thorn_income))