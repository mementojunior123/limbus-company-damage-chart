from math import floor
import backend
from backend import Skill, Enemy, Unit
from rotations import dawn_clair_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("Dawn Clair")
unit.sp = 45

total = 0
count = 2000

burns : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (9,9), (99,99)]
passives : list[str] = []

#passives.append('NFaust')
#passives.append("LCB Hong Lu")
passives.append('LCB Sang')

passive_active : bool = False
wrath_res : int = 0

start_sp : int = 45
start_ego : int = 0

avg_clash_count : int = 2

aoe_count : int = 3
for burn in burns:
    for _ in range(count):
        total += dawn_clair_rotation(unit, enemy, False, passive_active, burn, aoe_count, start_sp, start_ego, wrath_res, avg_clash_count, passives)

    print(f'{unit.name} average : {total/count:0.0f}({burn = })')
    total = 0