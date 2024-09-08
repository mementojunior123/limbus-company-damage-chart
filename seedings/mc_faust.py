from math import floor
import backend
from backend import Skill, Enemy, Unit
import rotations
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

enemy = get_enemy("Test")

unit = get_unit("MC Faust")
unit.sp = 45

total = 0
count = 2000
charge_pot : int = 0

charge_consumed : int = (charge_pot - 1) * 10 if charge_pot > 0 else 0
s2_envy_res_count : int = 2
crack_cliff_potency : int = 3
passive_active : bool = False

for charge in range(0, 21, 5):
    for _ in range(count):
        total += rotations.mcfaust_rotation(unit, enemy, False, passive_active, s2_envy_res_count, 
                                            charge, charge_pot, charge_consumed, crack_cliff_potency)
    print(f'{unit.name} average : {total/count:0.0f}({charge = })')
    total = 0