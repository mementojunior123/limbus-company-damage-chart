from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import liu_ish_rotation
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Liu Rodya")
unit.sp = 45

total = 0
count = 2000
burns : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (9, 9), (99,99)]
passive_freq : float = 2
slot_priority : bool = True
for burn in burns:
    for _ in range(count):
        total += rotations.liu_rodya_rotation(unit, enemy, False, burn, passive_freq, slot_priority)
    print(f'{unit.name} average : {total/count:0.0f}({burn = })')
    total = 0