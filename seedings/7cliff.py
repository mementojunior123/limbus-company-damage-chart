import sys
sys.path.append(".")

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

unit = get_unit("7Cliff")
unit.sp = 45

total = 0
count = 2000
clashing : bool = True
passive : bool = False
unit.skill_2.set_conds([clashing])
passive : backend.SkillEffect = backend.skc.ApplyAdditionalStatus('Rupture', 1, 0)
if passive: unit.apply_effect(passive)
ruptures : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (15, 6), (99,99)]

for rupture in ruptures:
    for _ in range(count):
        total += rotations.effects_rotation(unit, enemy, False, {'Rupture' : rupture})
    print(f'{unit.name} average : {total/count:0.0f}({rupture = })')
    total = 0