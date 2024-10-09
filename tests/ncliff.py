from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("NCliff")
unit.sp = 45

total : int = 0
count : int = 2000
passive_active : bool = True

if passive_active: unit.apply_effect(backend.skc.CoinPower(1))
for _ in range(count):
    total += rotations.normal_rotation(unit, enemy, False)
print(f'{unit.name} average : {total/count:0.0f}({passive_active = })')
total = 0

#print(unit.skill_3.calculate_damage(unit, enemy, True))