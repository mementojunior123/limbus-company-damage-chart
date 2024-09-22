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

unit = get_unit("7 Ryo")
unit.sp = 45

total = 0
count = 50_000
passive_active : bool = False


if passive_active: unit.apply_effect(backend.skc.TypedDamageUp('Slash', 1))
for _ in range(count):
    total += rotations.effects_rotation(unit, enemy, False, {backend.StatusNames.slash_fragile : (0, 0)})
print(f'{unit.name} average : {total/count:0.2f}')

