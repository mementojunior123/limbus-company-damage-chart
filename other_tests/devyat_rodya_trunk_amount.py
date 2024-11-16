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

unit = get_unit("Devyat Rodya")
unit.sp = 45

count = 2000

testing : bool = False
turn_amount = 10
result : list[int] = [0 for _ in range(turn_amount)]

for trunk in range(1):
    if testing: continue
    for _ in range(count):
        for i, trunk_count in enumerate(rotations.devyat_rodya_trunk_sim(unit, enemy, False, trunk, turn_amount)):
            result[i] += trunk_count
    final_result = [round(trunk_amount / count, 2) for trunk_amount in result]
    print(f'Trunk amount average growth : {final_result}(start_trunk = {trunk})')
    total = 0
    diffs = [round(final_result[i + 1] - final_result[i], 2) for i in range(len(final_result)-1)]
    print(diffs)


if testing: print(rotations.devyat_rodya_trunk_sim(unit, enemy, True))