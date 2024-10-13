from backend import Unit, Enemy
import backend
from random import choice, shuffle, randint, random
from math import ceil, floor
from rotation_templates import normal_rotation, simple_charge_rotation, simple_poise_rotation, charge_rotation, effects_rotation

def get_bag():
    bag = [1, 1, 1, 2, 2, 3]
    shuffle(bag)
    
    return bag

def deici_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_insight : int = 1,
                   is_perfect : bool = False, worst_rng : bool = False, blunt_damage_up : int = 0, insight_lock : bool = False):
    sequence = [None for i in range(6)]
    if is_perfect: bag = [3,1,2,1,2,1]
    elif worst_rng: bag = [1,1,1,2,2,3]
    else: bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.insight = start_insight
    if blunt_damage_up:
        unit.apply_unique_effect('passive', backend.skc.TypedDamageUp("Blunt", blunt_damage_up), True)

    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if not insight_lock:
            if (a == 3 or a == 2):
                if b == 1:
                    bag.remove(b)
                    unit.insight = b
                else:
                    decision = dashboard[1] #protect skills 2/3 from being discarded with guard
        else:
            if unit.insight != 3:
                if a == 3:
                    decision = b
                    if b != 1:
                        bag.remove(a)
                        unit.insight = a
                elif a == 2:
                    decision = a
                    if b == 1:
                        bag.remove(b)
                        unit.insight = b
            else:
                decision = dashboard[1]
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            if is_perfect: bag += [3,1,2,1,2,1]
            elif worst_rng: bag += [1,1,1,2,2,3]
            else: bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def deici_lu_rotation(unit : Unit, enemy : Enemy, debug : bool = False, starting_insight : int = 1, is_perfect : bool = False):
    sequence = [None for i in range(6)]
    if is_perfect: bag = [3,2,2,1,1,1]
    else: bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.insight = starting_insight
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        if unit.insight == 3: #Case 1: deici lu is already at insight 3
            decision = dashboard[1] #We lock insight
        elif (a == 3): #Case 2: deici lu isnt at insight 3 but there's a discardable skill 3
            decision = b
            if b != 3: #A skill 3 cant discard
                bag.remove(a)
                unit.insight = 3
                
        elif (a == 2) and (b == 2): #Case 3: We have 2 skill 2s on dashboard without insight 3
            decision = a #In this case we choose to protect the skill 2
        else: #Case 4: We have a skill 1 and another skill that can discard on the dashboard
            decision = a #We discard the skill of the lowest rank
            bag.remove(b)
            unit.insight = b

        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:

            if is_perfect: new_bag = [3,2,2,1,1,1]
            else: new_bag = get_bag()
            bag += new_bag
    if debug: print("-".join(sequence))
    return total


def molar_rotation(unit : Unit, enemy : Enemy, debug = False, enemy_tremor = None, unit_tremor = None, is_perfect= False,
                   reverb_active : bool = False, passive_active : bool = False):
    if unit_tremor is None: unit.tremor = 0
    else: unit.tremor = unit_tremor

    if not enemy_tremor is None: enemy.tremor = enemy_tremor
    enemy.reverb = reverb_active
    unit.molar_passive = passive_active

    sequence = [None for _ in range(6)]

    if is_perfect: bag = [2,1,2,1,3,1]
    else: bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)

        decision = a

        if a == 2:
            if b == 1:
                bag.remove(b)
                unit.tremor += 4
            decision = a

        elif a == 3:

            if b == 1: bag.remove(b); unit.tremor += 4 #Case 1: a S1 is discardable
            elif b == 2 and unit.tremor < 10:
                if dashboard[0] == 3: #Case 2: S3 is ready but not enough tremor so we wait for a s1 and we protect the s3 from discard
                    decision = b
                else:
                    decision = a #Case 3: We cant protect the s3 and have to use it early
            else: #Case 4: The skill 3 is ready and the other slot isnt a skill 1
                decision = a
                if b != 3: bag.remove(b)
            

        
        sequence[i] = str(decision)
        if decision != "Guard":
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            if debug: print(result)
            total += result
            bag.remove(decision)
        else:
            if debug: print(decision)

        if len(bag) < 2: 
            if is_perfect: bag += [2,1,2,1,3,1]
            else: bag += get_bag()
        unit.tremor -= 1
        if unit_tremor < 0: unit_tremor = 0
        if enemy.tremor > 99: enemy.tremor = 99

    if debug: print("-".join(sequence))
    return total

def nclair_rotation(unit : Unit, enemy : Enemy, debug = False, start_sp : int = -20, mad_flame : bool = False, 
                    clash_frequency : float = 0.5, fanatic_start : bool = False, average_clash_count : int = 1,
                    perfect_rng = False):
    unit.sp = start_sp
    unit.fanatic = 0 if fanatic_start is False else 1
    sequence = [None for _ in range(6)]

    bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    
    for i in range(6):
        if unit.fanatic:
            has_fanatic = True
        else:
            has_fanatic = False
        unit.fanatic = 0
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)

        decision = a

        if a == 3:
            sp_cost = 15
        elif a == 2:
            sp_cost = 10
        else:
            sp_cost = 7
        
        if unit.sp - sp_cost <= -45:
            decision = 'Guard'
        else:
            decision = a

        if (decision == 2 or decision == 3):
                if has_fanatic:
                    skills[decision].set_conds([True])
                else:
                    skills[decision].set_conds([False])

        sequence[i] = str(decision)
        if decision != "Guard":
            unit.sp -= sp_cost
            if random() <= clash_frequency:
                clash_sp_gain = 10 + (average_clash_count - 1) * 2
                if mad_flame:
                    clash_sp_gain = ceil(clash_sp_gain / 2)
                unit.sp += clash_sp_gain
            if perfect_rng:
                result = skills[decision].calculate_damage(unit, enemy, debug=debug,
                sequence=["Tails" for _ in skills[decision].coins])
            else:
                result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            if debug: print(result)
            total += result
            bag.remove(decision)
        else:
            bag.remove(dashboard[0])
            unit.sp += randint(5, 10)

        if len(bag) < 2: 
            bag += get_bag()

    if debug: print("-".join(sequence))
    return total

def wdon_rotation(unit : Unit, enemy : Enemy, debug = False, start_charge : int = 0):
    unit.charge = start_charge
    sequence = [None for _ in range(6)]

    bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)

        decision = a
        if a == 3 and unit.charge < 10:
            decision = b

        

        

        sequence[i] = str(decision)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        if debug: print(result)
        total += result
        bag.remove(decision)
        unit.charge -= 1


        if len(bag) < 2: 
            bag += get_bag()

    if debug: print("-".join(sequence))
    return total

def wryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0, skill2_cond_count : int = 0):
    unit.charge = start_charge
    sequence = [None for _ in range(6)]

    bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)

        decision = a
        if a == 3 and unit.charge < 7:
            decision = b

        if decision == 2:
            if skill2_cond_count > 0:
                skill2_cond_count -= 1
                unit.skill_2.set_conds([True])
            else:
                unit.skill_2.set_conds([False])

        sequence[i] = str(decision)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        if debug: print(result)
        total += result
        bag.remove(decision)
        if unit.charge > 20 : unit.charge = 20
        unit.charge -= 1


        if len(bag) < 2: 
            bag += get_bag()

    if debug: print("-".join(sequence))
    return total

def peqcliff_rotation(unit : Unit, enemy : Enemy, debug : bool = False, hp_percent : float = 1.0, average_envyres : int = 0, average_hit_taken_ol : int = 0):

    sequence = [None for _ in range(6)]

    bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)

        decision = a
        current_res : int = average_envyres

        if decision == 2:
            current_res += 1

        elif decision == 3:
            if average_envyres >= 3:
                current_res = 6
            elif average_envyres >= 1:
                current_res += 2
            coinpower1 : bool = True if current_res >= 4 else False
            coinpower2 : bool = True if current_res >= 6 else False
            unit.skill_3.set_conds([coinpower1, coinpower2])

        elif decision == 1:
            current_res = 0

        if current_res > 6: current_res = 6
        if current_res < 0: current_res = 0
        ol : int = average_hit_taken_ol
        if ol > 9: ol = 9
        if ol < 0: ol = 0
        match current_res:
            case 0|1:
                ol += 0
            case 2:
                ol += 1
            case 3:
                ol += 3
            case 4|5:
                ol += 5
            case 6:
                ol += 7

        unit.clear_effects()
        if hp_percent != 1 or hp_percent != 1.0: unit.apply_effect(backend.SkillEffect.new("DynamicBonus", 1.0 - hp_percent))
        if ol > 0: 
            unit.apply_effect(backend.SkillEffect.new("OffenseLevelUp", ol))

        sequence[i] = str(decision)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        if debug: print(result)
        total += result
        bag.remove(decision)


        if len(bag) < 2: 
            bag += get_bag()

    if debug: print("-".join(sequence))
    return total

def rcliff_rotation(unit : Unit, enemy : Enemy, debug : bool = False, qs_patience : int = 2,
                    min_speed_rng : int = 3, max_speed_rng : int = 7):
    sequence = [None for _ in range(6)]

    bag = get_bag()

    skills = {1: unit.skill_1, 2:unit.skill_2, 3:unit.skill_3}
    total = 0
    current_haste = 0
    current_atk_powerup = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        speed = randint(min_speed_rng, max_speed_rng) + current_haste
        if current_atk_powerup:
            power_bonus = backend.SkillEffect.new("BasePower", current_atk_powerup)
            unit.apply_effect(power_bonus)
        current_atk_powerup = 0
        current_haste = 0

        if a == 1:
            if bag[2] == 3:
                decision = 'Bodysack'
            else:
                decision = a
        elif a == 2:
            if bag[2] == 3:
                if dashboard[0] == 1:
                    decision = 'Bodysack'
                elif dashboard[0] == 2 and speed < 6 and b == 2:
                    decision = 'Bodysack'
                else:
                    decision = a
            else:
                decision = a
        
        elif a == 3:
            if speed >= 6:
                decision = a
            elif dashboard[0] == 3:
                qs_patience -= 1
                if qs_patience <= 0:
                    decision = a
                else:
                    decision = b

            elif dashboard[1] == 3:
                decision = 'Bodysack'


        if decision == 1:
            pass

        elif decision == 2:
            if speed >= 6:
                unit.skill_2.set_conds([True])
            else:
                unit.skill_2.set_conds([False])

        elif decision == 3:
            if speed >= 6:
                unit.skill_3.set_conds([True])
            else:
                unit.skill_3.set_conds([False])

        
        if decision == 'Bodysack':
            unit.sp -= 10
            result = 26 if randint(1, 100) <= (unit.sp + 50) else 16
            current_haste = 3
            current_atk_powerup = 1
            unit.sp += 10
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)

        sequence[i] = str(decision)    
        if debug: print(result)
        total += result
        if decision == 'Bodysack':
            bag.remove(dashboard[0])
        else:
            bag.remove(decision)


        if len(bag) < 3: 
            bag += get_bag()
        unit.clear_effects()

    if debug: print("-".join(sequence))
    return total

def cinqclair_rotation(unit : Unit, enemy : Enemy, debug : bool, start_poise : tuple[int, int] = (0,0), passive_active : bool = True,
                       speed_range_rng : tuple[int, int] = (4,8), duel_declared : bool = False, enemy_speed_rng : tuple[int, int] = (2,4)
                       ,conds : tuple[bool, bool, bool] = (False, False, False)):
    '''conds are s2 clash win, s3 clash win, s3 single combat'''
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    current_haste = 0
    enemy.sinclair_duel = duel_declared
    min_speed : int = speed_range_rng[0]
    unit.skill_2.set_conds([conds[0]])
    unit.skill_3.set_conds([conds[1], conds[2]])
    for i in range(6):
        max_speed : int = speed_range_rng[1]
        if passive_active:
            max_speed_bonus = 2 * (unit.poise['Count'] // 5)
            if max_speed_bonus < 0: max_speed_bonus = 0
            if max_speed_bonus > 6: max_speed_bonus = 6
            max_speed += max_speed_bonus

        sinclair_speed = randint(min_speed, max_speed) + current_haste
        enemy_speed = randint(*enemy_speed_rng)
        current_haste = 0
        unit.speed = sinclair_speed - enemy_speed
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if decision == 1:
            current_haste = 2
            if enemy.sinclair_duel:
                current_haste += 2
        
        elif decision == 2:
            current_haste = 0
            if enemy.sinclair_duel:
                current_haste += 3

        elif decision == 3:
            current_haste = 2
            if enemy.sinclair_duel:
                current_haste += 1
            enemy.sinclair_duel = True
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise()
    
    if debug: print("-".join(sequence))
    return total

def chefryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, 
                     enemy_max_hp : int = 2000, enemy_missing_hp : int = 0,
                     icca_patience : int = 2, focused_encounter : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()
    enemy.max_hp = enemy_max_hp
    enemy.hp = enemy_max_hp - enemy_missing_hp
    if enemy.hp < 0: enemy.hp = 0

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    current_turn : int = 0
    icca_hold_time : int = 0
    for i in range(6):
        current_turn += 1
        if not focused_encounter:
            enemy.max_hp = enemy_max_hp
            enemy.hp = enemy_max_hp - enemy_missing_hp
            if enemy.hp < 0: enemy.hp = 0

        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        if not focused_encounter:
            decision = a
        elif a == 3:
            if current_turn >= 5:
                decision = a
            elif icca_hold_time >= icca_patience:
                decision = a
            else:
                icca_hold_time += 1
                decision = b
        else:
            decision = a

        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def ringsang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_bleed : tuple[int, int] = (0,0), permanent_effects : int = 0, 
                      passive_active : bool = False, bleed_decay : tuple[int, int] = (2,4), debug_effects : bool = False):
    
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0


    enemy.clear_effects()
    enemy.apply_status('Bleed', start_bleed[0], start_bleed[1])
    for i in range(permanent_effects):
        enemy.apply_status(f'BadEffect{i+1}', 3 , 3)
    current_ol_up : int = 0

    for i in range(6):
        enemy.on_turn_start()
        the_bleed : backend.StatusEffect = enemy.statuses['Bleed']
        the_bleed.consume_count(randint(*bleed_decay))
        if debug_effects:
            for status_name in enemy.statuses:
                effect : backend.StatusEffect = enemy.statuses[status_name]
                if not effect.is_active(): continue
                print(f'{status_name} : ({effect.potency}, {effect.count})', end=', ')
            print(f'(Turn {i + 1})')
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        unit.clear_effects()
        if current_ol_up >= 0:
            ol_up_passive = backend.SkillEffect.new("OffenseLevelUp", current_ol_up)
            unit.apply_effect(ol_up_passive)
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if passive_active and enemy.statuses['Bleed'].potency >= 4:
            current_ol_up = 6
        else:
            current_ol_up = 0
        
        if len(bag) < 2:
            bag += get_bag()
        enemy.on_turn_end()
    if debug or debug_effects: print("-".join(sequence))
    return total

def rish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.charge = start_charge

    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        if a == 3 and unit.charge < 8:
            decision = b
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        unit.charge -= 1
    
    if debug: print("-".join(sequence))
    return total


def ttlu_rotation(unit : Unit, enemy : Enemy, debug : bool = False, shank_reuse_odds : float = 0, max_shank_reuse_count : int = 0,
                   mutilate_reuse_odds : float = 0, mutilate_10_bleed : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if decision == 3:
            unit.skill_3.set_conds([False])

        elif decision == 2:
            if (random() < shank_reuse_odds) and (max_shank_reuse_count > 0):
                max_shank_reuse_count -= 1
                unit.skill_2.set_conds([True])
            else:
                unit.skill_2.set_conds([False])
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)
        if decision == 3:
            if random() < mutilate_reuse_odds:
                sequence[i] = 'Mutilate(reuse)'
                unit.skill_3.set_conds([True])
                enemy.apply_status('Bleed', 0, 0)
                the_bleed : backend.StatusEffect = enemy.statuses.Bleed
                if mutilate_10_bleed:
                    the_bleed.potency = 10
                    the_bleed.count = 10
                else:
                    the_bleed.potency = 0
                    the_bleed.count = 0
                total += unit.skill_3.calculate_damage(unit, enemy, debug=debug)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def blmeur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), 
                    missing_hp : float = 0, tctb_odds : float = 0.0, targets_to_hit : int = 1, dead_allies : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    unit.missing_hp = missing_hp
    if dead_allies >= 3:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland())
        if dead_allies >= 5:
            unit.apply_unique_effect('bonus_poise_gain', backend.skc.GainAdditionalPoise(2, 2))
        else:
            unit.apply_unique_effect('bonus_poise_gain', backend.skc.GainAdditionalPoise(1, 1))
    if targets_to_hit <= 1:
        unit.extra_skills[0].set_conds([True])
    else:
        unit.extra_skills[0].set_conds([False])
    for i in range(6):
        did_TCTB : bool = False
        actual_targets_hit : int = 1
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3:
            if random() < tctb_odds:
                did_TCTB = True

                max_targets_hit : int = 1 + (unit.poise['Potency'] // 7)
                if max_targets_hit > 3: max_targets_hit = 3

                actual_targets_hit = min(targets_to_hit, max_targets_hit)
                if actual_targets_hit < 1: actual_targets_hit = 1

                if actual_targets_hit <= 1:
                    unit.extra_skills[0].set_conds([True])
                else:
                    unit.extra_skills[0].set_conds([False])
                skill_to_use = unit.extra_skills[0]
            else:
                skill_to_use = unit.skill_3
        else:
            skill_to_use = skills[decision]
       
        
        result = skill_to_use.calculate_damage(unit, enemy, debug=debug)
        if did_TCTB:
            total += result * actual_targets_hit
        else:
            total += result

        
        if debug: print(result)
        sequence[i] = str(decision) if not did_TCTB else 'TCTB'
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise()
    
    if debug: print("-".join(sequence))
    return total

def maidryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), max_AOE : int = 1, 
                     passive_active : bool = True, reuse_odds : float = 0, start_bm : int = 0,
                     min_speed : int = 3, max_speed : int = 8):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    
    unit.clear_statuses()
    unit.clear_effects()
    enemy.clear_effects()

    unit.set_poise(*start_poise)
    unit.speed = 0
    enemy.apply_status('BM', 0, start_bm)
    enemy.apply_status('Bind', 0, 0)
    unit.apply_status('Haste', 0, 0)
    if passive_active:
        unit.apply_effect(backend.skc.MaidRyoPassive())
    for i in range(6):
        unit.on_turn_start()
        enemy.on_turn_start()
        the_haste : backend.StatusEffect = unit.statuses['Haste']
        the_bind : backend.StatusEffect = enemy.statuses['Bind']
        ryo_speed = randint(min_speed, max_speed) + the_haste.count
        enemy_speed = randint(2,4) - the_bind.count
        unit.speed = ryo_speed - enemy_speed
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if decision == 2:
            if unit.poise_count >= 6:
                unit.consume_poise(6)
                aoe_count : int = 3 if max_AOE >= 3 else max_AOE
                if aoe_count < 1: aoe_count = 1
            else:
                aoe_count = 1
            if aoe_count == 1:
                unit.skill_2.set_conds([False, False])
            elif aoe_count == 2:
                unit.skill_2.set_conds([True, False])
            elif aoe_count == 3:
                unit.skill_2.set_conds([True, True])

        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        if decision == 2:
            total += result * (aoe_count - 1)
        elif decision == 3:
            if random() < reuse_odds:
                total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()

        unit.on_turn_end()
        unit.consume_poise(1)
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def mcfaust_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_active : bool = True, s2_envy_res : int = 0,
                     start_charge : int = 0, start_charge_potency : int = 0, start_charge_consumed : int = 0, crack_heath_potency : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    #crackcliff logic
    if crack_heath_potency: other_bag = get_bag()
    else: other_bag = None
    #crackcliff logic

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.charge = start_charge
    unit.charge_potency = start_charge_potency
    unit.charge_consumed = start_charge_consumed
    envy_frag : int = 0
    for i in range(6):
        unit.clear_effects()
        if passive_active: unit.apply_effect(backend.skc.MCFaustPassive())
        if envy_frag : unit.apply_effect(backend.skc.TypedDamageUp('Envy', envy_frag))
        envy_frag = 0
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        has_photo : bool = False

        #crackcliff logic
        if other_bag and crack_heath_potency:
            if len(other_bag) >= 2:
                other_dashboard = [other_bag[0], other_bag[1]]
                other_a = max(other_dashboard)
                other_b = min(other_dashboard)
            else:
                other_a = other_bag[0]
            if other_a >= 2:
                unit.apply_effect(backend.skc.Photoelectricity(crack_heath_potency))
                has_photo = True
            other_bag.remove(other_a)
        #crackcliff logic

        if a == 3:
            if b == 2 and unit.charge >= 10:
                decision = b
            elif b == 1 and unit.charge >= 12:
                decision = b
            else:
                decision = a
        if decision == 2:
            if s2_envy_res > 0:
                s2_envy_res -= 1
                unit.skill_2.set_conds([True])
            else:
                unit.skill_2.set_conds([False])

        if debug: print(f'(Before attack) Charge count : {unit.charge}, Charge potency : {unit.charge_potency}, Charge consumed : {unit.charge_consumed}, Photoelctricity : {'Yes' if has_photo else 'No'}') 
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if decision == 3:
            if unit.charge_potency >= 2:
                envy_frag = 2
            else:
                envy_frag = 1
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.charge -= 1
        if unit.charge < 0 : unit.charge = 0
        if unit.charge > 20: unit.charge = 20
    
    if debug: print("-".join(sequence))
    return total

def butler_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_activity : float = 0, does_clash : bool = True, 
                          sinking_start : tuple[int, int] = (0,0), echoes_start : int = 0, enemy_sp : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    enemy.clear_effects()
    unit.clear_effects()
    unit.clear_statuses()

    enemy.apply_status('Sinking', *sinking_start)
    enemy.apply_status(backend.StatusNames.echoes_of_the_manor, 0, echoes_start)
    if debug: print(enemy.statuses[backend.StatusNames.echoes_of_the_manor].count)
    enemy.sp = enemy_sp

    for i in range(6):    
        unit.on_turn_start()
        enemy.on_turn_start()
        
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        unit.clear_effects()
        passive_odds : float = passive_activity + 0.25 if decision == 2 else passive_activity
        if random() < passive_odds:
            unit.apply_effect(backend.skc.ButlerOutisPassive(does_clash))
        
        if decision == 2:
            unit.skill_2.set_conds([does_clash])
        elif decision == 3:
            unit.skill_3.set_conds([does_clash])
        
        if debug:
            print(f'Current sinking : {enemy.statuses.Sinking.potency}, {enemy.statuses.Sinking.count}; Current echoes : {enemy.statuses[backend.StatusNames.echoes_of_the_manor].count}')

        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def warp_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_active : bool = True,
                        start_charge : int = 0, start_charge_potency : int = 0, start_charge_consumed : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.charge = start_charge
    unit.charge_potency = start_charge_potency
    unit.charge_consumed = start_charge_consumed
    unit.charge_barrier = 0
    unit.clear_effects()
    if passive_active: unit.apply_effect(backend.skc.WarpOutisPassive())
    for i in range(6):
        unit.charge += unit.charge_barrier
        unit.charge_barrier = 0
        if unit.charge < 0: unit.charge = 0
        if unit.charge > 20: unit.charge = 20
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3:
            if unit.charge < 7:
                decision = b
            elif unit.charge >= 15:
                decision = a
            elif unit.charge_potency >= 2:
                decision = a
            else:
                decision = b
            if i == 5: decision = a
       
        if debug: print(f'Before attack: {unit.charge} charge count and {unit.charge_potency} charge potency, {unit.charge_consumed} charge consumed')
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.charge -= 1
        if unit.charge < 0: unit.charge = 0
        
    if debug: print("-".join(sequence))
    return total

def mid_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, vengence_mark : bool = False, envy_dmg_up : int = 0,
                     envy_seed : list[int]|None = None, envy_defenses : list[bool]|None = None, skill_counter : dict[int|str, int]|None = None):
    
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    if envy_seed is None: envy_seed = [0 for _ in range(5)]
    if envy_defenses is None: envy_defenses = [False for _ in range(5)]
    envy_dashboard : list[list[bool]] = [None for _ in range(5)]
    for index, seed in enumerate(envy_seed):
        this_dashboard = [True if i < seed else False for i in range(6)]
        shuffle(this_dashboard)
        this_dashboard.append(True if randint(1, 6) <= seed else False)
        envy_dashboard[index] = this_dashboard

    enemy.vengeance_mark = vengence_mark
    unit.apply_unique_effect('passive', backend.skc.MidDonPassive(), True)
    unit.apply_unique_effect('passive2', backend.skc.TypedDamageUp('Envy', envy_dmg_up), True)
    unit.abs_res = 0
    unit.abs_res_type = 'Envy'
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        envy_res = progress_envy_dashboard(envy_dashboard, envy_defenses)
        unit.abs_res = envy_res if envy_res >= 3 else 0
        if unit.abs_res >= 5 and random() < 0.75:
            decision = 'Counter'
            skill_to_use = unit.skills[3]
            unit.abs_res += 1
            envy_res += 1
            
        if decision == 2:
            unit.abs_res += 1
            envy_res += 1
        conv_dict = {0 : 0, 1 : 0, 2 : 1, 3 : 3, 4 : 5, 5 : 5, 6: 7, 7 : 7}
        ol_up : int = conv_dict[envy_res]
        skill_to_use = skills[decision] if decision != 'Counter' else unit.skills[3]
        if skill_to_use.type[1] != 'Envy':
            ol_up = 0
        result = skill_to_use.calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.OffenseLevelUp(ol_up)])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        if skill_counter: skill_counter[decision] += 1
        bag.remove(decision) if decision != 'Counter' else bag.pop(0)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def progress_envy_dashboard(envy_dashboard : list[list[bool]], envy_defenses : list[bool], defense_limit : int = 2) -> int:
    can_envy : list[bool] = [None for _ in range(5)]
    for index, dashboard in enumerate(envy_dashboard):
        if dashboard[0] == True or dashboard[1] == True:
            can_envy[index] = True
        else:
            can_envy[index] = False
    if False not in can_envy:
        for dashboard in envy_dashboard:
            dashboard.remove(True)
        return 5
    did_break : bool = False
    for index, opportunity in enumerate(can_envy):
        if opportunity: continue
        if envy_defenses[index]: defense_limit -= 1
        else: did_break = True; break
    if did_break == False:
        if defense_limit >= 0:
            for dashboard in envy_dashboard:
                if True in dashboard:
                    dashboard.remove(True)
                else:
                    dashboard.pop(0)
            return 5
    
    envy_count : int = 0
    for dashboard in envy_dashboard:
        a, b = dashboard[0], dashboard[1]
        if a != b:
            if random() < 0.75:
                dashboard.remove(False)
            else:
                dashboard.remove(True)
                envy_count += 1
        else:
            dashboard.remove(a)
            envy_count += 1 if a == True else 0
    return envy_count

def regret_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_tremor : int = 0, max_aoe : int = 1, enemy_tremor : int = 0, status_count : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.atk_weight = 1
    unit.tremor = start_tremor
    enemy.tremor = enemy_tremor
    enemy.fake_status_count = status_count + 1
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if decision != 1 and unit.tremor < 5 and max_aoe > 1: decision = b
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result * min(unit.atk_weight, max_aoe)
        
        if debug: print(f'{result} * {unit.atk_weight}')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        unit.tremor -= 1
        if unit.tremor < 0: unit.tremor = 0
    if debug: print("-".join(sequence))
    return total

def liu_ish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_burn : tuple[int, int] = (0,0), passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status('Burn', 0, 0)
    burn_status : backend.StatusEffect = enemy.statuses.Burn
    burn_status.potency, burn_status.count = start_burn
    if burn_status.potency <= 0 or burn_status.count <= 0:
        burn_status.potency = 0
        burn_status.count = 0
    
    
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if random() < passive_frequency:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.LiuIshPassive()])
            total += result
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            total += result

        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def base_heath_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    effects : list[backend.SkillEffect] = []
    used_s2 : bool = False
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        
       
        if random() < passive_frequency:
            effects.append(backend.skc.DynamicBonus(0.1))
        if used_s2:
            effects.append(backend.skc.BasePowerUp(1))
            effects.append(backend.skc.DynamicBonus(0.1))
            
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=effects)
        
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        used_s2 = True if decision == 2 else False

        
        
        if len(bag) < 2:
            bag += get_bag()

        effects.clear()
    if debug: print("-".join(sequence))
    return total

def base_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, enemy_sp : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    used_s3 : bool = False
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if used_s3 and enemy_sp < 0:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.DynamicBonus(0.1)])
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        used_s3 = True if decision == 3 else False
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def base_faust_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        
       
        if random() < passive_frequency:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.DynamicBonus(0.1)])
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)


        
        
        if len(bag) < 2:
            bag += get_bag()

    if debug: print("-".join(sequence))
    return total

def base_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_frequency : float = -1, unit_speed : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    prev_decision : int = 0
    unit.speed = unit_speed
    effects : list[backend.SkillEffect] = []
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        if random() < passive_frequency:
            effects.append(backend.skc.DynamicBonus(0.1))
        if prev_decision == 2:
            effects.append(backend.skc.BasePowerUp(2))
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=effects)
        

        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()

        prev_decision = decision
        effects.clear()
    if debug: print("-".join(sequence))
    return total


def base_ryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_frequency : float = -1, s2_cond_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    prev_decision : int = 0
    effects : list[backend.SkillEffect] = []
    unit.set_poise(0,0)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        if random() < passive_frequency:
            effects.append(backend.skc.DynamicBonus(0.25))

        if random() < s2_cond_frequency:
            unit.skill_2.set_conds([True])
        else:
            unit.skill_2.set_conds([False])

        if prev_decision == 1|3:
            unit.add_poise(2, 0)

        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=effects)
        

        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()

        prev_decision = decision
        effects.clear()
    if debug: print("-".join(sequence))
    return total


def base_lu_rotation(unit : Unit, enemy : Enemy, debug : bool = False, not_hit_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if random() < not_hit_frequency:
            unit.skill_2.set_conds([True])
            unit.skill_3.set_conds([True])
        else:
            unit.skill_2.set_conds([False])
            unit.skill_3.set_conds([False])
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def liu_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_burn : tuple[int, int] = (0,0), passive_frequency : float = -1, 
                       slot_priority : bool = False, passive : backend.SkillEffect = None):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status('Burn', 0, 0)
    burn_status : backend.StatusEffect = enemy.statuses.Burn
    burn_status.potency, burn_status.count = start_burn
    if passive is None: passive = backend.skc.LiuDyaPassive(slot_priority)
    if burn_status.potency <= 0 or burn_status.count <= 0:
        burn_status.potency = 0
        burn_status.count = 0
    unit.skill_2.set_conds([False])
    
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if random() < passive_frequency:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[passive])
            total += result
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            total += result

        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def bl_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), has_passive : bool = False, bl_meur : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    if has_passive:
        passive = backend.skc.DAddXForEachY(1, 'coin_power', 5, 'unit.poise_count', 0, 3)
        unit.apply_unique_effect('passive', passive, True)

    if bl_meur:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland(), True)

    for i in range(6):
        if bl_meur: unit.add_poise(bl_meur, bl_meur)
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if has_passive: unit.add_poise(0, 1)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result}(poise = ({unit.poise_potency}, {unit.poise_count}))')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise()
        #next turn stuff
        if decision == 3 and random() < 0.95:
            unit.add_poise(2, 1)
        elif decision == 2:
            unit.add_poise(1, 2)
        elif decision == 1:
            unit.add_poise(3, 1)
    
    if debug: print("-".join(sequence))
    return total


def hunt_cliff_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_coffin : int = 0, start_horse : int = 0, start_sinking : tuple[int, int] = (0,0), 
                        start_sp : int = 45, max_AOE : int = 1, passive_active : bool = True, playstyle : str = "Coffin Spam", clash_count : int = 2):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3, 'Counter' : unit.extra_skills[0], 4 : unit.extra_skills[1], 3.1 : unit.extra_skills[1]}
    total = 0
    enemy.ruin = 0

    enemy.apply_status('Sinking', 0,0)
    sinking_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.sinking)
    sinking_status.potency, sinking_status.count = start_sinking
    unit.sp = start_sp

    unit.coffin = start_coffin
    unit.horse = start_horse
    unit.corroded = False
    
    effects : list[backend.SkillEffect] = []
    if passive_active: unit.apply_unique_effect("passive", backend.skc.DAddXForEachY(0.01, 'dynamic', 1, 'enemy.statuses.Sinking.potency', 0, 0.15), True)

    for i in range(6):
        if not unit.corroded or True:
            unit.atk_weight = 1
            if unit.horse : effects.append(backend.skc.OffenseLevelUp(3))

            dashboard = [bag[0], bag[1]]
            a = max(dashboard)
            b = min(dashboard)
            if playstyle == "Coffin Spam":
                if not unit.horse:
                    decision = 'Counter'
                else:
                    if unit.sp >= 15:
                        decision = 'Counter'
                    else:
                        decision = a
            elif playstyle == 'Mixed':
                decision = 2 if 2 in dashboard else 'Counter'
            elif playstyle == "No Horse":
                decision = a
            else:
                decision = a
            
            if unit.horse:
                if decision == 'Counter': decision = 4
                if decision == 3: decision = 3.1
        
            unit.sp += 10 + (clash_count-1) * 2
            if unit.sp < -45: unit.sp = -45; unit.corroded = True
            if unit.sp > 45: unit.sp = 45
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            actual_aoe : int = unit.atk_weight if unit.atk_weight <= max_AOE else max_AOE
            total += result * actual_aoe
            
            if debug: print(f'{result} * {actual_aoe} target(s) ||| (sp = {unit.sp}, coffin = {unit.coffin})')
            sequence[i] = str(decision) if decision != 3.1 else '4'
            if decision in [1, 2, 3]: bag.remove(decision)
            elif decision == 'Counter' or decision == 4:
                bag.remove(dashboard[0])
            elif decision == 3.1:
                bag.remove(3)

            
            
            if len(bag) < 2:
                bag += get_bag()
            
            effects.clear()
            if decision == 2 and unit.horse: unit.sp -= 10
            if unit.sp < -45: unit.sp = -45; unit.corroded = True
            if unit.sp > 45: unit.sp = 45
            if unit.horse:
                if decision == 4 or decision == 3.1:
                    unit.horse = 0
                elif decision == 'Counter':
                    unit.horse = 0
                else:
                    if unit.sp <= -25: unit.horse = 0
                    else: unit.horse += 1
                    if unit.horse > 3: unit.horse = 3
                unit.sp -= (15 - unit.coffin // 2)
            else:
                if decision == 'Counter':
                    unit.horse = 1
                    unit.sp -= 5
            
            dmg_up : int = (unit.coffin // 3) * 2
            if dmg_up > 6: dmg_up = 6
            if dmg_up < 0: dmg_up = 0
            effects.append(backend.skc.DamageUp(dmg_up))
            if decision == 'Counter':
                effects.append(backend.skc.OffenseLevelUp(1))
            
            if enemy.ruin > 0: enemy.ruin -= 1
            if decision == 2: enemy.ruin = 2
            
            if unit.sp < -45: unit.sp = -45; unit.corroded = True
            if unit.sp > 45: unit.sp = 45
        else:
            sequence[i] = None
            unit.horse = 0
            unit.sp = 0
            unit.corroded = False
        
        


    
    if debug: print("-".join(sequence))
    return total


def w_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0, has_regret : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.charge = start_charge
    if has_regret:
        unit.apply_unique_effect('passive1', backend.skc.BasePowerUp(-1), True)
        unit.apply_unique_effect('passive2', backend.skc.CoinPower(2), True)
    else:
        unit.clear_effects()
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision > 1 and unit.charge < 5: decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.charge -= 1 if unit.charge > 0 else 0
    
    if debug: print("-".join(sequence))
    return total

def mc_heath_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_active : bool = True,
                        start_charge : int = 0, start_charge_potency : int = 0, start_charge_consumed : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.charge = start_charge
    unit.charge_potency = start_charge_potency
    unit.charge_consumed = start_charge_consumed
    if passive_active: unit.apply_unique_effect('passive', backend.skc.ChargePotencyConversionPassive(10), True)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if a == 3:
            if b == 2 and unit.charge >= 10:
                decision = b


            elif b == 1 and unit.charge >= 16:
                decision = b
            else:
                decision = a
        
        elif a == 2 and b == 1:
            if 2 <= unit.charge <= 4:
                decision = b
       
        if debug: print(f'Before attack: {unit.charge} charge count and {unit.charge_potency} charge potency, {unit.charge_consumed} charge consumed')
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.charge -= 1
        if unit.charge < 0: unit.charge = 0
        
    if debug: print("-".join(sequence))
    return total


def zwei_greg_rotation(unit : Unit, enemy : Enemy, debug : bool = False, perma_def_level : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    next_turn_def_level : int = 0
    for i in range(6):

        unit.def_level = perma_def_level + next_turn_def_level
        next_turn_def_level = 0
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if decision == 2:
            next_turn_def_level = 2
        elif decision == 3:
            next_turn_def_level = 3
        else:
            next_turn_def_level = 0
    
    if debug: print("-".join(sequence))
    return total

def cinq_don_rotation(unit : Unit, enemy : Enemy, debug : bool, passive_frequency : float = -1, duel_declared : bool = False,
                       speed_range_rng : tuple[int, int] = (4,7), enemy_speed_rng : tuple[int, int] = (2,4), avg_clash_count : int = 2):
                       
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.haste = 0
    unit.skill_1.set_conds([True if avg_clash_count else False])

    enemy.don_duel = duel_declared
    min_speed : int = speed_range_rng[0]
    max_speed : int = speed_range_rng[1]
    passive : backend.SkillEffect = backend.skc.AddXForEachY(0.06, 'dynamic', 1, 'unit.speed_diff', 0, 0.3)
    unit.clash_count = avg_clash_count
    for i in range(6):
        

        don_speed = randint(min_speed, max_speed) + unit.haste
        enemy_speed = randint(*enemy_speed_rng)
        unit.haste = 0
        unit.speed = don_speed
        unit.speed_diff = don_speed - enemy_speed
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if random() < passive_frequency:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[passive])
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if enemy.don_duel: unit.haste += 2
        elif decision == 3:
            enemy.don_duel = True
            unit.haste += 1
        
        if len(bag) < 2:
            bag += get_bag()
        
    
    if debug: print("-".join(sequence))
    return total

def rhino_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0, 
                        passive_active : bool = True, speed_rng : tuple[int, int] = (3, 5)):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.charge = start_charge
    
    min_speed : int = speed_rng[0]
    max_speed : int

    for i in range(6):
        max_speed = speed_rng[1]
        if passive_active:
            max_speed_bonus = 2 * (unit.charge // 5)
            if max_speed_bonus < 0: max_speed_bonus = 0
            if max_speed_bonus > 6: max_speed_bonus = 6
            max_speed += max_speed_bonus
        unit.speed = randint(min_speed, max_speed)
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == a and unit.charge < 10: decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result} (After attack : {unit.charge} charge)')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.charge > 0: unit.charge -= 1

    
    if debug: print("-".join(sequence))
    return total

def zwei_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise_count : int = 0, passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(1 if start_poise_count else 0, start_poise_count)
    enemy.next_frag = 0
    for i in range(6):
        if passive_active:
            unit.shield = unit.poise_count * 2
            if unit.shield < 0: unit.shield = 0
            if unit.shield > 20: unit.shield = 20
        else:
            unit.shield = 0

        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if enemy.next_frag:
            enemy.next_frag = 0
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.DynamicBonus(0.1)])
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def pirate_gregor_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), start_bleed : tuple[int, int] = (0,0), 
                           start_coins : int = 0, passive_active : bool = True, bleed_drain : int = 8):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)

    enemy.apply_status('Bleed', 0,0)
    bleed_status : backend.StatusEffect = enemy.statuses.get('Bleed')
    bleed_status.potency, bleed_status.count = start_bleed

    unit.coins = start_coins
    if passive_active:
        unit.apply_unique_effect('passive', backend.skc.PirateGregorPassive(), True)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        bleed_status.consume_count(bleed_drain)
    
    if debug: print("-".join(sequence))
    return total

def kk_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), passive_active : bool = True, enemy_bleed : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.bleed = enemy_bleed
    unit.set_poise(*start_poise)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if passive_active and unit.poise_potency >= 5:
            decision = 3
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision) if decision in bag else bag.remove(dashboard[0])

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def bl_faust_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), passive_active : bool = True, 
                      start_plum : int = 0, bl_meur : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    unit.skill_3.set_conds([True])
    enemy.apply_status(backend.StatusNames.red_plum_blossom, 0, 0)
    enemy.statuses[backend.StatusNames.red_plum_blossom].count = start_plum if start_plum <= 10 else 10

    if passive_active:
        unit.apply_unique_effect('passive', backend.skc.BlFaustPassive(), True)
    if bl_meur:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland(), True)
    for i in range(6):
        if bl_meur: unit.add_poise(bl_meur, bl_meur)
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def warp_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.charge = start_charge
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3 and unit.charge < 10: decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result} (After attack : {unit.charge} charge)')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.charge > 0: unit.charge -= 1

    
    if debug: print("-".join(sequence))
    return total

def seven_faust_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_rupture : tuple[int, int] = (0,0), 
                         is_clashing : bool = True, passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status(backend.StatusNames.rupture, 0,0)
    rupture_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.rupture)
    rupture_status.potency, rupture_status.count = start_rupture
    if passive_active:
        unit.apply_unique_effect('passive', backend.skc.SevenFaustPassive(), True)
    enemy.analyzed = 0
    unit.skill_2.set_conds([is_clashing])
    unit.skill_3.set_conds([is_clashing])
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if enemy.analyzed:
            if randint(1, 3) == 1:
                enemy.phys_res['Slash'] += 0.2
        enemy.analyzed = 0
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        enemy.phys_res['Slash'] = 1
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total


def ring_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_bleed : tuple[int, int] = (0,0), permanent_effects : int = 0, 
                      passive_active : bool = False, bleed_decay : tuple[int, int] = (2,4), debug_effects : bool = False):
    
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0


    enemy.clear_effects()
    enemy.apply_status('Bleed', start_bleed[0], start_bleed[1])
    for i in range(permanent_effects):
        enemy.apply_status(f'BadEffect{i+1}', 3 , 3)

    for i in range(6):
        enemy.on_turn_start()

        the_bleed : backend.StatusEffect = enemy.statuses['Bleed']
        the_bleed.consume_count(randint(*bleed_decay))

        if debug_effects:
            for status_name in enemy.statuses:
                effect : backend.StatusEffect = enemy.statuses[status_name]
                if not effect.is_active(): continue
                print(f'{status_name} : ({effect.potency}, {effect.count})', end=', ')
            print(f'(Turn {i + 1})')


        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if (a == 3) and (b == 2) and (enemy.get_status_count() >= 3):
            decision = b

        if passive_active:
            enemy.apply_status(['Burn', 'Bleed', 'Tremor', 'Rupture', 'Sinking'][randint(0, 4)], 2, 0)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        if len(bag) < 2:
            bag += get_bag()
        enemy.on_turn_end()
    if debug or debug_effects: print("-".join(sequence))
    return total

def dawn_clair_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_active : bool = True, start_burn : tuple[int, int] = (0,0), max_AOE : int = 1,
                        start_sp : int = 45, start_ego : int = 0, wrath_res : int = 0, avg_clash_count : int = 2, support_passives : tuple[str] = ()):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3, 4 : unit.extra_skills[0]}
    total = 0

    unit.wrath_res = wrath_res
    unit.is_ares = True if wrath_res >= 4 else False
    unit.ego = start_ego
    unit.sp = start_sp
    enemy.apply_status("Burn", 0,0)
    the_burn : backend.StatusEffect = enemy.statuses.get('Burn')
    the_burn.potency, the_burn.count = start_burn
    
    if passive_active:
        unit.apply_unique_effect('passive1', backend.skc.DawnClairCoinPower(), True)
        unit.apply_unique_effect('passive2', backend.skc.ApplyAdditionalStatus('Burn', 1, 1), True)
    for i in range(6):
        #---Turn Start---
        if not unit.ego:
            if unit.sp >= 40:
                unit.ego = 1
                unit.sp -= 20
        else:
            if unit.sp <= 0:
                unit.ego = 0
                
        #---Chaining Phase---
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3 and unit.ego: decision = 4
        #---Combat Start---   
        if 'NFaust' in support_passives: 
            unit.sp += 10 #Whisltes

        if "LCB Hong Lu" in support_passives: 
            unit.sp += 6 #LCB Hong Lu support passive

        unit.clamp_sp()

        #---On Use---
        if unit.ego and decision == 2:
            unit.sp -= 5 #Skill 2 SP loss

        #---Clash Win---
        unit.sp += 15 + (avg_clash_count - 1) * 3 if avg_clash_count else 0 #Clash Win Base SP Gain
        if decision == 3 or decision == 4:
            unit.sp += 10 if avg_clash_count else 0 #Skill 3/4 Clash win SP Gain
        unit.clamp_sp()

        #---Attack Phase---
        unit.atk_weight = 1
        unit.skill_1.set_conds([bool(unit.ego)])
        unit.skill_2.set_conds([bool(unit.ego)])
        enemy.all_burn = the_burn.potency * max_AOE
        if unit.ego:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.AddXForEachY(1, 'base', 1, 'enemy.statuses.Burn.potency')])
        else:
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        actual_aoe : int = min(unit.atk_weight, max_AOE)
        total += (result * actual_aoe)
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision) if decision != 4 else bag.remove(3)

        #---After Attack---
        if unit.ego and decision == 2:
            unit.sp -= 5 #Skill 2 SP loss

        if decision == 4:
            unit.sp -= 15 #Skill 4 SP loss

        #---Turn end---
        if 'LCB Sang' in support_passives: #LCB Yi Sang Sp Gain
            if unit.ego:
                if decision == 2 or decision == 4 or decision == 3:
                    unit.sp += 10
                    unit.clamp_sp()
        
        if unit.ego: #Ego Sp Loss
            sp_loss : int = backend.clamp(unit.ego * 5, 0, 40)
            unit.sp -= sp_loss
            unit.ego += 1

        #Bag refresh
        if len(bag) < 2:
            bag += get_bag()
        
        unit.clamp_sp()

    if debug: print("-".join(sequence))
    return total

def mb_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_burn : tuple[int, int] = (0,0), start_bullet : int = 1, 
                      max_AOE : int = 1, start_flame : int = 0, passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.bullet = backend.clamp(start_bullet, 0, 7)

    enemy.clear_effects()
    enemy.apply_status("Burn", *start_burn)
    enemy.apply_status(backend.StatusNames.dark_flame,0, start_flame)
    if passive_active: unit.apply_unique_effect('passive', backend.skc.MBOutisPassive(), True)

    for i in range(6):
        enemy.on_turn_start()
        unit.atk_weight = 1
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if i < 5 and decision == 3 and unit.bullet < 7: 
            decision = b
       
        unit.sp += 12
        unit.clamp_sp()
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        actual_AOE : int = min(max_AOE, unit.atk_weight)
        total += result * actual_AOE
        
        if debug: print(f'{result} * {actual_AOE}')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total


def kk_ryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_bleed : tuple[int, int] = (0,0), bleed_drain : int = 0, passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    enemy.apply_status('Bleed', start_bleed[0], start_bleed[1])
    the_bleed : backend.StatusEffect = enemy.statuses['Bleed']
    the_bleed.potency, the_bleed.count = start_bleed
    passive : backend.SkillEffect = backend.skc.DAddXForEachY(0.1, 'dynamic', 1, 'enemy.statuses.Bleed.potency', 0, 0.1)
    for i in range(6):

        
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[passive] if random() < passive_frequency else None)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        the_bleed.consume_count(bleed_drain)
    
    if debug: print("-".join(sequence))
    return total

def bl_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), bl_meur : int = 0, least_poise : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)

    if bl_meur:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland(), True)
    unit.skill_2.set_conds([least_poise])
    unit.skill_3.set_conds([least_poise])

    for i in range(6):
        if bl_meur: unit.add_poise(bl_meur, bl_meur)

        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def molar_ish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_tremor : int = 0, start_sinking : tuple[int, int] = (0,0), passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.clear_effects()
    unit.clear_effects()
    unit.tremor = start_tremor
    enemy.apply_status("Sinking", *start_sinking)
    if passive_active: unit.apply_unique_effect('passive', backend.skc.MolarIshPassive(), True)
    for i in range(6):
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3 and unit.tremor < 10: decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()

        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def l_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_rupture : tuple[int, int] = (0,0), does_reuse : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status(backend.StatusNames.rupture, 0,0)
    rupture_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.rupture)
    rupture_status.potency, rupture_status.count = start_rupture
    unit.skill_3.set_conds([does_reuse])
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def butler_ish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), 
                        passive_active : bool = True, faster : bool = True, s2_clash_win : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    enemy.clear_effects()
    unit.skill_1.set_conds([faster])
    unit.skill_2.set_conds([faster, passive_active, s2_clash_win])
    unit.skill_3.set_conds([faster, passive_active])
    for i in range(6):
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def shi_heath_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), 
                       max_AOE : int = 1, below_50 : bool = False, passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    for skill in unit.skills:
        skill.set_conds([below_50])

    for i in range(6):
        unit.atk_weight = 1
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.DynamicBonus(0.1)] if passive_frequency > random() else None)
        actual_aoe = min(max_AOE, unit.atk_weight)
        total += result * actual_aoe
        
        if debug: print(f'{result} * {actual_aoe}')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def hook_lu_rotation(unit : Unit, enemy : Enemy, debug : bool = False, speed_range : tuple[int, int] = (3,7), missing_hp : float = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    enemy.missing_hp = missing_hp
    unit.apply_status("Haste", 0, 0)
    unit.statuses['Haste'].count = 0
    for i in range(6):
        unit.on_turn_start()
        unit.speed = randint(*speed_range) + unit.statuses['Haste'].count
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3 and unit.speed < 6 and b == 2 and i <= 4: decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def shi_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), s3_conds : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    unit.skill_3.set_conds([s3_conds])
    prev_decision : int = 0
    for i in range(6):
        if prev_decision == 1:
            unit.add_poise(3, 0)
        elif prev_decision == 2:
            unit.add_poise(2, 0)
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        prev_decision = decision
    
    if debug: print("-".join(sequence))
    return total

def lccb_ryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)

    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        if passive_active:
            if unit.sp >= 45: unit.add_poise(1, 1)
            else: unit.sp += 8; unit.clamp_sp()
    
    if debug: print("-".join(sequence))
    return total

def molar_clair_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_tremor : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = start_tremor
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()

        if unit.tremor > 0: unit.tremor = 0
    
    if debug: print("-".join(sequence))
    return total

def lccb_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, blunt_odds : float = -1, passive_freq : float = -1, unhit : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.skill_3.set_conds([unhit])
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        b : bool = True if blunt_odds >= random() else False
        unit.skill_1.set_conds([b])
        unit.skill_2.set_conds([b])
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects= [backend.skc.DynamicBonus(0.1)] if passive_freq >= random() else None)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def molar_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, unit_tremor : int = 0, enemy_tremor : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = unit_tremor
    enemy.tremor = enemy_tremor

    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if a == 2:
            if b == 1:
                unit.tremor += 4
                bag.remove(b)
            else:
                pass
        elif a == 3:
            if b != 3:
                unit.tremor += 4
                bag.remove(b)
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def cap_ish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), pride_res : int = 0, 
                     bleed : int = 0, passive_active : bool = False, missing_hp : float = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    if passive_active: unit.apply_unique_effect('passive', backend.skc.DynamicBonus(0.1), True)
    enemy.bleed = bleed
    enemy.missing_hp = missing_hp
    unit.set_poise(*start_poise)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)
        if decision == 2 and pride_res >= randint(1, 5):
            total += 20 if pride_res < 4 else 26

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
    
    if debug: print("-".join(sequence))
    return total

def liu_gregor_passive(unit : Unit, enemy : Enemy, debug : bool = False, start_burn : tuple[int, int] = (0,0), passive_active : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    enemy.apply_status('Burn', 0, 0)
    burn_status : backend.StatusEffect = enemy.statuses.Burn
    burn_status.potency, burn_status.count = start_burn
    if burn_status.potency <= 0 or burn_status.count <= 0:
        burn_status.potency = 0
        burn_status.count = 0
    
    if passive_active: unit.apply_unique_effect('passive', backend.skc.LiuGregorPassive(), True)
    next_atk_powerup : int = 0
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=[backend.skc.BasePowerUp(next_atk_powerup)])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        next_atk_powerup = 0
        if decision == 2 and burn_status.potency >= 6:
            next_atk_powerup = 1
        

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total


def butler_faust_rotation(unit : Unit, enemy : Enemy, debug : bool = False, sinking_start : tuple[int, int] = (0,0), echoes_start : int = 0, 
                          passive_active : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    enemy.clear_effects()

    enemy.apply_status('Sinking', *sinking_start)
    enemy.apply_status(backend.StatusNames.echoes_of_the_manor, 0, echoes_start)
    if debug: print(enemy.statuses[backend.StatusNames.echoes_of_the_manor].count)

    if passive_active: unit.apply_unique_effect('passive', backend.skc.ButlerFaustPassive(), True)
    for skill in unit.skills:
        skill.set_conds([passive_active])

    for i in range(6):    
        unit.on_turn_start()
        enemy.on_turn_start()
        
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        unit.clear_effects()
        if debug:
            print(f'Current sinking : {enemy.statuses.Sinking.potency}, {enemy.statuses.Sinking.count}; Current echoes : {enemy.statuses[backend.StatusNames.echoes_of_the_manor].count}')

        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        if len(bag) < 2:
            bag += get_bag()
        
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total


def rose_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, enemy_tremor_count : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.tremor_count = enemy_tremor_count
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if enemy.tremor_count > 0: enemy.tremor_count -= 1
        else: enemy.tremor_count = 0
    
    if debug: print("-".join(sequence))
    return total

def red_ryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_eyes : int = 0, start_skull : int = 0, passive_active : bool = False, 
                     start_bleed : tuple[int, int] = (0,0), bleed_decay : int = 0, speed_diff : int = 0, enemy_sp : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3, 4 : unit.extra_skills[0]}
    total = 0

    unit.red_eyes = start_eyes
    unit.penitence = start_skull
    unit.passive = passive_active
    
    unit.speed = speed_diff
    enemy.sp = enemy_sp

    unit.apply_unique_effect('base_passive1', backend.skc.RedRyoBaseSpHeal(), True)
    unit.apply_unique_effect('base_passive2', backend.skc.RedRyoBonusBleed(), True)
    unit.ashes = 0

    enemy.apply_status('Bleed', 0, 0)
    the_bleed : backend.StatusEffect = enemy.statuses['Bleed']
    the_bleed.potency, the_bleed.count = start_bleed    

    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3 and unit.red_eyes >= 15 and unit.penitence >= 15:
            decision = 4
        elif decision == 3:
            decision = b
       
        unit.sp += 12
        unit.clamp_sp()
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result} (After attack : {unit.red_eyes} eyes, {unit.penitence} skulls)\n')
        sequence[i] = str(decision)
        bag.remove(decision if decision != 4 else 3)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.ashes > 0: unit.ashes -= 1
        the_bleed.consume_count(bleed_decay)

    
    if debug: print("-".join(sequence))
    return total

def yuro_ryo_rotation(unit : Unit, enemy : Enemy, debug : bool = False, unit_tremor : int = 0, enemy_tremor : tuple[int, int] = (0,0)):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = unit_tremor
    enemy.tremor = enemy_tremor[0]
    enemy.tremor_count = enemy_tremor[1]
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if unit.tremor < 6 and decision == 3:
            decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if enemy.tremor_count > 0: enemy.tremor_count -= 1
        if unit.tremor > 0 : unit.tremor -= 1
    
    if debug: print("-".join(sequence))
    return total

def rose_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_charge : int = 0, enemy_tremor_count : int = 0, passive_active : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0

    unit.charge = start_charge
    unit.atk_weight = 0
    enemy.tremor_count = enemy_tremor_count
    effects : list[backend.SkillEffect] = []
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 2 and unit.charge < 3:
            decision = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=effects)
        total += result
        effects.clear()
        
        if debug: print(f'{result} (After attack : {unit.charge} charge)')
        sequence[i] = str(decision)
        bag.remove(decision)

        bursts : int = unit.atk_weight
        if (bursts > 0) and passive_active:
            effects.append(backend.skc.TypedDamageUp('Blunt', bursts))
            unit.charge -= 3 * bursts
            if unit.charge < 0: unit.charge = 0

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.charge > 0: unit.charge -= 1

    
    if debug: print("-".join(sequence))
    return total

def bl_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), passive_active : bool = True, 
                      missing_hp : float = 0, bl_meur : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    if missing_hp >= 0.5:
        unit.skill_3.set_conds([True])
    unit.skill_2.set_conds([True])

    if (passive_active or bl_meur):
        unit.apply_unique_effect('passive', backend.skc.DynamicBonus(0.2 if missing_hp >= 0.75 else 0), True)
    if bl_meur:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland(), True)
    for i in range(6):
        if bl_meur: unit.add_poise(bl_meur, bl_meur)
        unit.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def devyat_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_trunk : int = 0, enemy_rupture : tuple[int, int] = (0,0), 
                          start_sp : int = 45, clash_count : int = 2):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.trunk = start_trunk
    enemy.apply_status('Rupture', 0, 0)
    unit.sp = start_sp
    the_rupture : backend.StatusEffect = enemy.statuses.get("Rupture")
    the_rupture.potency, the_rupture.count = enemy_rupture
    for i in range(6):
        unit.trunk += 3
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if debug: print(f'Before attack: {unit.trunk} trunk and {the_rupture.potency}x{the_rupture.count} rupture')
        if unit.trunk >= 30: unit.sp -= unit.trunk // 3
        unit.sp += 10 + (clash_count - 1) * 2 if clash_count else 0
        unit.clamp_sp()
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=None if unit.trunk < 20 else [backend.skc.DynamicBonus(0.1)])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        if unit.trunk >= 30: unit.sp -= unit.trunk // 2
        unit.clamp_sp()
    
    if debug: print("-".join(sequence))
    return total

def deici_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, enemy_sinking : tuple[int, int] = (0,0), start_insight : int = 1, 
                        start_erudition : int = 0, discarding_allies : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.insight = start_insight
    unit.erudition = start_erudition
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = enemy_sinking
    effects : list[backend.SkillEffect|None] = None if not discarding_allies else [backend.skc.DynamicBonus(backend.clamp(discarding_allies * 0.1, 0, 0.3))]
    unit.skill_1.set_conds([True])
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        unit.erudition = backend.clamp(unit.erudition + backend.clamp(discarding_allies, 0, 3), 0, 6)
        
        if a == 3:
            if b == 3: 
                pass
            elif b == 2:
                pass
            elif b == 1:
                pass
        elif a == 2:
            if b == 2:
                unit.erudition = backend.clamp(unit.erudition + unit.insight, 0, 6)
            elif b == 1:
                unit.erudition = backend.clamp(unit.erudition + unit.insight, 0, 6)
                bag.remove(b)
                unit.insight = b
        else:
            bag.remove(b)
            unit.insight = b
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=effects)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def mariachi_rotation(unit : Unit, enemy : Enemy, debug : bool = False, poise : tuple[int, int] = (0,0), sinking : tuple[int, int] = (0,0), enemy_sp : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*poise)
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = sinking
    enemy.sp = enemy_sp
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def heir_gregor_rotation(unit : Unit, enemy : Enemy, debug : bool = False, enemy_sinking : tuple[int, int] = (0,0), passive_frequency : float = 0,
                         sp_variation : int = 0, start_sp : int = 45):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = enemy_sinking
    unit.sp = start_sp
    prev_sp : int = start_sp
    passive1 : backend.StatusEffect = backend.skc.DAddXForEachY(0.02, 'dynamic', 1, 'enemy.statuses.Sinking.potency', 0, 0.4)
    for i in range(6):
        if i % 2 == 0:
            unit.sp -= sp_variation
        else:
            unit.sp += sp_variation
        unit.clamp_sp()
        unit.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        sp_difference_chunks : int = backend.clamp(abs(unit.sp - prev_sp) // 5, 0, 5)
        passive2 : backend.StatusEffect = backend.skc.DamageUp(sp_difference_chunks)
        prev_sp = unit.sp
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=None if random() > passive_frequency else [passive1, passive2])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def zwei_ish_rotation(unit : Unit, enemy : Enemy, debug : bool = False, tremor : int = 0, dl_up : int = 0, start_stance : int = 0, passive_active : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = tremor
    unit.apply_status(backend.StatusNames.defense_level_up, 0, 0)
    the_dl_up : backend.StatusEffect = unit.statuses[backend.StatusNames.defense_level_up]
    the_dl_up.count = dl_up
    unit.defense_stance = start_stance
    unit.skill_2.set_conds([True])
    unit.skill_3.set_conds([True])
    for i in range(6):
        unit.on_turn_start()
        if unit.defense_stance:
            the_dl_up.count += 5
        if passive_active:
            bonus_dl : int = backend.clamp(unit.tremor, 0, 5)
            the_dl_up.count += bonus_dl
            if unit.defense_stance:
                the_dl_up.count += bonus_dl
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if i < 5:
            if (bag[1] == 3) and unit.defense_stance <= 0:
                decision = 'Guard'
            elif len(bag) >= 3:
                if bag[2] == 3 and unit.defense_stance <= 0:
                    decision = 'Guard'
       
        if decision != 'Guard':
            result = skills[decision].calculate_damage(unit, enemy, debug=debug)
            total += result
        else:
            unit.tremor += 10
            unit.defense_stance = 2
            result = 'Guard'
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision) if decision != 'Guard' else bag.pop(0)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if unit.tremor > 0: unit.tremor -= 1
        if unit.defense_stance > 0: unit.defense_stance -= 1
        unit.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def deici_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_sinking : tuple[int, int] = (0,0), below_50 : bool = False, is_perfect : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag() if not is_perfect else [3, 1, 2, 1, 2, 1]

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.skill_3.set_conds([below_50])
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = start_sinking
    unit.insight = 1
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        if a == 3: pass
        elif a == 2:
            if b == 1: 
                bag.remove(b)
                unit.insight = b
        else:
            bag.remove(b)
            unit.insight = b
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag() if not is_perfect else [3, 1, 2, 1, 2, 1]
    
    if debug: print("-".join(sequence))
    return total

def bush_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_tremor : int = 0,  start_sinking : tuple[int, int] = (0,0), 
                       ignore_deluge : bool = True, passive_active : bool = False, part_count : int = 1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = start_tremor
    unit.passive = passive_active
    unit.max_aoe = part_count
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = start_sinking
    for i in range(6):
        enemy.on_turn_start()
        unit.atk_weight = 1
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if debug: print(f'Before Attack : {the_sinking.potency}x{the_sinking.count} Sinking, {unit.tremor} self-tremor')
        result : int = skills[decision].calculate_damage(unit, enemy, debug=debug, ignore_fixed_damage=ignore_deluge)
        total += result * min(part_count, unit.atk_weight)   
        if debug: print(result, '*', f'min({unit.max_aoe=}, {unit.atk_weight=})')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if unit.tremor > 0: unit.tremor -= 1
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def n_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, passive_frequency : float = -1, below_50 : bool = False, start_nails : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.skill_1.set_conds([below_50])
    enemy.apply_status("Nails", 0, 0)
    enemy.statuses["Nails"].count = start_nails
    do_passive : bool = False
    unit.clear_statuses()
    for i in range(6):
        unit.on_turn_start()
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        do_passive = passive_frequency >= random()
        if do_passive: unit.apply_status("Fanatic", 0, 1)
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=None if not do_passive else [backend.skc.BasePowerUp(1)])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        unit.on_turn_end()
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total


def n_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_nails : int = 0, ncorp_allies : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status("Nails", 0, 0)
    enemy.statuses["Nails"].count = start_nails
    unit.clear_statuses()
    unit.apply_status("Fanatic", 0, 0)
    unit.ncorp_allies = ncorp_allies
    for i in range(6):
        unit.on_turn_start()
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        unit.on_turn_end()
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total


def bl_sinclair_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_poise : tuple[int, int] = (0,0), passive_poise : int = 0, bl_meur : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    if bl_meur:
        unit.apply_unique_effect('homeland', backend.skc.SwordplayOfTheHomeland(), True)
    unit.skill_2.set_conds([True])
    for i in range(6):
        if bl_meur: unit.add_poise(bl_meur, bl_meur)
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        if passive_poise: 
            unit.add_poise(0, passive_poise)
        unit.skill_3.set_conds([bool(passive_poise)])
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(f'{result}(poise = ({unit.poise_potency}, {unit.poise_count}))')
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise()
    
    if debug: print("-".join(sequence))
    return total

def mid_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, mark : bool = False, passive_active : bool = False, res4 : bool = False, res6 : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.vengeance_mark = mark
    if passive_active: unit.apply_unique_effect('passive', backend.skc.MidMeurPassive(), True)
    unit.skill_3.set_conds([res4, res6])
    for i in range(6):
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        enemy.on_turn_end()
    
    if debug: print("-".join(sequence))
    return total

def seven_outis_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_rupture : tuple[int, int] = (0,0), passive_frequency : float = -1):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    enemy.apply_status(backend.StatusNames.rupture, 0,0)
    rupture_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.rupture)
    rupture_status.potency, rupture_status.count = start_rupture
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=None if passive_frequency < random() else [backend.skc.SevenOutisPassive()])
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
    
    if debug: print("-".join(sequence))
    return total

def oufi_heathcliff_rotation(unit : Unit, enemy : Enemy, debug : bool = False, start_tremor : tuple[int, int] = (0,0), passive_active : bool = False, decay : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    if passive_active: unit.apply_unique_effect('passive', backend.skc.OufiHeathcliffPassive(), True)
    enemy.apply_status(backend.StatusNames.tremor, 0,0)
    tremor_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.tremor)
    tremor_status.potency, tremor_status.count = start_tremor
    enemy.tremor_decay = decay
    for i in range(6):
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        
        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def zwei_sinclair_west_rotation(unit : Unit, enemy : Enemy, debug : bool = False, tremor : int = 0, dl_up : int = 0, passive_active : bool = False):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.tremor = tremor
    unit.apply_status(backend.StatusNames.defense_level_up, 0, 0)
    the_dl_up : backend.StatusEffect = unit.statuses[backend.StatusNames.defense_level_up]
    the_dl_up.count = dl_up
    unit.skill_2.set_conds([True])
    unit.skill_1.set_conds([True])
    for i in range(6):
        unit.on_turn_start()
        if passive_active:
            bonus_dl : int = backend.clamp(unit.tremor, 0, 5)
            the_dl_up.count += bonus_dl
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        result = skills[decision].calculate_damage(unit, enemy, debug=debug)
        total += result

        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if unit.tremor > 0: unit.tremor -= 1
        unit.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def cinq_meur_rotation(unit : Unit, enemy : Enemy, debug : bool = False, 
            start_poise : tuple[int, int] = (0,0), 
            start_rupture : tuple[int, int] = (0,0),
            unit_speed : tuple[int, int] = (4, 7), enemy_speed : tuple[int, int] = (2, 4), 
            passive : bool = False, focusing : bool = True, start_focus : int = 0,):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.set_poise(*start_poise)
    enemy.apply_status(backend.StatusNames.rupture, 0,0)
    rupture_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.rupture)
    rupture_status.potency, rupture_status.count = start_rupture
    enemy.meur_focus = start_focus
    haste : int = 0
    for i in range(6):
        unit.on_turn_start()
        unit.speed = randint(*unit_speed) + haste
        enemy.speed = randint(*enemy_speed)
        unit.rel_speed = unit.speed - enemy.speed
        haste = 0
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
       
        entry_effects : list[backend.SkillEffect]
        if enemy.meur_focus <= 1:
            entry_effects = [] 
        elif enemy.meur_focus < 3:
            entry_effects = [backend.skc.BasePowerUp(1)]
        else:
            entry_effects = [backend.skc.BasePowerUp(1), backend.skc.CoinPower(1)]
        
        print(f'Before attack : {rupture_status.potency}x{rupture_status.count} rupture, {enemy.meur_focus} focused attack')
        result = skills[decision].calculate_damage(unit, enemy, debug=debug, entry_effects=entry_effects)
        total += result
        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        
        unit.consume_poise(1)
        unit.on_turn_end()
        if not focusing : enemy.meur_focus = 0
        if passive:
            haste += backend.clamp(unit.poise_potency // 3, 0, 2)
            if enemy.meur_focus < 3: enemy.meur_focus += 1
        else:
            enemy.meur_focus = 0
    
    if debug: print("-".join(sequence))
    return total


def t_rodya_rotation(unit : Unit, enemy : Enemy, debug : bool = False, tremor : int = 0, enemy_tremor : int = 0, start_mora : int = 0, start_bind : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total : int = 0
    unit.tremor = tremor
    enemy.tremor = enemy_tremor
    enemy.moratium = start_mora
    enemy.apply_status(backend.StatusNames.bind, 0,0)
    bind_status : backend.StatusEffect = enemy.statuses.get(backend.StatusNames.bind)
    bind_status.count = start_bind
    has_mora : bool = bool(start_mora)
    for i in range(6):
        enemy.on_turn_start()
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        result : int = skills[decision].calculate_damage(unit, enemy, debug=debug)

        if has_mora:
            total += floor(result * 1.3 * enemy.sin_res['Sloth'])
        else:
            total += result
        if enemy.moratium > 0: enemy.moratium -= 1
        has_mora = bool(enemy.moratium)

        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if unit.tremor > 0: unit.tremor -= 1
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def t_don_rotation(unit : Unit, enemy : Enemy, debug : bool = False, tremor : int = 0, enemy_tremor : int = 0, start_mora : int = 0):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total : int = 0
    unit.tremor = tremor
    enemy.tremor = enemy_tremor
    enemy.moratium = start_mora
    has_mora : bool = bool(start_mora)
    for i in range(6):
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a

        result : int = skills[decision].calculate_damage(unit, enemy, debug=debug)

        if has_mora:
            total += floor(result * 1.3 * enemy.sin_res['Sloth'])
        else:
            total += result
        if enemy.moratium > 0: enemy.moratium -= 1
        has_mora = bool(enemy.moratium)

        
        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision)

        
        
        if len(bag) < 2:
            bag += get_bag()
        if unit.tremor > 0: unit.tremor -= 1
    if debug: print("-".join(sequence))
    return total

def butterfly_sang_rotation(unit : Unit, enemy : Enemy, debug : bool = False, 
                            start_sinking : tuple[int, int] = (0,0), start_butterfly : tuple[int, int] = (0,0), start_ammo : tuple[int, int] = (10,10),
                            clash_count : int = 2, highest_res : int = 0, isares : bool = False, exclude_butterfly_damage : bool = True):
    sequence = [None for _ in range(6)]
    bag = get_bag()

    skills = {1 : unit.skill_1, 2 : unit.skill_2, 3 : unit.skill_3}
    total = 0
    unit.the_living, unit.the_departed = start_ammo
    for skill in unit.skills:
        skill.set_conds([True])
    enemy.apply_status('Sinking', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Sinking']
    the_sinking.potency, the_sinking.count = start_sinking

    enemy.apply_status('Butterfly', 0, 0)
    the_sinking : backend.StatusEffect = enemy.statuses['Butterfly']
    the_sinking.potency, the_sinking.count = start_butterfly
    for i in range(6):
        enemy.on_turn_start()
        unit.attack_cancel = False
        dashboard = [bag[0], bag[1]]
        a = max(dashboard)
        b = min(dashboard)
        decision = a
        if decision == 3:
            if unit.the_living + unit.the_departed < 7:
                decision = b if (b == 2) or (unit.the_living + unit.the_departed <= 2) else 'Guard' if bag[0] != 3 else b
        if decision != 'Guard':
            unit.sp += 10 + (clash_count - 1) * 2 if clash_count else 0
        unit.clamp_sp()
        if debug: print(f"Before {'attack' if decision != 'Guard' else 'guard'} : {unit.sp} sp, ({unit.the_living}x{unit.the_departed}) the living and the departed")
        if decision != 'Guard':
            result = skills[decision].calculate_damage(unit, enemy, debug=debug, ignore_fixed_damage= exclude_butterfly_damage)
            total += result
        else:
            gunsang_reload(unit)
            if debug: print(f"Reloading")
            result = 'Guard'
        
        if not unit.attack_cancel and decision == 2:
            if not isares:
                gunsang_random_ammo(unit, backend.clamp(highest_res, 0, 6))
            elif isares:
                if highest_res >= 4:
                    gunsang_reload(unit)
                    if debug: print(f"Reloading")
                else:
                    gunsang_random_ammo(unit, backend.clamp(highest_res * 2, 0, 12))
        if unit.the_living + unit.the_departed <= 0:
            gunsang_reload(unit)
            if debug: print(f"Reloading")

        if debug: print(result)
        sequence[i] = str(decision)
        bag.remove(decision) if decision != 'Guard' else bag.pop(0)

        
        
        if len(bag) < 2:
            bag += get_bag()
        enemy.on_turn_end()
    if debug: print("-".join(sequence))
    return total

def gunsang_random_ammo(unit : Unit, count : int):
    departing_weight : float
    if unit.sp >= 0:
        departing_weight = 0.7
    else:
        departing_weight = 0.3
    for _ in range(count):
        if unit.the_living + unit.the_departed >= 20: break
        if random() <= departing_weight:
            unit.the_departed += 1
        else:
            unit.the_living += 1
    if unit.the_departed <= 0:
        unit.the_departed = 1
        unit.the_living -= 1
    elif unit.the_living <= 0:
        unit.the_living = 1
        unit.the_departed -= 1

def gunsang_reload(unit : Unit):
    unit.sp -= (30 - (unit.the_living + unit.the_departed)) // 2
    unit.clamp_sp()
    departing_weight : float
    if unit.sp >= 0:
        departing_weight = 0.7
    else:
        departing_weight = 0.3
    unit.the_living = 0
    unit.the_departed = 0
    for _ in range(20):
        if random() <= departing_weight:
            unit.the_departed += 1
        else:
            unit.the_living += 1
    if unit.the_departed <= 0:
        unit.the_departed = 1
        unit.the_living -= 1
    elif unit.the_living <= 0:
        unit.the_living = 1
        unit.the_departed -= 1