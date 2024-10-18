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

unit = get_unit("Fang Lu")
unit.sp = 45

total = 0
count = 2000
passive_active : bool = False
enemy_is_bloodfiend : bool = False
enemy_hp_perecent : float = 0.15

is_clashing : bool = True
ruptures : list[tuple[int, int]] = [(0,0), (3,3), (6,6), (15,6), (15,9), (99,99)]
for rupture in ruptures:
    for _ in range(count):
        total += rotations.fang_lu_rotation(unit, enemy, False, rupture, is_clashing, passive_active, enemy_is_bloodfiend, enemy_hp_perecent)
    print(f'{unit.name} average : {total/count:0.0f}({rupture = })')
    total = 0

