from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("KK Ryo")
unit.sp = 45

total = 0
count = 2000

max_AOE : int = 3
enemy_tremor : int = 67
status_count : int = 0

freqs = [i * 0.25 for i in range(5)]
for passive_frequency in freqs:
    for _ in range(count):
        total += rotations.kk_ryo_rotation(unit, enemy, False, (99,99), 0, passive_frequency)
    print(f'{unit.name} average : {total/count:0.0f}({passive_frequency = })')
    total = 0

