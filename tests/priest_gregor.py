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

unit = get_unit("Priest Gregor")
unit.sp = 45

total = 0
count = 2000
bleed_seed : int = 4

bleed : tuple[int, int]
bleed_drain : int
bloodfeast_start : int
hp_percent : float
match bleed_seed:
    case 0:
        hp_percent = 1
        bleed_drain = 6
        bleed = (0,0)
        bloodfeast_start = 0
    case 1:
        hp_percent = 0.85
        bleed_drain = 6
        bleed = (3,3)
        bloodfeast_start = 0
    case 2:
        hp_percent = 0.7
        bleed_drain = 4
        bleed = (6,6)
        bloodfeast_start = 0
    case 3:
        hp_percent = 0.55
        bleed_drain = 2
        bleed = (12,8)
        bloodfeast_start = 0
    case 4:
        hp_percent = 0
        bleed_drain = 0
        bleed = (99,99)
        bloodfeast_start = 999



#hp_percent : float = 1
hand_start : int = 30 #unused
total_bloodfeast_consumed : int = 0
bloodfeast_income : int|None = None

testing : bool = False

for hands in range(0, 31, 10):
    if testing: continue
    for _ in range(count):
        total += rotations.priest_gregor_rotation(unit, enemy, False, bleed, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, hands, bloodfeast_income, hp_percent)
    print(f'{unit.name} average : {total/count:0.0f}({hands = })')
    total = 0

if testing: print(rotations.priest_gregor_rotation(unit, enemy, True, bleed, bleed_drain, bloodfeast_start, total_bloodfeast_consumed, hand_start, bloodfeast_income, hp_percent))