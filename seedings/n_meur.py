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

unit = get_unit("N Meur")
unit.sp = 45

total = 0
count = 2000
passive_frequency : float = 2
nail_count : int = 0
below_50 : bool = False

for _ in range(count):
    total += rotations.n_meur_rotation(unit, enemy, False, passive_frequency, below_50, nail_count)
print(f'{unit.name} average : {total/count:0.0f}')

#rotations.n_meur_rotation(unit, enemy, True, passive_frequency, below_50, nail_count)