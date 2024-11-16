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

total = 0
count = 2000
ruptures : list[tuple[int, int]] = [(0,0), (3,3), (15,3), (6,6), (15, 6), (99,99)]
rupture : tuple[int, int] = ruptures[0]
start : int = 42
end : int = 42

testing : bool = False
if not testing:
    final_result : list[int] = [0 for _ in range(end - start + 1)]
    for trunk in range(start, end + 1):
        for _ in range(count):
            total += rotations.devyat_rodya_rotation(unit, enemy, False, trunk, rupture, fixed_trunk=True)
        step_result = round(total/count, 2)
        final_result[trunk - start] = step_result
        print(f'{unit.name} average : {total/count:0.0f}({trunk=})', end ='\r')
        total = 0
    ROUND_RESULT : bool = False
    print(final_result if not ROUND_RESULT else [item for item in map(round, final_result)])
else:
    trunk = 0
    rupture = (0,0)
    print(rotations.devyat_rodya_rotation(unit, enemy, True, trunk, rupture, fixed_trunk=True))