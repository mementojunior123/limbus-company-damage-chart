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

unit = get_unit("LCCB Rodya")
unit.sp = 45

total = 0
count = 2000

blunt_odds : list[float] = [-1, 0.25, 0.5, 0.75, 2]
passive_freq : float = 0.5
unhit : bool = True
for blunt_odd in blunt_odds:
    for _ in range(count):
        total += rotations.lccb_rodya_rotation(unit, enemy, False, blunt_odd, passive_freq, unhit)
    print(f'{unit.name} average : {total/count:0.0f}({blunt_odd = })')
    total = 0

