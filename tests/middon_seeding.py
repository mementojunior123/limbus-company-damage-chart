from math import floor
from collections import defaultdict
import backend
from backend import Skill, Enemy, Unit
from rotations import mid_don_rotation
from sys import exit
get_skill = Skill.get_skill
get_enemy = Enemy.get_enemy
get_unit = Unit.get_unit

T = True
F = False

enemy = get_enemy("Test")


unit = get_unit("Mid Don")
unit.sp = 45

total = 0
count = 2000
team : int = 1
mark : bool = True
match team:
    case 0:
        envy_seed = [0 for _ in range(5)]
        envy_defs = [F for _ in range(5)]
        #(min case)
    case 1:
        envy_seed = [2, 2, 2, 1, 2]
        envy_defs = [F, T, F, T, F]
        #chef ryo(2 + F), crack faust(2 + T), R Ish(2 + F), lccb rodya(1, T), peqoud sang(2 + F)
        #(low case)  
    case 2:
        envy_seed = [2, 2, 2, 4, 2]
        envy_defs = [T, T, F ,F ,F]
        #mid meur(2 + T), crack faust(2 + T), R Ish(2 + F), peqcliff(3 + 1(bodysack) + F), peqoud sang(2 + F)
        #(medium case)
    case 3:
        envy_seed = [2, 4, 3, 4, 3]
        envy_defs = [T, F, T, F, F]
        #mid meur(2 + T), nfaust(3 + 1(hex nail) + F), shi ish(3 + T), peqcliff(3 + 1(bodysack) + F), deici rodya(2 + 1(discard), F)
        #(high case)
    case 4:
        envy_seed = [6 for _ in range(5)]
        envy_defs = [F for _ in range(5)]
        #(max case)

for envy_dmg_up in range(6):
    skill_counter = {1 : 0, 2 : 0, 3 : 0, 'Counter' : 0}

    for _ in range(count):
        total += mid_don_rotation(unit, enemy, False, mark, envy_dmg_up, envy_seed, envy_defs, skill_counter)

    print(f'{unit.name} average : {total/count:0.2f}(envy_dmg_up = {envy_dmg_up})')
    total = 0
    '''
    print('Averages: {', end='')
    for skill in skill_counter:
        print(f'{skill} : {skill_counter[skill] / count:0.2f}', end = ', ' if skill != 'Counter' else '')
    print('}')
    '''