from math import floor, ceil
from random import random, randint
from typing import Any, Callable, Optional, Union, TypedDict


def bind_method(method : Callable, obj : object):
    bound_method = method.__get__(obj)
    obj.__setattr__(method.__name__, bound_method)

def clamp(x : float|int, a : float|int, b : float|int) -> float|int :
    if x > b: x = b
    if x < a: x = a
    return x

def get_chained_attribute(obj : object, name : str) -> Any:
        steps = name.split('.')
        step_count = len(steps)
        if step_count != 1:
            current = obj
            for index, step in enumerate(steps):
                current = getattr(current, step)
                if index + 2 >= step_count: break
            final_target = current
            reach = steps[-1]
        else:
            final_target = obj
            reach = name
    
        return getattr(final_target, reach)

def set_chained_attribute(obj : object, name : str, value : Any):
        steps = name.split('.')
        step_count = len(steps)
        if step_count != 1:
            current = obj
            for index, step in enumerate(steps):
                current = current.__getattribute__(step)
                if index + 2 >= step_count: break
            final_target = current
            reach = steps[-1]
        else:
            final_target = obj
            reach = name
        final_target.__setattr__(reach, value)

class StatusDict(dict):
    def __getattr__(self, name: str) -> Any:
        return self[name]

class AttrStrDict(dict):
    def __getattr__(self, name: str) -> Any:
        return self[name]
    
    def __setattr__(self, name: str, val: Any) -> Any:
        self[name] = val

class SinResDict(TypedDict):
    Wrath : float
    Lust : float
    Sloth : float
    Gluttony : float
    Gloom : float
    Pride : float
    Envy : float

class PhysResDict(TypedDict):
    Slash : float
    Pierce : float
    Blunt : float

class ResDict(TypedDict):
    sin : SinResDict
    phys : PhysResDict

["Wrath", "Lust", "Sloth", "Gluttony", "Gloom", "Pride", "Envy"]
class Enemy:

    @classmethod
    def get_enemy(cls, name):
        if name in ENEMIES:
            return ENEMIES[name]
        else:
            print("enemy was not found")
            return None

    def __init__(self, def_level, hp, phys_res : dict, sin_res : dict, observation : int = 0, can_break : bool = False,
                 stagger_tresholds : list[int]|None = None) -> None:
        if stagger_tresholds is None: stagger_tresholds = []
        stagger_tresholds = sorted(stagger_tresholds, reverse=True)
        self.def_level = def_level
        self.hp = hp
        self.max_hp = hp
        self.observation_level = observation
        self.can_break = can_break
        self.part_broken : bool = False
        self.is_staggered : bool = False
        self.stagger_level : int = 0
        self.statuses : dict[str, StatusEffect] = StatusDict()
        self.next_turn_statuses : dict[str, list[int]] = {}
        
        for val in ["Slash", "Pierce", "Blunt"]:
            if not val in phys_res:
                phys_res[val] = 1
        
        
        self.phys_res : PhysResDict = phys_res
        for val in ["Wrath", "Lust", "Sloth", "Gluttony", "Gloom", "Pride", "Envy"]:
            if not val in sin_res:
                sin_res[val] = 1
            
        
        self.sin_res : SinResDict = sin_res
        self.og_res : ResDict = {"sin" : self.sin_res.copy(), "phys" : self.phys_res.copy()}

        self.og_tresholds = stagger_tresholds.copy()
        self.stagger_tresholds = stagger_tresholds
    
    def clear_effects(self):
        self.statuses.clear()
    
    def get_status_count(self) -> int:
        status_effect_count : int = 0
        for status_effect_name in self.statuses:
            real_status : StatusEffect = self.statuses[status_effect_name]
            if real_status.is_active():
                status_effect_count += 1
        return status_effect_count
    
    @property
    def status_count(self) -> int:
        return self.get_status_count()
    
    def has_status(self, status_name : str):
        status : StatusEffect|None = self.statuses.get(status_name, None)
        if status is None: return False
        if not status.is_active(): return False
        return True

    def has_tremor_flavor(self, flavor_name : str):
        if getattr(self, 'tremor_flavor', None) is None: return False
        if self.tremor_flavor == flavor_name: return True
        elif type(self.tremor_flavor) == list:
            if flavor_name in self.tremor_flavor: return True
        return False
    
    def process_tremor_flavors(self):
        if getattr(self, 'tremor_flavor', None) is None: return
        elif type(self.tremor_flavor) == list:
            self.tremor_flavor = None 

    def hit(self, damage, env : 'Environment'):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            if self.can_break: 
                self.break_part()
        self.update_stagger_level()
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_hit(effect, env)
    
    def raise_stagger_treshold(self, damage : int, env : 'Environment' = None):
        if not self.stagger_tresholds: return
        self.stagger_tresholds[0] += damage
        self.update_stagger_level()
    
    def take_damage(self, damage : int, env : 'Environment'):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            if self.can_break: 
                self.break_part()
        self.update_stagger_level()
    
    def on_skill_start(self, env : 'Environment', is_defending : bool = True):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_skill_start(effect, env, is_defending=is_defending)

    def on_skill_end(self, env : 'Environment', is_defending : bool = True):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_skill_end(effect, env, is_defending=is_defending)
    
    def on_turn_start(self):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_turn_start(effect)

    def on_turn_end(self):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_turn_end(effect)
        for effect_name in self.next_turn_statuses:
            self.apply_status(effect_name, self.next_turn_statuses[effect_name][0], self.next_turn_statuses[effect_name][1])
        self.next_turn_statuses.clear()
        self.process_tremor_flavors()
            
    def update_stagger_level(self):
        if not self.stagger_tresholds: return
        self.stagger_tresholds.sort()
        biggest_hp_treshold = self.stagger_tresholds[0]
        if self.hp <= biggest_hp_treshold:
            self.stagger()
            self.stagger_tresholds.pop()
            while len(self.stagger_tresholds) > 0:
                next_treshold = self.stagger_tresholds[0]
                if self.hp < next_treshold:
                    self.stagger()
                    self.stagger_tresholds.pop()
    
    def reset_tresholds(self):
        self.stagger_tresholds = self.og_tresholds.copy()

    def apply_status(self, status_type : str, potency : int, count : int, env : Union['Environment', None] = None):
        if not status_type in self.statuses:
            status : StatusEffect = StatusEffect.new(status_type, (potency, count), self)
            self.statuses[status_type] = status
            status.when_first_applied(status, env, True)
        else:
            status : StatusEffect = self.statuses[status_type]
            status.add(potency, count)
            status.when_added(status, (potency, count), env, True)
    
    def apply_status_next_turn(self, status_type : str, potency : int, count : int):
        if status_type in self.next_turn_statuses:
            self.next_turn_statuses[status_type][0] += potency
            self.next_turn_statuses[status_type][1] += count
        else:
            self.next_turn_statuses[status_type] = [potency, count]
    
    def break_part(self):
        if not self.can_break: return
        self.part_broken = True
        if self.stagger_level <= 1:
            self.phys_res = {"Slash" : 2, "Blunt" :2, "Pierce" : 2}
    
    def unbreak_part(self):
        self.part_broken = False
        if self.is_staggered == False:
            self.phys_res = self.og_tresholds.copy()

    def stagger(self):
        self.stagger_level += 1
        if self.stagger_level == 1:
            res = 2
        elif self.stagger_level == 2:
            res = 2.5
        elif self.stagger_level >= 3:
            res = 3
        else:
            self.stagger_level = 1
            res = 2
        self.phys_res = {"Slash" : res, "Blunt" :res, "Pierce" : res}
        self.is_staggered = True
        
    
    def unstagger(self):
        if self.part_broken:
            self.phys_res = {"Slash" : 2, "Blunt" :2, "Pierce" : 2}
        else:
            self.phys_res = self.og_res["phys"].copy()
        self.stagger_level = 0
        self.is_staggered = False


class Skill:

    @classmethod
    def get_skill(cls, name):
        if name in SKILLS:
            return SKILLS[name]
        else:
            print("skill was not found")
            return None

    def __init__(self, basic_data : tuple[int, int, int], ol : int, name : str, type : tuple[str, str], coins : list[list['SkillEffect']], 
                 conditions : list['AnySkillConditional'] = None, tags : list[str]|None = None, skill_type : Any = None) -> None:
        self.base : int = basic_data[0]
        self.coin_power : int = basic_data[1]
        self.coin_amount : int = basic_data[2]
        self.ol : int = ol
        self.name : str = name
        self.type : tuple[str, str] = type
        self.tags : list[str] = [] if tags is None else tags
        self.coins : list[list[SkillEffect]] = coins

        if conditions is None: self.conditions = []
        else: self.conditions = conditions

        self.condition_state : list[bool] = [False for _  in self.conditions]
        self.crits : list = [None for _ in coins]
        self.ignore_no_poise = False
        
        self.skill_type = skill_type
    
    def has_tag(self, tag_name : str):
        if tag_name in self.tags: return True
        return False

    def copy_coin(self, coin_index : int):
        coin_to_copy = self.coins[coin_index]
        new_coin = [skill_effect.copy() for skill_effect in coin_to_copy]
        return new_coin
    
    def __str__(self) -> str:
        return self.name
    
    def process_environement(self, env):
        pass

    def reset(self):
        pass

    def set_conds(self, conds : list[bool]):
        self.condition_state = conds
    
    def set_crits(self, seq):
        self.crits = seq
    
    def apply_effect_if_cond(self, effect: "SkillEffect", env : 'Environment', condition_state):
        if callable(effect.condition):
            if effect.condition(effect, env):
                effect.apply(effect, env)
                #if env.debug_mode: print(f'applying effect with function {effect.apply.__name__}')
        elif effect.condition < 0:
            effect.apply(effect, env)
            #if env.debug_mode: print(f'applying effect with function {effect.apply.__name__}')

        elif effect.condition < len(condition_state):
            if condition_state[effect.condition]:
                effect.apply(effect, env)
                #if env.debug_mode: print(f'applying effect with function {effect.apply.__name__}')
        else:
            raise IndexError

    def calculate_damage(self, owner : "Unit", enemy: Enemy, debug = False, sequence : list[str|None] = None, 
                         clash_count : int = 0, ignore_fixed_damage : bool = True, entry_effects : list['SkillEffect']|None = None):
        if entry_effects is None: entry_effects = []
        condition_state = self.condition_state
        if sequence is None: sequence = [None for _ in self.coins]
        env = Environment(self, owner, enemy, debug)
        env.sequence = sequence
        env.ignore_fixed_damage = ignore_fixed_damage
        effect : SkillEffect

        for effect in owner.effects + entry_effects:
            self.apply_effect_if_cond(effect, env, condition_state)
        env.update_apply_queue()

        enemy.on_skill_start(env, is_defending = True)
        owner.on_skill_start(env, is_defending = False)
        env.update_apply_queue()

        
        ol_mult = (env.ol - env.def_level) / (abs(env.def_level - env.ol) + 25)
        env.static = 1 + env.p_res_mod + env.s_res_mod + ol_mult + (enemy.observation_level * 0.03) + (clash_count * 0.03)

        for i, effect in enumerate(self.conditions):
            self.apply_effect_if_cond(effect, env, condition_state)
        env.update_apply_queue()

        env.current_power = env.base
        
        
        if debug: print(f'Using skill {self.name} (skill type = {self.skill_type})')

        for i, coin in enumerate(self.coins):
            env.current_damage = 0
            env.current_coin_index = i
            for effect in env.effects:
                if effect.early_update:
                    effect.early_update(effect, env)
            env.update_apply_queue()
            if env.CANCEL_ATTACK:
                env.CANCEL_ATTACK = False
                env.update()
                if debug: print(f"Attack Cancelled")
                break
            if env.CANCEL_COIN:
                env.CANCEL_COIN = False
                env.update()
                if debug: print("Coin Cancelled")
                continue
            if i >= len(sequence):
                sequence.append(None)
            head_odds = 50 + owner.sp
            if sequence[i] == "Heads":
                env.current_power += env.coin_power

            elif sequence[i] == "Tails":
                pass
            
            else:
                rand_val = randint(1, 100)
                if rand_val <= head_odds:
                    env.current_power += env.coin_power
                    sequence[i] = "Heads"
                else:
                    sequence[i] = "Tails"

            if i >= len(self.crits):
                self.crits.append(None)


            if owner.poise["Potency"] <= 0 and self.ignore_no_poise == False:
                did_crit = False
            elif self.crits[i] is True:
                did_crit = True
                if env.CONSUME_POISE: owner.consume_poise(1)
            
            elif self.crits[i] is False:
                did_crit = False
            
            else:
                crit_odds = (owner.poise_potency * 0.05 * env.crit_odds_mult) + env.crit_odds_bonus
                if crit_odds > random():
                    did_crit = True
                    if env.CONSUME_POISE: owner.consume_poise(1)
                else:
                    did_crit = False

            env.did_crit = did_crit

            for effect in coin:
                self.apply_effect_if_cond(effect,env, condition_state)

            for effect in env.effects:
                if effect.mid_update:
                    effect.mid_update(effect, env)
            env.update_apply_queue()

            
            if env.CANCEL_ATTACK:
                env.CANCEL_ATTACK = False
                env.update()
                if debug: print(f"Attack Cancelled")
                break
            if env.CANCEL_COIN:
                env.CANCEL_COIN = False
                env.update()
                if debug: print("Coin Cancelled")
                continue


            ol_mult = (env.ol - env.def_level) / (abs(env.def_level - env.ol) + 25)
            env.static = 1.00 + env.s_res_mod + ol_mult + env.p_res_mod  + (enemy.observation_level * 0.00) + (clash_count * 0.03)
            if did_crit: env.static += env.crit_bonus


            val = max([ floor(env.current_power * env.static * env.dynamic), 1])
            env.current_damage += val
            
            enemy.hit(env.current_damage, env)
            env.total += env.current_damage

            for effect in env.effects:
                if effect.late_update:
                    effect.late_update(effect, env)
            

            if debug:
                print(f"Coin {i + 1}: power = {env.current_power}, damage = {env.current_damage}, static = {env.static:0.2f}, dynamic = {env.dynamic}")
                print(f"phys_res = {env.p_res_mod}, sin_res = {env.s_res_mod}, ol_mult = {ol_mult}\n")

            env.update_apply_queue()

            env.update()
            enemy.update_stagger_level()

            for effect in env.effects:
                if effect.megalate_update:
                    effect.megalate_update(effect, env)
            env.update_apply_queue()
            
        for effect in env.effects:
            effect.on_skill_end(effect, env)
            #if env.debug_mode: print(effect.on_skill_end.__name__)
        env.update_apply_queue()
        enemy.on_skill_end(env, is_defending = True)
        owner.on_skill_end(env, is_defending = False)

        for index, val in enumerate(sequence):
            if val is None:
                sequence[index] = 'None'
        if debug:
            print("-".join(sequence))

        result = env.total
        del env
        return result


class Unit:
    @classmethod
    def get_unit(cls, name):
        if not name in UNITS: print("unit was not found"); return None
        return UNITS[name]
    
    def __init__(self, name, skills) -> None:
        self.name = name
        self.sp = 0
        
        self.skills : list[Skill] = skills
        self.skill_1 : Skill = skills[0]
        self.skill_1.skill_type = 1
        self.skill_2 : Skill = skills[1]
        self.skill_2.skill_type = 2
        self.skill_3 : Skill = skills[2]
        self.skill_3.skill_type = 3
        self.extra_skills : list[Skill] = skills[3:]

        self.effects : list["SkillEffect"] = []
        self.unique_effects : dict[str, "SkillEffect"] = {}
        self.level : int = 40
        self.poise : dict[str, int] = {"Potency" : 0, "Count" : 0}
        self.next_turn_poise : dict[str, int] = {"Potency" : 0, "Count" : 0}
        self.statuses : dict[str, StatusEffect] = StatusDict()
        self.next_turn_statuses : dict[str, list[int]] = {}
    
    def clamp_sp(self):
        if self.sp > 45: self.sp = 45
        if self.sp < -45: self.sp = -45
    
    def apply_status(self, status_type : str, potency : int, count : int, env : Union['Environment', None] = None):
        if not status_type in self.statuses:
            status : StatusEffect = StatusEffect.new(status_type, (potency, count), self)
            self.statuses[status_type] = status
            status.when_first_applied(status, env, False)
        else:
            status : StatusEffect = self.statuses[status_type]
            status.add(potency, count)
            status.when_added(status, (potency, count), env, False)
    
    def apply_status_next_turn(self, status_type : str, potency : int, count : int):
        if status_type in self.next_turn_statuses:
            self.next_turn_statuses[status_type][0] += potency
            self.next_turn_statuses[status_type][1] += count
        else:
            self.next_turn_statuses[status_type] = [potency, count]
    
    def on_skill_start(self, env : 'Environment', is_defending : bool = False):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_skill_start(effect, env, is_defending=is_defending)

    def on_skill_end(self, env : 'Environment', is_defending : bool = False):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_skill_end(effect, env, is_defending=is_defending)
    
    def on_turn_start(self):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_turn_start(effect)

    def on_turn_end(self):
        effect_name : str
        effect : StatusEffect
        for effect_name in self.statuses:
            effect = self.statuses[effect_name]
            if not effect.is_active(): continue
            effect.on_turn_end(effect)
        for effect_name in self.next_turn_statuses:
            self.apply_status(effect_name, self.next_turn_statuses[effect_name][0], self.next_turn_statuses[effect_name][1])
        self.next_turn_statuses.clear()

        self.process_next_turn_poise()
    
    def process_next_turn_poise(self):
        self.add_poise_next_turn(self.next_turn_poise['Potency'], self.next_turn_poise['Count'])
        self.next_turn_poise['Potency'] = 0
        self.next_turn_poise['Count'] = 0

    def has_status(self, status_name : str):
        status : StatusEffect|None = self.statuses.get(status_name, None)
        if status is None: return False
        if not status.is_active(): return False
        return True

    
    @property
    def poise_potency(self) -> int:
        return self.poise['Potency']
    
    @poise_potency.setter
    def poise_potency(self, new_val : int):
        self.set_poise(new_val, self.poise['Count'])
    
    @property
    def poise_count(self):
        return self.poise['Count']
    
    @poise_count.setter
    def poise_count(self, new_val):
        self.set_poise(self.poise['Potency'], new_val)
    
    def apply_effect(self, effect : "SkillEffect"):
        self.effects.append(effect)
    
    def apply_unique_effect(self, effect_name : str, effect : 'SkillEffect', override : bool = False) -> bool:
        if override:
            if effect_name in self.unique_effects:
                old_effect = self.unique_effects.pop(effect_name)
                if old_effect in self.effects: self.effects.remove(old_effect)
            self.unique_effects[effect_name] = effect
            self.effects.append(effect)
            return True
        else:
            if effect_name in self.unique_effects:
                return False
            self.unique_effects[effect_name] = effect
            self.effects.append(effect)
            return True
            
    
    def clear_effects(self):
        self.effects.clear()
        self.unique_effects.clear()
    
    def clear_statuses(self):
        self.statuses.clear()
    
    def calculate_skill_rotation(self, enemy, debug = False):
        total = 0
        for _ in range(3):
            total += self.skill_1.calculate_damage(self, enemy, debug)

        total += self.skill_2.calculate_damage(self, enemy, debug)
        total += self.skill_2.calculate_damage(self, enemy, debug)

        total += self.skill_3.calculate_damage(self, enemy, debug)
        return total

    def __str__(self) -> str:
        return self.name
    
    def set_poise(self, potency, count):
        self.poise = {"Potency" : potency, "Count" : count}

        if self.poise["Potency"] <= 0 and self.poise["Count"]:
            self.poise["Potency"] = 1
        elif self.poise["Potency"] and self.poise["Count"] <=0:
            self.poise["Count"] = 1

    

    def add_poise(self, potency, count):
        self.poise["Potency"] += potency
        self.poise["Count"] += count

        if self.poise["Potency"] <= 0 and self.poise["Count"]:
            self.poise["Potency"] = 1
        elif self.poise["Potency"] and self.poise["Count"] <=0 :
            self.poise["Count"] = 1

    def add_poise_next_turn(self, potency, count):
        self.next_turn_poise["Potency"] += potency
        self.next_turn_poise["Count"] += count

        if self.next_turn_poise["Potency"] <= 0 and self.next_turn_poise["Count"]:
            self.next_turn_poise["Potency"] = 1
        elif self.next_turn_poise["Potency"] and self.next_turn_poise["Count"] <=0 :
            self.next_turn_poise["Count"] = 1

    def consume_poise(self, count = 1, potency = 0):
        self.poise["Count"] -= count
        self.poise["Potency"] -= potency

        if self.poise["Count"] <= 0 or self.poise["Potency"] <= 0:
            self.poise["Potency"] = 0
            self.poise["Count"] = 0
    
    def random_crit_sequence(self, amount):
        seq = [None for i in range(amount)]
        count = self.poise["Count"]
        pot = self.poise["Potency"]
        for i in range(amount):
            if count <= 0: pot = 0
            seq[i] = True if pot >= randint(1,20) else False
            count-=1
        return seq
        
        



class Environment:
    def __init__(self, skill : Skill, unit : Unit, enemy: Enemy, is_debugging = False) -> None:
        self.effects : dict[SkillEffect, Any] = {}
        self.static : int|float = 1 
        self.dynamic : int|float = 1

        self.skill = skill
        self.enemy = enemy
        self.unit =  unit

        
        p_type, s_type = skill.type
        
        self.p_res_mod = enemy.phys_res[p_type] - 1
        if self.p_res_mod < 0: self.p_res_mod /= 2

        
        self.s_res_mod = enemy.sin_res[s_type] - 1
        if self.s_res_mod < 0: self.s_res_mod /= 2

        self.ol = skill.ol + unit.level
        self.def_level_mod : int = 0
        ol_mult = (self.def_level - self.ol) / (abs(self.def_level - self.ol) + 25)
        self.crit_bonus = 0.20

        self.crit_odds_mult : float = 1
        self.crit_odds_bonus : float = 0


        self.static = 1.00 + ol_mult + self.p_res_mod + self.s_res_mod + (enemy.observation_level * 0.03)

        self.base = skill.base
        self.coin_power = skill.coin_power
        self.total = 0

        

        self.current_power = self.base
        self.current_damage = 0
        self.debug_mode = is_debugging

        self.did_crit : bool
        self.sequence : list[str|None]
        self.ignore_fixed_damage : bool = True
        self.current_coin_index : int = -1
        self.apply_queue : list[SkillEffect] = []

        self.updating_queue : bool = False
        self.global_state : dict[str, int]
        self.global_state = AttrStrDict()
        self.CONSUME_RUPTURE : bool = True
        self.CONSUME_POISE : bool = True
        self.CANCEL_ATTACK : bool = False
        self.CANCEL_COIN : bool = False
    
    @property
    def def_level(self) -> int:
        return self.enemy.def_level + self.def_level_mod

    def update_apply_queue(self):
        if self.updating_queue: return
        self.updating_queue = True
        while self.apply_queue:
            self.skill.apply_effect_if_cond(self.apply_queue[-1], self, self.skill.condition_state)
            self.apply_queue.pop()
        self.apply_queue.clear()
        self.updating_queue = False

    def get_target(self, name):
        if name[:5] == "unit.":
            target = self.unit
            new_name = name[5:]
        
        elif name[:6] == "enemy.":
            target = self.enemy
            new_name = name[6:]
        
        elif name[:6] == "skill.":
            target = self.skill
            new_name = name[6:]
        
        else:
            target = self
            new_name = name
        
        return target, new_name

    def get(self, name):
        return get_chained_attribute(self, name)
    
    def set(self, name, val):
        return set_chained_attribute(self, name, val)
    
    def add(self,name, val):
        old_val = self.get(name)
        new_val = old_val + val
        self.set(name, new_val)
        return self.get(name)
    
    def update(self):

        effect : SkillEffect
        effects_to_del = []
        
        for effect in self.effects:
            info = self.effects[effect]
            info[1] -=1
            if info[1] == 0:
                effect.remove(effect, self)
                effects_to_del.append(effect)
        
        for effect in effects_to_del:
            self.effects.pop(effect)
    
    def on_poise_gained(self, potency : int, count : int):
        for effect in self.effects:
            if effect.on_poise_gained:
                effect.on_poise_gained(effect, self, potency, count)
        self.update_apply_queue()
    
    def on_status_applied(self, status_name : str, potency : int, count : int):
        for effect in self.effects:
            if effect.on_status_applied:
                effect.on_status_applied(effect, self, status_name, potency, count)
        self.update_apply_queue()
    
    def on_tremor_burst(self):
        for effect in self.effects:
            if effect.on_tremor_burst:
                effect.on_tremor_burst(effect, self)
        self.update_apply_queue()

class SkillEffectConstructors:
    @staticmethod
    def SetGlobal(name : str, value : Any, condition : 'AnySkillConditional' = -1):
        return SkillEffect(name, 'set', value, condition=condition, apply_func=SpecialSkillEffects.set_global_state)

    @staticmethod
    def DamageUp(value : int):
        return sk.new("DamageUp", value)
    
    @staticmethod
    def TypedDamageUp(type : str, value : int):
        return sk.new("TypedDamageUp", (type, value))
    
    @staticmethod
    def DynamicBonus(value : float, condition : 'AnySkillConditional' = -1, duration : int = -1):
        return sk.new("DynamicBonus", value, condition, duration)
    
    @staticmethod
    def BasePowerUp(value : int, condition : 'AnySkillConditional' = -1, duration : int = -1):
        return sk.new("BasePower", value, condition=condition, the_duration=duration)
    
    @staticmethod
    def CoinPower(value : int, condition : 'AnySkillConditional' = -1, duration : int = -1):
        return sk.new("CoinPower", value, condition=condition, the_duration=duration)
    
    @staticmethod
    def OffenseLevelUp(value : int, condition : 'AnySkillConditional' = -1, duration : int = -1):
        return sk.new("OffenseLevelUp", value, condition=condition, the_duration=duration)
    
    @staticmethod
    def DefenseLevelDown(value : int, condition : 'AnySkillConditional' = -1, duration : int = -1):
        return sk.new("DefenseLevelDown", value, condition=condition, the_duration=duration)
    
    @staticmethod
    def ApplyFanatic(value : int, condition : 'AnySkillConditional' = -1):
        return sk.new("ApplyFanatic", value, condition)
    
    @staticmethod
    def ApplyBM(value : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.ApplyStatus('BM', 0, value, condition)
    
    @staticmethod
    def ApplyStatus(status_type : str, potency : int, count : int = 0, condition : 'AnySkillConditional' = -1):
        return sk.new("ApplyStatus", (status_type, potency, count), condition=condition)
    
    @staticmethod
    def ApplyAdditionalStatus(status_type : str, potency : int, count : int, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect(status_type, 'add', (potency, count), condition=condition, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.on_status_applied = SpecialSkillEffects.apply_additional_status
        return effect

    @staticmethod
    def ApplyStatusPot(status_type : str, potency : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.ApplyStatus(status_type, potency, 0, condition)

    @staticmethod
    def ApplyStatusCount(status_type : str, count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.ApplyStatus(status_type, 0, count, condition)

    @staticmethod
    def ApplyStatusNextTurn(status_type : str, potency : int, count : int = 0, condition : 'AnySkillConditional' = -1):
        return sk.new("ApplyStatusNextTurn", (status_type, potency, count), condition=condition)
    
    @staticmethod
    def ApplyStatusPotNextTurn(status_type : str, potency : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.ApplyStatusNextTurn(status_type, potency, 0, condition)
    
    @staticmethod
    def ApplyStatusCountNextTurn(status_type : str, count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.ApplyStatusNextTurn(status_type, 0, count, condition)

    @staticmethod
    def GainStatus(status_type : str, potency : int, count : int, condition : 'AnySkillConditional' = -1):
        return sk.new("GainStatus", (status_type, potency, count), condition=condition)

    @staticmethod
    def GainStatusNextTurn(status_type : str, potency : int, count : int, condition : 'AnySkillConditional' = -1):
        return sk.new("GainStatusNextTurn", (status_type, potency, count), condition=condition)
    
    @staticmethod
    def GainPoise(potency : int, count : int = 0, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", 'add', 0, condition=condition, data=[potency, count])
        effect.apply = SpecialSkillEffects.gain_poise
        return effect
    
    @staticmethod
    def GainPoiseNextTurn(potency : int, count : int = 0, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", 'add', 0, condition=condition, data=[potency, count])
        effect.apply = SpecialSkillEffects.gain_poise_next_turn
        return effect
    
    @staticmethod
    def GainPoiseCount(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.GainPoise(0, count, condition)
    
    @staticmethod
    def GainPoiseCountNextTurn(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffectConstructors.GainPoiseNextTurn(0, count, condition)
    
    @staticmethod
    def GainAdditionalPoise(potency : int, count : int, condition : 'AnySkillConditional' = -1):
        return sk.new("GainAdditionalPoise", (potency, count), condition=condition)
    
    @staticmethod
    def GainCharge(count : int, condition : 'AnySkillConditional' = -1):
        return sk.new("GainCharge", count, condition=condition)

    @staticmethod
    def ConsumeCharge(count : int, condition : 'AnySkillConditional' = -1):
        return sk.new("ConsumeCharge", count, condition=condition)
    
    @staticmethod
    def GainTremor(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('unit.tremor', 'add', count, condition=condition)
    
    @staticmethod
    def InflictTremor(potency : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('enemy.tremor', 'add', potency, condition=condition)

    @staticmethod
    def InflictTremorCount(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('enemy.tremor_count', 'add', count, condition=condition)
    
    @staticmethod
    def ConsumeChargeTrigger(count : int, effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        return sk.new("ConsumeChargeTrigger", (count, effect), condition=condition)

    @staticmethod
    def ConsumeRessourceTrigger(name : str, count : int|float, treshold : int, effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        return sk.new("ConsumeRessourceTrigger", (name, count, treshold, effect), condition=condition)

    @staticmethod
    def OnUse(other_effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
        effect.apply = SpecialSkillEffects.on_hit_trigger
        effect.special_data = other_effect
        return effect

    @staticmethod
    def OnHit(other_effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
        effect.late_update = SpecialSkillEffects.on_hit_trigger
        effect.special_data = other_effect
        return effect
    
    @staticmethod
    def OnAttackEnd(other_effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
        effect.on_skill_end = SpecialSkillEffects.on_hit_trigger
        effect.special_data = other_effect
        return effect

    @staticmethod
    def OnHeadsHit(effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        return sk.new("OnHeadsHit", effect, condition=condition)
    
    @staticmethod
    def OnTailsHit(effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        return sk.new("OnTailsHit", effect, condition=condition)
    
    @staticmethod
    def OnCrit(effect : 'SkillEffect', condition : 'AnySkillConditional' = -1, duration : int = 1):
        return sk.new("OnCrit", effect, condition=condition, the_duration=duration)
    
    @staticmethod
    def OnCritRoll(effect : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        return sk.new("OnCritRoll", effect, condition=condition)
    
    @staticmethod
    def AfterAttack(effect_to_trigger : 'SkillEffect', condition : 'AnySkillConditional' = -1):
        effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=-1)
        effect.on_skill_end = SpecialSkillEffects.on_hit_trigger
        effect.special_data = effect_to_trigger
        return effect
    
    @staticmethod
    def HealSP(value : int, duration : int = -1, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('unit.sp', 'add', value, duration, condition)
        effect.apply = SpecialSkillEffects.heal_sp
        return effect
    
    @staticmethod
    def LoseSP(value : int, duration : int = -1, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('unit.sp', 'add', value, duration, condition)
        effect.apply = SpecialSkillEffects.lose_sp
        return effect
    
    @staticmethod
    def AddXForEachY(x_step : float|int, x_name : Union[str, 'SetterMethod'], y_step : float|int, 
                      y_name : Union[str, 'GetterMethod'], min : float|int = 0, max : float|int = 1, offset : float|int = 0,
                      condition : 'AnySkillConditional' = -1, duration : int = -1):
        effect = SkillEffect(x_name, "add", x_step, condition= condition, duration=duration, 
        data = {"x_step": x_step, "x_name": x_name, "y_step": y_step, "y_name": y_name, "range": (min, max), "offset" : offset})
        
        effect.apply = SpecialSkillEffects.add_foreach_y
        return effect
    
    @staticmethod
    def DAddXForEachY(x_step : float|int, x_name : Union[str, 'SetterMethod'], y_step : float|int, 
                      y_name : Union[str, 'GetterMethod'], min : float|int = 0, max : float|int = 1, offset : float|int = 0,
                      condition : 'AnySkillConditional' = -1):
        effect = SkillEffect(x_name, "add", x_step, condition= condition, duration=-1, 
        data = {"x_step": x_step, "x_name": x_name, "y_step": y_step, "y_name": y_name, "range": (min, max), "offset" : offset})
        
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.d_add_foreach_y
        effect.megalate_update = SpecialSkillEffects.d_add_foreach_y_cleanup
        return effect
    
    @staticmethod
    def AddStatusPotForEachY(value : int, status_name : str, y_step : float|int, y_name : str, min : int = 0, max : int = 1, offset : int = 0,
                            condition : 'AnySkillConditional' = -1, duration : int = -1, next_turn : bool = False):
        
        effect = SkillEffect(status_name, "add", value, condition= condition, duration=duration, 
        data = {"x_step": value, "status_name": status_name, "y_step": y_step, "y_name": y_name, "range": (min, max), "offset" : offset, 'next_turn' : next_turn})
        effect.apply = SpecialSkillEffects.add_pot_foreach_y
        return effect
    
    @staticmethod
    def AddStatusCountForEachY(value : int, status_name : str, y_step : float|int, y_name : str, min : int = 0, max : int = 1, offset : int = 0,
                            condition : 'AnySkillConditional' = -1, duration : int = -1, next_turn : bool = False):
        
        effect = SkillEffect(status_name, "add", value, condition= condition, duration=duration, 
        data = {"x_step": value, "status_name": status_name, "y_step": y_step, "y_name": y_name, "range": (min, max), "offset" : offset, 'next_turn' : next_turn})
        effect.apply = SpecialSkillEffects.add_count_foreach_y
        return effect

    @staticmethod
    def GainStatusCountForEachY(value : int, status_name : str, y_step : float|int, y_name : str, min : int = 0, max : int = 1, offset : int = 0,
                            condition : 'AnySkillConditional' = -1, duration : int = -1, next_turn : bool = False):
        
        effect = SkillEffect(status_name, "add", value, condition= condition, duration=duration, 
        data = {"x_step": value, "status_name": status_name, "y_step": y_step, "y_name": y_name, "range": (min, max), "offset" : offset, 'next_turn' : next_turn})
        effect.apply = SpecialSkillEffects.gain_count_foreach_y
        return effect

    @staticmethod
    def ReuseCoin(reuse_count : int, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('dynamic', 'add', reuse_count, condition=condition, 
        apply_func=SpecialSkillEffects.apply_reuse, remove_func=SpecialSkillEffects.remove_nothing)
        effect.special_data = 0
        effect.megalate_update = SpecialSkillEffects.reuse_coin_late_update
        effect.on_skill_end = SpecialSkillEffects.on_reuse_end
        return effect
    
    @staticmethod
    def ReuseCoinConditional(reuse_count : int, eval_func : Callable[['SkillEffect', Environment], bool], condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('dynamic', 'add', (reuse_count, eval_func), condition=condition, 
        apply_func=SpecialSkillEffects.apply_reuse, remove_func=SpecialSkillEffects.remove_nothing)
        effect.special_data = 0
        effect.megalate_update = SpecialSkillEffects.reuse_coin_cond_late_update
        effect.on_skill_end = SpecialSkillEffects.on_reuse_end
        return effect

    @staticmethod
    def PeqSangReuseCoin(reuse_count : int, condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('dynamic', 'add', reuse_count, condition=condition, 
        apply_func=SpecialSkillEffects.apply_reuse, remove_func=SpecialSkillEffects.remove_nothing)
        effect.special_data = 0
        effect.megalate_update = SpecialSkillEffects.peq_sang_reuse_coin_late_update
        effect.on_skill_end = SpecialSkillEffects.on_reuse_end
        return effect

    @staticmethod
    def Fragile(count : int, status_effect : 'StatusEffect'):
        effect = SkillEffect('dynamic', 'add', count)
        effect.special_data = status_effect
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.FragileEarlyUpdate
        effect.megalate_update = SpecialSkillEffects.FragileCleanup
        return effect
    
    @staticmethod
    def FestiveFever(count : int, status_effect : 'StatusEffect'):
        effect = SkillEffect('dynamic', 'add', count)
        effect.special_data = status_effect
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.FestiveFeverEarlyUpdate
        effect.megalate_update = SpecialSkillEffects.FragileCleanup
        return effect

    @staticmethod
    def MaidRyoPassive():
        return sk.new("MaidRyoPassive", None)

    @staticmethod
    def MCFaustS2ChargeGain():
        return sk.new("MCFaustS2ChargeGain", None)
    
    @staticmethod
    def MCFaustS3ChargeGain():
        return sk.new("MCFaustS3ChargeGain", None)
    
    @staticmethod
    def MCFaustS2DamageBonus(condition : 'AnySkillConditional' = -1):
        return sk.new("MCFaustS2DamageBonus", None, condition=condition)
    
    @staticmethod
    def MCFaustS3DamageBonus():
        return sk.new("MCFaustS3DamageBonus", None)
    
    @staticmethod
    def MCFaustPassive(low_hp_enemy : bool = False):
        return sk.new("MCFaustPassive", low_hp_enemy)

    @staticmethod
    def Photoelectricity(value : int, condition : 'AnySkillConditional' = -1):
        return sk.new("Photoelectricity", value, condition=condition)
    
    @staticmethod
    def ButlerOutisS3Bonus(condition : 'AnySkillConditional' = -1):
        return sk.new('ButlerOutisS3Bonus', None, condition=condition)

    @staticmethod
    def ButlerOutisPassive(did_clash : bool = False):
        return sk.new('ButlerOutisPassive', did_clash)
    
    @staticmethod
    def WarpOutisPassive():
        return sk.new('WarpOutisPassive', None)
    
    @staticmethod
    def WarpOutisChargeBarrier():
        return sk.new('WarpOutisChargeBarrier', None)
    
    @staticmethod
    def WarpOutisCoinpowerS3():
        return sk.new('WarpOutisCoinpowerS3', None)
    
    @staticmethod
    def WarpOutisChargeGainS3():
        return sk.new('WarpOutisChargeGainS3', None)
    
    @staticmethod
    def MidDonResonanceBonus():
        return sk.new("MidDonResonanceBonus", None)
    
    @staticmethod
    def MidDonPassive():
        return SkillEffect('coin_power', 'add', 0, apply_func=SpecialSkillEffects.MidDonPassive)
    
    @staticmethod
    def CounterBasepowerGain():
        return sk.new("CounterBasepowerGain", None)
    
    @staticmethod
    def ResetAttackWeight(count : int = 1, condition : 'AnySkillConditional' = -1):
        return sk.new("ResetAttackWeight", count, condition=condition)
    
    @staticmethod
    def RegretBurst():
        return sk.new("RegretBurst", None)
    
    @staticmethod
    def LiuIshPassive():
        return sk.new('LiuIshPassive', None)
    
    @staticmethod
    def LiuIshS2Burn():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.LiuIshS2Burn
        return effect
    
    @staticmethod
    def LiuDyaS2Burn():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.LiuDyaS2Burn
        return effect

    @staticmethod
    def LiuDyaS3Burst():
        return SkillEffect('current_damage', 'add', 0, apply_func=SpecialSkillEffects.LiuDyaS3Burst)
    
    @staticmethod
    def LiuDyaS3Bonus():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.early_update = SpecialSkillEffects.LiuDyaS3Bonus
        effect.late_update = SpecialSkillEffects.LiuDyaS3BonusCleanup
        return effect
    
    @staticmethod
    def LiuDyaPassive(slot_priority : bool = False):
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.LiuDyaPassiveSkillStart
        effect.early_update = SpecialSkillEffects.LiuDyaPassive
        effect.late_update = SpecialSkillEffects.LiuDyaPassiveCleanup
        effect.special_data = slot_priority
        return effect
    
    @staticmethod
    def HuntCliffS4Bonus():
        return SkillEffect('current_damage', 'add', 0, apply_func=SpecialSkillEffects.HuntCliffS4Bonus)
    
    @staticmethod
    def HuntCliffS4Regen():
        effect = SkillEffect('unit.sp', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.megalate_update = SpecialSkillEffects.HuntCliffS4Regen
        return effect
    
    @staticmethod
    def HuntCliffS3Sinking():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.HuntCliffS3Sinking
        return effect
    
    @staticmethod
    def HuntCliffSpBonus():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.HuntCliffSpBonus
        return effect
    
    @staticmethod
    def ChargePotencyConversionPassive(treshold : int = 10):
        effect = SkillEffect('unit.charge', 'add', treshold, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.ChargePotencyConversionPassive
        return effect
    
    @staticmethod
    def MCHeathS3ChargeGain():
        return SkillEffect('unit.charge', 'add', 0, apply_func=SpecialSkillEffects.MCHeathS3ChargeGain)
    
    @staticmethod
    def EchoesOfTheManor():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.on_status_applied = SpecialSkillEffects.EchoesOnStatusApplied
        return effect
    
    @staticmethod
    def PirateGregS3Bonus():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.late_update = SpecialSkillEffects.PirateGregS3Bonus
        return effect
    
    @staticmethod
    def PirateGregorPassive():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.megalate_update = SpecialSkillEffects.PirateGregPassiveMegaLateUpdate
        return effect
    
    @staticmethod
    def SwordplayOfTheHomeland():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.SwordplayOfTheHomeland
        return effect
    
    @staticmethod
    def RedPlumBlossom(count : int, status_effect : 'StatusEffect'):
        effect = SkillEffect('dynamic', 'add', count)
        effect.special_data = status_effect
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.RedPlumBlossomEarlyUpdate
        effect.late_update = SpecialSkillEffects.RedPlumBlossomLateUpdate
        effect.megalate_update = SpecialSkillEffects.RedPlumBlossomMegaLateUpdate
        return effect
    
    @staticmethod
    def BlFaustS3Conversion(condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('unit.poise_potency', 'add', 0, condition=condition)
        effect.apply = SpecialSkillEffects.BlFaustS3Conversion
        return effect
    
    @staticmethod
    def BlFaustPassive():
        effect = SkillEffect('unit.poise_potency', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.late_update = SpecialSkillEffects.BlFaustPassive
        return effect
    
    @staticmethod
    def WarpSangS3CoinPower():
        effect = SkillEffect('coin_power', 'add', 0)
        effect.apply = SpecialSkillEffects.WarpSangS3CoinPower
        return effect
    
    @staticmethod
    def SevenFaustPassive():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.SevenFaustPassive)
    
    @staticmethod
    def RingOutisReuse():
        effect = SkillEffect('current_damage', 'add', 0)
        effect.special_data = 0
        effect.mid_update = SpecialSkillEffects.RingOutisS2Reuse
        effect.on_skill_end = SpecialSkillEffects.RingOutisS2End
        return effect
    
    @staticmethod
    def RingRandomStatus(potency : int, count : int):
        effect = SkillEffect("dynamic", "add", 0)
        effect.special_data = [potency, count]
        effect.apply = SpecialSkillEffects.RingRandomStatus
        return effect
    
    @staticmethod
    def RingOutisS3Bonus():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.mid_update = SpecialSkillEffects.RingOutisS3Bonus
        effect.megalate_update = SpecialSkillEffects.d_add_foreach_y_cleanup
        return effect

    @staticmethod
    def DawnClairS4Bonus():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.DawnClairS4Bonus
        return effect
    
    @staticmethod
    def DawnClairCoinPower():
        effect = SkillEffect('coin_power', 'add', 0)
        effect.apply = SpecialSkillEffects.DawnClairCoinPower
        return effect

    @staticmethod
    def MBOutisBurn():
        return skc.AddStatusPotForEachY(1, "Burn", 1, "enemy.statuses.Dark Flame.count", 0, 7)

    @staticmethod
    def NextTurnDarkFlame(count : int):
        return skc.ApplyStatusCountNextTurn(StatusNames.dark_flame, count)
    
    @staticmethod
    def NextTurnDarkFlameBullet():
        return skc.AddStatusCountForEachY(1, StatusNames.dark_flame, 1, 'unit.bullet', 0, 7, next_turn=True)
    
    @staticmethod
    def MBOutisS2BulletGain():
        return SkillEffect('unit.bullet', 'add', 1, apply_func=SpecialSkillEffects.MBOutisS2BulletGain)
    
    @staticmethod
    def MBOutisS3Effects():
        effect= SkillEffect('dynamic', 'add', 0)
        effect.apply = SpecialSkillEffects.MBOutisS3BeforeAttack
        effect.megalate_update = SpecialSkillEffects.MBOutisS3AfterAttack
        return effect

    @staticmethod
    def MBOutisPassive():
        effect= SkillEffect('dynamic', 'add', 0, duration=1)
        effect.early_update = SpecialSkillEffects.MBOutisPassive
        return effect
    
    @staticmethod
    def BlDonS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BlDonS3Bonus)

    @staticmethod
    def MolarIshPassive():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.late_update = SpecialSkillEffects.MolarIshPassive
        return effect
    
    @staticmethod
    def LDonS2Rupture():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.LDonS2Rupture)
    
    @staticmethod
    def MolarClairS3Spend():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.MolarClairS3Spend)
    
    @staticmethod
    def NCliffS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.NCliffS3Bonus)
    
    @staticmethod
    def LiuGregorPassive():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.late_update = SpecialSkillEffects.LiuGregorPassive
        return effect

    @staticmethod
    def ButlerFaustPassive():
        return SkillEffectConstructors.AddStatusPotForEachY(3, 'Sinking', 1, 'enemy.statuses.Echoes of the Manor.count', 1, 3, condition=0)
    
    @staticmethod
    def RedEyesGain(count : int):
        effect = SkillEffect('dynamic', 'add', count, 1, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.RedEyesBonus
        effect.late_update = SpecialSkillEffects.RedEyesGain
        return effect
    
    @staticmethod
    def PenitenceGain(count : int):
        effect = SkillEffect('dynamic', 'add', count, 1, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.PenitenceBonus
        effect.late_update = SpecialSkillEffects.PenitenceGain
        return effect
    
    @staticmethod
    def RedRyoS1PenitenceGain():
        effect = SkillEffect('dynamic', 'add', 3, 1, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.PenitenceBonus
        effect.late_update = SpecialSkillEffects.PenitenceS1Gain
        return effect
    
    @staticmethod
    def RedRyoS2RedEyesGain():
        effect = SkillEffect('dynamic', 'add', 3, 1, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.RedEyesBonus
        effect.late_update = SpecialSkillEffects.RedEyesS2Gain
        return effect
    
    @staticmethod
    def RedRyoS3PenitenceGain():
        effect = SkillEffect('dynamic', 'add', 3, 1, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.PenitenceBonus
        effect.late_update = SpecialSkillEffects.PenitenceS3Gain
        return effect
    
    @staticmethod
    def RedRyoS4PowerGain():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.RedRyoS4PowerGain)
    
    @staticmethod
    def RedRyoS4AfterAttack():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.RedRyoS4AfterAttack)
    
    @staticmethod
    def RedRyoS4Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.RedRyoS4Bonus)
    
    @staticmethod
    def RedRyoS4Bleed():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.RedRyoS4Bleed)
    
    @staticmethod
    def RedRyoBaseSpHeal():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.late_update = SpecialSkillEffects.RedRyoBaseSpHeal
        return effect
    
    
    @staticmethod
    def RedRyoBonusBleed():
        effect = SkillEffect('dynamic', 'add', 0)
        effect.on_status_applied = SpecialSkillEffects.RedRyoBonusBleed
        return effect
    
    @staticmethod
    def YuroRyoS2Count():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.YuroRyoS2Count)
    
    @staticmethod
    def GCorpGregorS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.GCorpGregorS3Bonus)

    @staticmethod
    def GainCourrierTrunk(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', count, apply_func=SpecialSkillEffects.GainCourrierTrunk, condition=condition)
    
    @staticmethod
    def DevyatRodyaCoinPower():
        effect = SkillEffect('coin_power', 'add', 0)
        effect.early_update = SpecialSkillEffects.DevyatRodyaCoinPower
        effect.late_update = SpecialSkillEffects.d_add_foreach_y_cleanup
        return effect
    
    @staticmethod
    def DVRRuptureCondCheck():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DVRRuptureCondCheck)
    
    @staticmethod
    def FLuRuptureCondCheck():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.FLuRuptureCondCheck)
    
    @staticmethod
    def StopRuptureDrain(condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.StopRuptureDrain, condition=condition)

    @staticmethod
    def GainErudition(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', count, apply_func=SpecialSkillEffects.GainErudition, condition=condition)
    
    @staticmethod
    def DeiciMeurS3Insight():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DeiciMeurS3Insight)
    
    @staticmethod
    def DeiciMeurS3Sinking():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DeiciMeurS3Sinking)
    
    @staticmethod
    def DeiciMeurResetInsight():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.on_skill_end = SpecialSkillEffects.DeiciMeurResetInsight
        return effect
    
    @staticmethod
    def HeirGregorS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.HeirGregorS3Bonus)

    @staticmethod
    def ZweiIshDlTremorConversion(maximum : int = 5):
        return SkillEffectConstructors.GainStatusCountForEachY(1, StatusNames.defense_level_up, 2, 'unit.tremor', 0, maximum)
    
    @staticmethod
    def ZweiIshS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ZweiIshS3Bonus)
    
    @staticmethod
    def SpicebushS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.SpicebushS3Bonus)
    
    @staticmethod
    def SpiceBushSinkingDeluge():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.SpiceBushSinkingDeluge)
        effect.apply = SpecialSkillEffects.SpiceBushSinkingDeluge
        return effect
    
    @staticmethod
    def SpicebushS2AOE():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.SpicebushS2AOE)
        effect.apply = SpecialSkillEffects.SpicebushS2AOE
        return effect
    
    @staticmethod
    def Fanatic(count : int, status_effect : 'StatusEffect'):
        effect = SkillEffect('base', 'add', count)
        effect.special_data = status_effect
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.FanaticEarlyUpdate
        effect.megalate_update = SpecialSkillEffects.FanaticCleanup
        return effect

    @staticmethod
    def StopPoiseDrain(condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.StopPoiseDrain, condition=condition)
    
    @staticmethod
    def MidMeurPassive():
        return SkillEffect('coin_power', 'add', 0, apply_func=SpecialSkillEffects.MidMeurPassive)
    
    @staticmethod
    def WeaknessAnalyzed(condition : 'AnySkillConditional' = -1):
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.WeaknessAnalyzed, condition=condition)
        effect.on_skill_end = SpecialSkillEffects.WeaknessAnalyzedCleanup
        return effect
    
    @staticmethod
    def SevenOutisS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.SevenOutisS3Bonus)
    
    @staticmethod
    def SevenOutisPassive():
        return SkillEffect('dynamic', 'add', 0.1, condition=SkillConditionals.EnemyPhysResWeakOrFatal)
    
    @staticmethod
    def Tremor(potency : int, status_effect : 'StatusEffect'):
        effect = SkillEffect('def_level_mod', 'add', potency)
        effect.special_data = status_effect
        effect.apply = SpecialSkillEffects.apply_nothing_wduration
        effect.early_update = SpecialSkillEffects.TremorEarlyUpdate
        effect.megalate_update = SpecialSkillEffects.TremorCleanup
        return effect
    
    @staticmethod
    def TremorDecayConversion():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TremorDecayConversion, condition=SkillConditionals.TremorSumAbove20)

    @staticmethod
    def OufiHeathcliffPassive():
        return SkillEffectConstructors.DAddXForEachY(0.1, 'dynamic', 6, 'enemy.statuses.Tremor.potency', 0, 0.3)
    
    @staticmethod
    def ZweiSinclairWestS3Tremor():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ZweiSinclairWestS3Tremor)
    
    @staticmethod
    def CinqMeurS3HeadsBonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.CinqMeurS3HeadsBonus)
    
    @staticmethod
    def TRodyaS3CoinPower():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TRodyaS3CoinPower)
    
    @staticmethod
    def TRodyaMoratium():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TRodyaMoratium)
    
    @staticmethod
    def TDonMoratium():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TDonMoratium)
    
    @staticmethod
    def ButterflySangConsumeAmmo(count : int):
        return SkillEffect('dynamic', 'add', count, apply_func=SpecialSkillEffects.ButterflySangConsumeAmmo)
    
    @staticmethod
    def ButterflySangS3ConsumeAmmo():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ButterflySangS3ConsumeAmmo)
    
    @staticmethod
    def ButterflySangS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ButterflySangS3Bonus)
    
    @staticmethod
    def InflictBulletButterfly():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.InflictBulletButterfly)
    
    @staticmethod
    def ButterflySangReload(condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ButterflySangReload, condition=condition)
    
    @staticmethod
    def ButterflySangShortcut(count : int):
        return (skc.ButterflySangConsumeAmmo(count), skc.OnHit(skc.InflictBulletButterfly()))
    
    @staticmethod
    def ButterflySangCondReload():
        return skc.AfterAttack(skc.ButterflySangReload(condition=SkillConditionals.ButterSangAttackCancelled))
    
    @staticmethod
    def Butterfly(status_effect : 'StatusEffect'):
        effect = SkillEffect('dynamic', 'add', status_effect)
        effect.apply = SpecialSkillEffects.ButterflyEffect
        effect.late_update = SpecialSkillEffects.ButterflyEffectLateUpdate
        return effect
    
    @staticmethod
    def TCorpLuPassive():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TCorpLuPassive)
        effect.on_tremor_burst = SpecialSkillEffects.TCorpLuPassiveOnTremorBurst
        return effect
    
    @staticmethod
    def TremorBurst(count_reduced : int = 0, condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', count_reduced, apply_func=SpecialSkillEffects.TremorBurst, condition=condition)
    
    @staticmethod
    def ReverbEntanglement(condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.ReverbEntanglement, condition=condition)
    
    @staticmethod
    def TCorpLuS3CoinPower():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.TCorpLuS3CoinPower)
    
    @staticmethod
    def BarberOutisS1Bloodfeast():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BarberOutisS1Bloodfeast)
    
    @staticmethod
    def BarberOutisS2Bloodfeast():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BarberOutisS2Bloodfeast)
    
    @staticmethod
    def BarberOutisS3Bonus():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BarberOutisS3Bonus)
    
    @staticmethod
    def BarberOutisS3AtkWeight():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BarberOutisS3AtkWeight)
    
    @staticmethod
    def BarberOutisResetAtkWeight():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.BarberOutisResetAtkWeight)
    
    @staticmethod
    def BarberOutisPassive():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.early_update = SpecialSkillEffects.BarberOutisPassiveEarlyUpdate
        effect.megalate_update = SpecialSkillEffects.d_add_foreach_y_cleanup
        return effect
    

    
    @staticmethod
    def FangLuPassive():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.mid_update = SpecialSkillEffects.FangLuPassiveMidUpdate
        effect.late_update = SpecialSkillEffects.FangLuPassiveLateUpdate
        effect.megalate_update = SpecialSkillEffects.FangLuPassiveMegalateUpdate
        return effect
    
    @staticmethod
    def FixedDamage(damage : int):
        return SkillEffect('total', 'add', damage, apply_func=SpecialSkillEffects.FixedDamage)
    
    @staticmethod
    def GainBloodiedHand(count : int):
        return SkillEffect('dynamic', 'add', count, apply_func=SpecialSkillEffects.GainBloodiedHand)
    
    @staticmethod
    def PriestGregorS1OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.PriestGregorS1OnUse)

    @staticmethod
    def PriestGregorS2OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.PriestGregorS2OnUse)
    
    @staticmethod
    def PriestGregorS3OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.PriestGregorS3OnUse)
    
    @staticmethod
    def PriestGregorInnatePassive():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.late_update = SpecialSkillEffects.PriestGregorInnatePassiveOnHit
        return effect
    
    @staticmethod
    def GainBloomingThorn(count : int, condition : 'AnySkillConditional' = -1):
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.GainBloomingThorn)

    
    @staticmethod
    def DulcRodyaS1OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DulcRodyaS1OnUse)
    
    @staticmethod
    def DulcRodyaS2OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DulcRodyaS2OnUse)
    
    @staticmethod
    def DulcRodyaS3OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DulcRodyaS3OnUse)
    
    @staticmethod
    def DulcRodyaS4OnUse():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DulcRodyaS4OnUse)
    
    @staticmethod
    def DulcRodyaS4AfterAttack():
        return SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.DulcRodyaS4AfterAttack)

    @staticmethod
    def DulcRodyaInnatePassive():
        effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration)
        effect.on_status_applied = SpecialSkillEffects.DulcRodyaInnatePassive
        return effect


def get_dlup_str():
    return f'unit.statuses.{StatusNames.defense_level_up}.count'

class SkillEffect:
    @classmethod
    def new(cls, effect_type : str, values, condition : 'AnySkillConditional' = -1, the_duration : int = -1):
        if type(values) != tuple and type(values) != list:
            values = [values]
        
        if effect_type == "OnHit":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.late_update = SpecialSkillEffects.on_hit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnHeadsHit":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.late_update = SpecialSkillEffects.on_heads_hit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnHeadsRoll":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.mid_update = SpecialSkillEffects.on_heads_hit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnTailsHit":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.late_update = SpecialSkillEffects.on_tails_hit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnTailsRoll":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.mid_update = SpecialSkillEffects.on_heads_hit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnCritRoll":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=1)
            effect.mid_update = SpecialSkillEffects.on_crit_trigger
            effect.special_data = values[0]
            return effect
        
        elif effect_type == "OnCrit":
            effect = SkillEffect("dynamic", "add", 0, condition= condition, duration=the_duration)
            effect.late_update = SpecialSkillEffects.on_crit_trigger
            effect.special_data = values[0]
            return effect

        elif effect_type == "ReuseCoin":
            effect = SkillEffect('dynamic', 'add', values[0], condition=condition, 
            apply_func=SpecialSkillEffects.apply_reuse, remove_func=SpecialSkillEffects.remove_nothing)
            effect.special_data = 0
            effect.megalate_update = SpecialSkillEffects.reuse_coin_late_update
            effect.on_skill_end = SpecialSkillEffects.on_reuse_end
            return effect

        elif effect_type == "DamageUp":
            return SkillEffect("dynamic", "add", values[0] * 0.1, condition= condition)

        elif effect_type == "Fragile":
            effect = SkillEffect("dynamic", "add", values[0] * 0.1, condition= condition)
            effect.apply = SpecialSkillEffects.add_frag_to_env
            effect.remove = SkillEffect.remove
            effect.megalate_update = SpecialSkillEffects.apply_fragile
            return effect
        
        elif effect_type == "ApplyStatus":
            effect = SkillEffect(values[0], 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.apply_status
            effect.special_data = [values[1], values[2]]
            return effect
        
        elif effect_type == "ApplyStatusNextTurn":
            effect = SkillEffect(values[0], 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.apply_status_next_turn
            effect.special_data = [values[1], values[2]]
            return effect

        elif effect_type == "GainStatus":
            effect = SkillEffect(values[0], 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.gain_status
            effect.special_data = [values[1], values[2]]
            return effect
        
        elif effect_type == "GainStatusNextTurn":
            effect = SkillEffect(values[0], 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.gain_status_next_turn
            effect.special_data = [values[1], values[2]]
            return effect
        
        elif effect_type == "GainCharge":
            effect = SkillEffect('unit.charge', 'add', values[0])
            effect.apply = SpecialSkillEffects.gain_charge
            return effect
        
        elif effect_type == "ConsumeCharge":
            effect = SkillEffect('unit.charge', 'add', values[0], condition=condition)
            effect.apply = SpecialSkillEffects.consume_charge
            return effect
        
        elif effect_type == "ConsumeChargeTrigger":
            effect = SkillEffect('unit.charge', 'add', values[0], condition=condition)
            effect.special_data = values[1]
            effect.apply = SpecialSkillEffects.consume_charge_to_trigger_effect
            return effect

        elif effect_type == "ConsumeRessourceTrigger":
            effect = SkillEffect(values[0], 'add', values[1])
            effect.special_data = [values[2], values[3]]
            effect.apply = SpecialSkillEffects.consume_ressource_to_trigger_effect
            return effect

        elif effect_type == "CounterBasepowerGain":
            effect = SkillEffect('base', 'add', 0)
            effect.apply = SpecialSkillEffects.counter_basepower_gain
            return effect

        elif effect_type == "ApplyFanatic":
            return SkillEffect("unit.fanatic", 'add', values[0], condition=condition)

        elif effect_type == "DynamicBonus":
            return SkillEffect("dynamic", "add", values[0], condition= condition, duration=the_duration)
        
        elif effect_type == "CoinPower":
            return SkillEffect("coin_power", "add", values[0], condition= condition, duration=the_duration)
        
        elif effect_type == "GainPoise":
            effect = SkillEffect("dynamic", 'add', 0, condition=condition, data=[values[0], values[1]])
            effect.apply = SpecialSkillEffects.gain_poise
            return effect
        
        elif effect_type == "GainAdditionalPoise":
            effect = SkillEffect("dynamic", 'add', 0, condition=condition, data=[values[0], values[1]])
            effect.on_poise_gained = SpecialSkillEffects.gain_additional_poise
            return effect
        
        elif effect_type == "SetPoise":
            effect = SkillEffect("dynamic", 'add', 0, condition=condition, data=[values[0], values[1]])
            effect.apply = SpecialSkillEffects.set_poise
            return effect

        elif effect_type == "CriticalDamageBonus":
            effect = SkillEffect("dynamic", 'add', values[0], condition=condition, duration=the_duration)
            effect.apply = SpecialSkillEffects.apply_nothing_wduration
            effect.mid_update = SpecialSkillEffects.CriticalDamageBonusUpdate
            effect.megalate_update = SpecialSkillEffects.CriticalDamageBonusCleanup
            return effect
        
        elif effect_type == "AddXForEachY":
            if len(values) > 5: offset = values[5]
            else: offset = 0
            effect = SkillEffect(values[1], "add", values[0], condition= condition, duration=the_duration, data = 
            {"x_step": values[0], "x_name": values[1], "y_step": values[2], "y_name": values[3], "range": values[4], "offset" : offset}
            )
            effect.apply = SpecialSkillEffects.add_foreach_y
            return effect
        elif effect_type == "DAddXForEachY":
            if len(values) > 5: offset = values[5]
            else: offset = 0
            effect = SkillEffect(values[1], "add", 0, condition= condition, data = 
            {"x_step": values[0], "x_name": values[1], "y_step": values[2], "y_name": values[3], "range": values[4], "offset" : offset}
            )
            effect.early_update = SpecialSkillEffects.d_add_foreach_y
            effect.late_update = SpecialSkillEffects.d_add_foreach_y_cleanup
            return effect
        
        elif effect_type == "SpendX":
            effect = SkillEffect(values[1], "add", 0, condition=condition, data=
                                 {"name" : values[1], "cost" : values[0], "treshold" : values[2]})
            effect.apply = SpecialSkillEffects.spend
            return effect

        elif effect_type == "BasePower":
            return SkillEffect("base", "add", values[0], condition= condition, duration=the_duration)
        
        elif effect_type == "OffenseLevelUp":
            return SkillEffect("ol", "add", values[0], condition=condition, duration=the_duration)
        
        elif effect_type == "DefenseLevelDown":
            return SkillEffect("def_level_mod", "add", -values[0], condition=condition, duration=the_duration)

        elif effect_type == "TypedDamageUp":
            effect = SkillEffect("dynamic", "add", values[0], condition=condition,
                                 data = {"type" : values[0], "amount" : values[1]}
                                 )
            effect.apply = SpecialSkillEffects.typed_damage_up
            effect.remove = SpecialSkillEffects.remove_typed_damage_up
            return effect
               
        elif effect_type == "ICCA":
            effect = SkillEffect("current_damage", "add", 0, condition= condition)
            effect.mid_update = SpecialSkillEffects.ICCA_update
            return effect
        elif effect_type == "ICCALastCoinBonus":
            return SkillEffect("dynamic", 'add', 0, apply_func=SpecialSkillEffects.ICCA_last_coin_boost)
        
        elif effect_type == "DDEDRCoinPowerBonus":
            return SkillEffect("coin_power", 'add', 0, apply_func=SpecialSkillEffects.DDEDR_coin_power_boost)
        
        elif effect_type == "DDEDRLastCoinBouns":
            return SkillEffect("dynamic", 'add', 0, apply_func=SpecialSkillEffects.DDEDR_last_coin_boost)
        
        elif effect_type == "MolarBurst":
            effect = SkillEffect("current_damage", "add", 0, condition=condition, duration=1)
            effect.mid_update = SpecialSkillEffects.Moutis_update
            return effect
        
        elif effect_type == 'DeiciLuReuse':
            effect = SkillEffect('current_damage', 'add', 0)
            effect.apply = SpecialSkillEffects.DeiciLuS1Reuse
            effect.on_skill_end = SpecialSkillEffects.DeiciLuS1End
            return effect

        elif effect_type == "RingRandomStatus":
            effect = SkillEffect("dynamic", "add", 0)
            effect.special_data = [values[0], values[1]]
            effect.apply = SpecialSkillEffects.RingRandomStatus
            return effect
        
        elif effect_type == 'RingSangReuse':
            effect = SkillEffect('current_damage', 'add', 0)
            effect.special_data = 0
            effect.early_update = SpecialSkillEffects.RingSangS2Reuse
            effect.on_skill_end = SpecialSkillEffects.RingSangS2End
            return effect
        
        elif effect_type == "RingSangS3Bonus":
            effect = SkillEffect('dynamic', 'add', 0)
            effect.apply = SpecialSkillEffects.RingSangS3Bonus
            return effect
        
        elif effect_type == "LiuIshS3Bonus":
            effect = SkillEffect('dynamic', 'add', 0)
            effect.early_update = SpecialSkillEffects.LiuIshS3Bonus
            effect.late_update = SpecialSkillEffects.LiuIshS3BonusCleanup
            return effect
        
        elif effect_type == 'LiuIshPassive':
            return sk.new("DAddXForEachY", (0.1, "dynamic", 3, "enemy.statuses.Burn.count", (0,0.3), 0))
        
        elif effect_type == 'LiuIshS2Burn':
            effect = SkillEffect('dynamic', 'add', 0)
            effect.apply = SpecialSkillEffects.LiuIshS2Burn
            return effect
        
        elif effect_type == 'CinqClairS3Conversion':
            effect = SkillEffect('dynamic', 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.CinqClairS3Conversion
            return effect

        elif effect_type == "CinqClairS3CritBonus":
            effect = SkillEffect('dynamic', 'add', 0, condition=condition, duration=1)
            effect.mid_update = SpecialSkillEffects.CinqClairS3CritBonusMidUpdate
            return effect
        elif effect_type == "ShankDamageBonus":
            effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.apply_nothing_wduration, remove_func=SpecialSkillEffects.remove_nothing)
            effect.mid_update = SpecialSkillEffects.ShankDamageBonusMidUpdate
            effect.megalate_update = SpecialSkillEffects.ShankDamageBonusLateUpdate
            return effect

        elif effect_type == "ApplyBM":
            return SkillEffect('enemy.BM', 'add', values[0], apply_func=SpecialSkillEffects.ApplyBM, condition=condition)
        
        elif effect_type == "MaidRyoPassive":
            effect = SkillEffect('dynamic', 'add', 0)
            effect.mid_update = SpecialSkillEffects.MaidRyoPassiveMidUpdate
            effect.late_update = SpecialSkillEffects.MaidRyoPassiveLateUpdate
            effect.megalate_update = SpecialSkillEffects.MaidRyoPassiveMegalateUpdate
            return effect
        
        elif effect_type == "MCFaustS2ChargeGain":
            effect = SkillEffect('unit.charge', 'add', 0)
            effect.apply = SpecialSkillEffects.MCFaustS2ChargeGain
            return effect
        
        elif effect_type == "MCFaustS3ChargeGain":
            effect = SkillEffect('unit.charge', 'add', 0)
            effect.apply = SpecialSkillEffects.MCFaustS3ChargeGain
            return effect

        elif effect_type == "MCFaustS2DamageBonus":
            effect = SkillEffect('dynamic', 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.MCFaustS2DamageBonus
            return effect
        
        elif effect_type == "MCFaustS3DamageBonus":
            effect = SkillEffect('dynamic', 'add', 0)
            effect.apply = SpecialSkillEffects.MCFaustS3DamageBonus
            return effect

        elif effect_type == "MCFaustPassive":
            effect = SkillEffect('dynamic', 'add', 0)
            effect.special_data = values[0]
            effect.mid_update = SpecialSkillEffects.MCFaustPassiveMidUpdate
            effect.megalate_update = SpecialSkillEffects.MCFaustPassiveMegalateUpdate
            return effect
        
        elif effect_type == "Photoelectricity":
            effect = SkillEffect('unit.charge', 'add', values[0], condition=condition)
            effect.apply = SpecialSkillEffects.apply_nothing_wduration
            effect.late_update = SpecialSkillEffects.PhotoelectricityLateUpdate
            effect.on_skill_end = SpecialSkillEffects.PhotoelectricityOnSkillEnd
            return effect
        
        elif effect_type == "ButlerOutisS3Bonus":
            return SkillEffect('current_damage', 'add', 0, condition=condition, apply_func=SpecialSkillEffects.ButlerOutisS3Bonus)
        
        elif effect_type == 'ButlerOutisPassive':
            return SkillEffect('dynamic', 'add', values[0], apply_func=SpecialSkillEffects.ButlerOutisPassive)
        
        elif effect_type == 'WarpOutisPassive':
            effect = SkillEffect('dynamic', 'add', 0)
            effect.mid_update = SpecialSkillEffects.WarpOutisPassiveMidUpdate
            return effect
        
        elif effect_type == 'WarpOutisChargeBarrier':
            effect = SkillEffect('dynamic', 'add', 0, apply_func=SpecialSkillEffects.WarpOutisChargeBarrier)
            return effect
        
        elif effect_type == 'WarpOutisCoinpowerS3':
            effect = SkillEffect('coin_power', 'add', 0)
            effect.apply = SpecialSkillEffects.WarpOutisCoinpowerS3
            return effect
        
        elif effect_type == 'WarpOutisChargeGainS3':
            effect = SkillEffect('unit.charge', 'add', 0)
            effect.apply = SpecialSkillEffects.WarpOutisChargeGainS3
            return effect

        elif effect_type == "MidDonResonanceBonus":
            effect = SkillEffect('ol', 'add', 0)
            effect.apply = SpecialSkillEffects.MidDonResonanceBonus
            return effect
        
        elif effect_type == 'MidDonPassive':
            effect = SkillEffect('coin_power', 'add', 0)
            effect.apply = SpecialSkillEffects.MidDonPassive
            return effect
        
        elif effect_type == "ResetAttackWeight":
            effect = SkillEffect('unit.atk_weight', 'add', 0, condition=condition)
            effect.apply = SpecialSkillEffects.ResetAttackWeight
            return effect
        
        elif effect_type == "RegretBurst":
            effect = SkillEffect("current_damage", 'add', 0)
            effect.apply = SpecialSkillEffects.RegretBurst
            return effect

        else: 
            return None
        
    def copy(self):
        return SkillEffect(self.name, self.operation, self.value, self.duration, self.condition,
                           self.apply, self.remove, self.special_data)    

    def __init__(self, name : str, operation : str, value : float, duration : int = -1, condition : 'AnySkillConditional' = -1, 
                 apply_func : Callable|None = None, remove_func : Callable|None = None, data : Any = None) -> None:
        self.name = name
        self.operation = operation
        self.value = value
        self.duration = duration
        self.condition : int|SkillConditional = condition
        self.special_data = data

        self.early_update = None
        self.mid_update = None
        self.late_update = None
        self.megalate_update = None
        self.on_poise_gained = None
        self.on_status_applied = None
        self.on_tremor_burst = None

        if not (apply_func is None): self.apply = apply_func
        else: self.apply = SpecialSkillEffects.apply

        if not (remove_func is None): self.remove = remove_func
        else: self.remove = SpecialSkillEffects.remove

        self.on_skill_end = SkillEffect.on_skill_end
    
    @staticmethod
    def apply(self : 'SkillEffect', env : Environment):
        pass
    @staticmethod
    def early_update(self : 'SkillEffect', env: Environment):
        pass
    @staticmethod
    def mid_update(self : 'SkillEffect' , env: Environment):
        pass
    @staticmethod
    def late_update(self : 'SkillEffect', env: Environment):
        pass
    @staticmethod
    def remove(self : 'SkillEffect', env: Environment):
        pass
    @staticmethod
    def on_skill_end(self : 'SkillEffect', env : Environment):
        pass   
    @staticmethod
    def megalate_update(self : 'SkillEffect', env : Environment):
        pass
    @staticmethod
    def on_poise_gained(self : 'SkillEffect', env : Environment, poise_potency : int, poise_count : int):
        pass
    @staticmethod
    def on_status_applied(self : 'SkillEffect', env : Environment, status_name : str, potency : int, count : int):
        pass
    @staticmethod
    def on_tremor_burst(self : 'SkillEffect', env : Environment):
        pass

class SpecialSkillEffects: 

    def on_hit_trigger(self : SkillEffect, env : Environment):
        effect_to_trigger : SkillEffect = self.special_data
        env.apply_queue.append(effect_to_trigger)
        #if env.debug_mode: print(f'OnHit applying {effect_to_trigger.apply.__name__}')

    def on_heads_hit_trigger(self : SkillEffect, env : Environment):
        effect_to_trigger : SkillEffect = self.special_data
        if env.sequence[env.current_coin_index] == "Heads":
            env.apply_queue.append(effect_to_trigger)
    
    def on_tails_hit_trigger(self : SkillEffect, env : Environment):
        effect_to_trigger : SkillEffect = self.special_data
        if env.sequence[env.current_coin_index] == "Tails":
            env.apply_queue.append(effect_to_trigger)
        
    def on_crit_trigger(self : SkillEffect, env : Environment):
        effect_to_trigger : SkillEffect = self.special_data
        if env.did_crit:
            env.apply_queue.append(effect_to_trigger)

    def apply(self : SkillEffect, env : Environment):
        name = self.name
        val = self.value
        op = self.operation
        time = self.duration
        

        if op == "add":
            env.add(name, val)
            env.effects[self] = [val, time]
    
    def apply_nothing_wduration(self : SkillEffect, env : Environment):
        env.effects[self] = [0, self.duration]
    
    def apply_reuse(self : SkillEffect, env : Environment):
        if self.special_data == 0:
            env.effects[self] = [len(env.skill.coins), -1]
        else:
            env.effects[self] = [0, -1]
    
    
    def on_reuse_end(self : SkillEffect, env : Environment):
        inital_coin_count = env.effects[self][0]
        if not inital_coin_count: return
        env.skill.coins = env.skill.coins[:inital_coin_count]
        self.special_data = 0
    
    def reuse_coin_late_update(self : SkillEffect, env : Environment):
        max_reuse_count = self.value
        current_reuse_count = self.special_data
        if current_reuse_count < max_reuse_count:
            self.special_data += 1
            new_coin = env.skill.copy_coin(env.current_coin_index)
            env.skill.coins.append(new_coin)
    
    def reuse_coin_cond_late_update(self : SkillEffect, env : Environment):
        max_reuse_count : int = self.value[0]
        eval_func : Callable[[SkillEffect, Environment], bool] = self.value[1]
        if not eval_func(self, env): return
        current_reuse_count = self.special_data
        if current_reuse_count < max_reuse_count:
            self.special_data += 1
            new_coin = env.skill.copy_coin(env.current_coin_index)
            env.skill.coins.append(new_coin)
    
    def peq_sang_reuse_coin_late_update(self : SkillEffect, env : Environment):
        if not env.did_crit: return
        max_reuse_count = self.value
        current_reuse_count = self.special_data
        if current_reuse_count < max_reuse_count:
            self.special_data += 1
            new_coin = env.skill.copy_coin(env.current_coin_index)
            env.skill.coins.append(new_coin)

    def apply_fanatic(self : SkillEffect, env : Environment):
        if hasattr(env.unit, 'fanatic'):
            env.unit.fanatic += self.value
        else:
            env.unit.fanatic += self.value
        
        env.effects[self] = [self.value, self.duration]

    def remove_nothing(self : SkillEffect, env : Environment):
        pass
    
    def add_frag_to_env(self : SkillEffect, env : Environment):
        env.effects[self] = [self.value, -1]

    def apply_fragile(self : SkillEffect, env : Environment):
        if env.effects[self][1] != -2: return
        condition_state = env.skill.condition_state
        if self.condition >= 0:
            if self.condition < len(condition_state):
                if condition_state[self.condition]:
                    env.dynamic += self.value
        else:
            env.dynamic += self.value

    def FestiveFeverEarlyUpdate(self : SkillEffect, env : Environment):
        fever : StatusEffect = self.special_data
        self.value = fever.count
        if self.value <= 0: env.effects[self][0] = 0; return
        dynamic_bonus : float = clamp(0.015 * fever.count, 0, 0.15)
        if SkillTagNames.does_bloodfeast in env.skill.tags:
            dynamic_bonus *= 2
        env.effects[self][0] = dynamic_bonus
        env.dynamic += dynamic_bonus

    def FragileEarlyUpdate(self : SkillEffect, env : Environment):
        fragile : StatusEffect = self.special_data
        self.value = fragile.count
        if self.value <= 0: env.effects[self][0] = 0; return
        dynamic_bonus : float = clamp(0.1 * fragile.count, 0, 1)
        env.effects[self][0] = dynamic_bonus
        env.dynamic += dynamic_bonus
    
    def FragileCleanup(self : SkillEffect, env : Environment):
        dynamic_bonus : float = env.effects[self][0]
        env.effects[self][0] = 0
        env.dynamic -= dynamic_bonus
    
    def FanaticEarlyUpdate(self : SkillEffect, env : Environment):
        fanatic : StatusEffect = self.special_data
        self.value = fanatic.count
        if self.value <= 0: env.effects[self][0] = 0; return
        base_bonus : int = fanatic.count if env.enemy.has_status('Nails') else 0
        env.effects[self][0] = base_bonus
        env.current_power += base_bonus
    
    def FanaticCleanup(self : SkillEffect, env : Environment):
        base_bonus : int = env.effects[self][0]
        env.effects[self][0] = 0
        env.current_power -= base_bonus

    def apply_status(self : SkillEffect, env : Environment):
        pot, count, = self.special_data[0], self.special_data[1]
        status_type = self.name

        env.enemy.apply_status(status_type, pot, count)
        env.on_status_applied(status_type, pot, count)
        env.effects[self] = [0, -1]
    
    def apply_status_next_turn(self : SkillEffect, env : Environment):
        pot, count, = self.special_data[0], self.special_data[1]
        status_type = self.name
        env.enemy.apply_status_next_turn(status_type, pot, count)
        env.on_status_applied(status_type, pot, count)

        env.effects[self] = [0, -1]

    def apply_additional_status(self : SkillEffect, env : Environment, status_type : str, potency : int, count : int):
        if status_type == self.name:
            env.enemy.apply_status(status_type, self.value[0], self.value[1])
        env.effects[self] = [0, -1]

    def counter_basepower_gain(self : SkillEffect, env : Environment):
        ol_difference : int = env.ol - env.enemy.def_level
        if ol_difference <= 0:
            env.effects[self] = [0, -1]
            return
        base_power_bonus : int = ol_difference // 3
        env.base += base_power_bonus
        env.effects[self] = [base_power_bonus, -1]
    
    def gain_status(self : SkillEffect, env : Environment):
        pot, count, = self.special_data[0], self.special_data[1]
        status_type = self.name
        env.unit.apply_status(status_type, pot, count)
        env.effects[self] = [0, -1]
    
    def gain_status_next_turn(self : SkillEffect, env : Environment):
        pot, count, = self.special_data[0], self.special_data[1]
        status_type = self.name
        env.unit.apply_status_next_turn(status_type, pot, count)
        env.effects[self] = [0, -1]

    def remove(self : SkillEffect, env: Environment):
        name = self.name
        op = self.operation


        if op == "add":
            offset = env.effects[self][0]
            env.add(name, -offset)
    
    def gain_charge(self : SkillEffect, env : Environment):
        charge_count = self.value
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0

        env.unit.charge += charge_count
        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        if env.unit.charge < 0: env.unit.charge = 0
        if env.unit.charge > 20: env.unit.charge = 20
        env.effects[self] = [charge_count, -1]
    
    def consume_charge(self : SkillEffect, env : Environment):
        count : int = self.value
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        
        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1
        if env.unit.charge >= count:
            env.unit.charge -= count
            env.unit.charge_consumed += count
        
            env.effects[self] = [count, -1]
        else:
            env.effects[self] = [0, -1]
    
    def consume_charge_to_trigger_effect(self : SkillEffect, env : Environment):
        count : int = self.value
        effect_to_trigger : SkillEffect = self.special_data
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        
        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1
        if env.unit.charge >= count:
            env.unit.charge -= count
            env.unit.charge_consumed += count
            env.apply_queue.append(effect_to_trigger)
            env.effects[self] = [count, -1]
        else:
            env.effects[self] = [0, -1]

    #ressource
    def consume_ressource_to_trigger_effect(self : SkillEffect, env : Environment):
        ressource_name : str = self.name
        count : int|float = self.value
        effect_to_trigger : SkillEffect 
        treshold : int|float
        treshold, effect_to_trigger = self.special_data
        
        ressource_count : int|float = env.get(ressource_name)
        if ressource_count >= treshold:
            env.add(ressource_name, -count)
            env.apply_queue.append(effect_to_trigger)
            env.effects[self] = [count, -1]
        else:
            env.effects[self] = [0, -1]

    def gain_poise(self : SkillEffect, env : Environment):
        pot, count = self.special_data[0], self.special_data[1]
        env.unit.add_poise(pot, count)
        env.on_poise_gained(pot, count)
        env.effects[self] = [0, -1]

    def gain_poise_next_turn(self : SkillEffect, env : Environment):
        pot, count = self.special_data[0], self.special_data[1]
        env.unit.add_poise_next_turn(pot, count)
        env.on_poise_gained(pot, count)
        env.effects[self] = [0, -1]

    def gain_additional_poise(self : SkillEffect, env : Environment, p, c):
        pot, count = self.special_data[0], self.special_data[1]
        env.unit.add_poise(pot, count)
        env.effects[self] = [0, -1]
    
    def set_poise(self : SkillEffect, env : Environment):
        pot, count = self.special_data[0], self.special_data[1]
        env.unit.set_poise(pot, count)
        env.effects[self] = [0, -1]
    
    def CriticalDamageBonusUpdate(self : SkillEffect, env : Environment):
        if env.did_crit:
            env.dynamic += self.value
            env.effects[self][0] = self.value
        else:
            env.effects[self][0] = 0
    
    def CriticalDamageBonusCleanup(self : SkillEffect, env : Environment):
        env.dynamic -= env.effects[self][0]
    
    def spend(self : SkillEffect, env: Environment):
        name = self.special_data["name"]
        treshold = self.special_data["treshold"]
        cost = self.special_data["cost"]
        if env.get(name) >= treshold:
            env.add(name, -cost)

    def add_foreach_y(self : SkillEffect, env :Environment):
        name = self.name
        val = self.value
        op = self.operation
        time = self.duration

        data = self.special_data

        y_name : str|Callable[[SkillEffect, Environment], float|int] = data['y_name']
        y_result = env.get(y_name) if type(y_name) == str else y_name(self, env)
        x_name : str|Callable[[SkillEffect, Environment, float|int], None] = data['x_name']
        offset : float|int = data['offset']

        increment_count = (y_result - offset) // data["y_step"]

        total = increment_count * data["x_step"]

        my_min, my_max = data["range"]
        if total < my_min: total = my_min
        if total > my_max: total = my_max
        if op == "add" or True:
            env.add(x_name, total) if type(x_name) == str else x_name(self, env, total)
            env.effects[self] = [total, time]

    def d_add_foreach_y(self : SkillEffect, env : Environment):
        name = self.name
        val = self.value
        op = self.operation
        time = self.duration

        data = self.special_data

        y_name : str|Callable[[SkillEffect, Environment], float|int] = data['y_name']
        y_result = env.get(y_name) if type(y_name) == str else y_name(self, env)
        x_name : str|Callable[[SkillEffect, Environment, float|int], None] = data['x_name']
        offset : float|int = data['offset']

        increment_count = (y_result - offset) // data["y_step"]

        total = increment_count * data["x_step"]

        my_min, my_max = data["range"]
        if total < my_min: total = my_min
        if total > my_max: total = my_max
        if op == "add" or True:
            env.add(x_name, total) if type(x_name) == str else x_name(self, env, total)
            env.effects[self] = [total, time]
        
    def d_add_foreach_y_cleanup(self : SkillEffect, env : Environment):

        name = self.name
        op = self.operation
        if op == "add" or True:
            offset = env.effects[self][0]
            env.add(name, -offset)

    def add_pot_foreach_y(self : SkillEffect, env :Environment):
        time = self.duration
        data = self.special_data

        increment_count : int|float = (env.get(data["y_name"]) - data["offset"]) // data["y_step"]
        total_pot : int = floor(increment_count * data["x_step"])

        my_min, my_max = data["range"]
        total = clamp(total_pot, my_min, my_max)
        status_name : str = data['status_name']

        if data['next_turn']:
            env.enemy.apply_status_next_turn(status_name, total_pot, 0)
        else:
            env.enemy.apply_status(status_name, total_pot, 0)

        env.effects[self] = [total, time]
    
    def add_count_foreach_y(self : SkillEffect, env :Environment):
        time = self.duration
        data = self.special_data

        increment_count : int|float = (env.get(data["y_name"]) - data["offset"]) // data["y_step"]
        total_count : int = floor(increment_count * data["x_step"])

        my_min, my_max = data["range"]
        total : int = clamp(total_count, my_min, my_max)
        status_name : str = data['status_name']
        if data['next_turn']:
            env.enemy.apply_status_next_turn(status_name, 0, total_count)
        else:
            env.enemy.apply_status(status_name, 0, total_count)

        env.effects[self] = [total, time] 

    def gain_count_foreach_y(self : SkillEffect, env :Environment):
        time = self.duration
        data = self.special_data

        increment_count : int|float = (env.get(data["y_name"]) - data["offset"]) // data["y_step"]
        total_count : int = floor(increment_count * data["x_step"])

        my_min, my_max = data["range"]
        total : int = clamp(total_count, my_min, my_max)
        status_name : str = data['status_name']
        if data['next_turn']:
            env.unit.apply_status_next_turn(status_name, 0, total_count)
        else:
            env.unit.apply_status(status_name, 0, total_count)

        env.effects[self] = [total, time] 

    def typed_damage_up(self : SkillEffect, env :Environment):
        dmg_type = self.special_data["type"]
        val = self.special_data["amount"] * 0.1

        if env.skill.type[0] == dmg_type or env.skill.type[1] == dmg_type:
            if self.operation == "add":
                env.add("dynamic", val)
                env.effects[self] = [val, self.duration]

    def remove_typed_damage_up(self: SkillEffect, env: Environment):
        dmg_type = self.special_data["type"]

        if env.skill.type[0] == dmg_type or env.skill.type[1] == dmg_type:
            if self.operation == "add":
                offset = env.effects[self][0]
                env.add("dynamic", -offset)
    
    def heal_sp(self : SkillEffect, env : Environment):
        env.unit.sp += self.value
        if env.unit.sp > 45: env.unit.sp = 45
        if env.unit.sp <= -45: env.unit.sp = -45; env.unit.corroded = True
        env.effects[self] = [self.value, self.duration]
    
    def lose_sp(self : SkillEffect, env : Environment):
        env.unit.sp -= self.value
        if env.unit.sp > 45: env.unit.sp = 45
        if env.unit.sp <= -45: env.unit.sp = -45; env.unit.corroded = True
        env.effects[self] = [self.value, self.duration]
    
    def set_global_state(self : SkillEffect, env : Environment):
        env.global_state[self.name] = self.value
        env.effects[self] = [0, -1]

    def ChargePotencyConversionPassive(self : SkillEffect, env : Environment):
        target_pot : int = env.unit.charge_consumed // self.value
        env.unit.charge_potency = 1 + target_pot
        
    def ICCA_update(self : SkillEffect, env: Environment):
        missing_hp = env.enemy.max_hp - env.enemy.hp
        base = missing_hp // 20
        if base < 0: base = 0
        if base > 20: base = 20

        ol_mult = (env.ol - env.enemy.def_level) / (abs(env.ol - env.enemy.def_level ) + 25)


        p_res = env.enemy.phys_res["Slash"] - 1
        s_res = env.enemy.sin_res["Lust"] - 1
        if s_res < 0: s_res/= 2
        if p_res < 0: p_res/= 2


        mult = 1 + s_res + p_res + (ol_mult)
        if mult < 1: mult = 1

        bonus = base * mult
        if bonus < 1: bonus = 1
        env.current_damage += floor(bonus)

        if env.debug_mode:
            print(f"{base} chunks --> {bonus}(floored) (ol_mult = {ol_mult}; final_mult = {mult}; sin_res = {s_res}; phys_res = {p_res})")
            print(f"{env.ol} offense vs {env.enemy.def_level} defense")
    
    def ICCA_last_coin_boost(self : SkillEffect, env : Environment):
        bonus = 0
        if env.sequence[0] == 'Heads':
            bonus += 0.10
        if env.sequence[1] == 'Heads':
            bonus += 0.05
        if env.sequence[2] == 'Heads':
            bonus += 0.05
        env.add('dynamic', bonus)
        env.effects[self] = [bonus, -1]

    def DDEDR_last_coin_boost(self : SkillEffect, env : Environment):
            bonus = 0
            if env.sequence[0] == 'Heads':
                bonus += 0.10
            if env.sequence[1] == 'Heads':
                bonus += 0.10
            if env.sequence[2] == 'Heads':
                bonus += 0.10
            env.add('dynamic', bonus)
            env.effects[self] = [bonus, -1]

    def DDEDR_coin_power_boost(self : SkillEffect, env : Environment):
        wshu = env.unit
        if not hasattr(wshu, 'charge'): wshu.charge = 0
        if wshu.charge < 7:
            env.effects[self] = [0, -1]
            return
        if wshu.charge >= 15: wshu.charge -=15
        else: wshu.charge = 0
        env.add('coin_power', 5)
        env.effects[self] = [5, -1]

    def Moutis_update(self : SkillEffect, env : Environment):
        if hasattr(env.enemy, "tremor"):
            enemy_tremor = env.enemy.tremor
        else:
            enemy_tremor = 0
        if getattr(env.unit, "molar_passive", False):
            bonus = floor(enemy_tremor * 0.3)
            if bonus > 20: bonus = 20

            bonus = floor(bonus * env.enemy.sin_res["Sloth"])
            env.current_damage += bonus
            if env.debug_mode:
                print(f'enemy has {enemy_tremor} tremor: molar outis dealing {bonus} bonus sloth damage')

        if getattr(env.enemy, "reverb", False):
            bonus = enemy_tremor
            bonus = floor(bonus * env.enemy.sin_res["Sloth"])
            env.current_damage += bonus
            if env.debug_mode:
                print(f'enemy has {enemy_tremor} tremor reverb: dealing {bonus} bonus sloth damage')

    def DeiciLuS1Reuse(self : SkillEffect, env : Environment):
        insight = env.unit.__getattribute__('insight') or 1
        env.skill.coins = [[] for _ in range(insight)]

    def DeiciLuS1End(self : SkillEffect, env : Environment):
        env.skill.coins = [[]]

    def RingRandomStatus(self : SkillEffect, env : Environment):
        pot, count = self.special_data[0], self.special_data[1]
        status_name = ['Burn', 'Bleed', 'Tremor', 'Sinking', 'Rupture'][randint(0, 4)]
        env.enemy.apply_status(status_name, pot, count)
        #env.apply_queue.append(skc.ApplyStatus(status_name, pot, count))#implement bonus later
        env.effects[self] = [0, -1]

    def RingSangS2Reuse(self : SkillEffect, env : Environment):
        if self.special_data >= 2: return
        status_effect_count : int = 0
        for status_effect_name in env.enemy.statuses:
            real_status = env.enemy.statuses[status_effect_name]
            if real_status.is_active():
                status_effect_count += 1
                if status_effect_count >= 3: break
        
        reuse_odds : float = 0.4 + status_effect_count * 0.2

        if random() <= reuse_odds:
            env.skill.coins.append(env.skill.copy_coin(0))
            self.special_data += 1
        
    def RingSangS2End(self : SkillEffect, env : Environment):
        env.skill.coins = [env.skill.coins[0]]
        self.special_data = 0
    
    def RingSangS3Bonus(self : SkillEffect, env : Environment):
        status_effect_count : int = 0
        for status_effect_name in env.enemy.statuses:
            real_status = env.enemy.statuses[status_effect_name]
            if real_status.is_active():
                status_effect_count += 1
                if status_effect_count >= 5: break

        bonus : float = status_effect_count * 0.25
        if bonus > 1.25: bonus = 1.25

        env.add("dynamic", bonus)
        env.effects[self] = [bonus, -1]

    def LiuIshS3Bonus(self : SkillEffect, env : Environment):
        name = self.name
        val = self.value
        op = self.operation
        time = self.duration
        burn_status : StatusEffect|None = env.enemy.statuses.get('Burn', None)
        if not burn_status:
            total = 0
        else:
            total = 0.5 if (burn_status.potency >= 6 and burn_status.count >= 6) else 0
        if op == "add" or True:
            env.add('dynamic', total)
            env.effects[self] = [total, time]
    
    def LiuIshS3BonusCleanup(self : SkillEffect, env : Environment):
        name = self.name
        op = self.operation
        offset = env.effects[self][0]
        env.add(name, -offset)

    def LiuIshS2Burn(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        burn_status : StatusEffect = env.enemy.statuses.get('Burn', None)
        if not burn_status: return
        if burn_status.potency > 6: env.enemy.apply_status('Burn', 0, 2)

    def CinqClairS3Conversion(self : SkillEffect, env : Environment):
        if env.unit.poise['Count'] >= 10:
            env.unit.consume_poise(10)
            if getattr(env.enemy, 'sinclair_duel', False):
                env.unit.add_poise(20, 0)
            else:
                env.unit.add_poise(10, 0)
        env.effects[self] = [0, self.duration]
    
    def CinqClairS3CritBonusMidUpdate(self : SkillEffect, env : Environment):
        if env.did_crit:
            env.dynamic += 0.5
    
    def ShankDamageBonusMidUpdate(self : SkillEffect, env : Environment):
        if env.sequence[env.current_coin_index] == "Heads":
            bonus = 0.5
            if env.current_coin_index == 3:
                bonus += 0.5
        else:
            bonus = 0.0
        env.dynamic += bonus
        env.effects[self][0] = bonus
        
    def ShankDamageBonusLateUpdate(self : SkillEffect, env : Environment):
        offset = env.effects[self][0]
        env.dynamic -= offset

    def MaidRyoPassiveMidUpdate(self : SkillEffect, env : Environment):
        bm_status : StatusEffect|None = env.enemy.statuses.get('BM', None)
        if not hasattr(env.unit, 'speed'): env.unit.speed = 0
        if bm_status is None:
            bonus = 0
        elif not bm_status.is_active():
            bonus = 0
        elif env.did_crit:
            bonus = env.unit.speed * 0.1
            if bonus > 0.6 : bonus = 0.6
            if bonus < 0 : bonus = 0
        else:
            bonus = 0
        env.effects[self][0] = bonus
        env.dynamic += bonus
    
    def MaidRyoPassiveLateUpdate(self : SkillEffect, env : Environment):
        bm_status : StatusEffect|None = env.enemy.statuses.get('BM', None)
        if not bm_status: return
        if not bm_status.is_active(): return
        env.unit.add_poise(0, 1)
        env.unit.apply_status_next_turn('Haste', 0, 1)
        if env.did_crit:
            bm_status.count = 0
            bm_status.potency = 0

    def MaidRyoPassiveMegalateUpdate(self : SkillEffect, env : Environment):
        env.dynamic -= env.effects[self][0]
        env.effects[self][0] = 0

    def ApplyBM(self : SkillEffect, env : Environment):
        if hasattr(env.enemy, 'BM'):
            env.enemy.BM += self.value
        else:
            env.enemy.BM = self.value
        
        env.effects[self] = [self.value, self.duration]

    def MCFaustS2ChargeGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0

        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        if 5 <= env.unit.charge <= 9:
            charge_offset = 10 - env.unit.charge
            env.unit.charge = 10
        else:
            charge_offset = 0

        if env.unit.charge < 0: env.unit.charge = 0
        if env.unit.charge > 20: env.unit.charge = 20
        env.effects[self] = [charge_offset, -1]
    
    def MCFaustS3ChargeGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0

        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        charge_offset : int = env.unit.charge_potency + 5
        if charge_offset > 8: charge_offset = 8

        env.unit.charge += charge_offset
        
        if env.unit.charge < 0: env.unit.charge = 0
        if env.unit.charge > 20: env.unit.charge = 20

        env.effects[self] = [charge_offset, -1]

    def MCFaustS2DamageBonus(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        charge_count_consumed : int = env.unit.charge
        env.unit.charge_consumed += charge_count_consumed
        
        charge_count_consumed += 10 if env.coin_power >= 6 else 0
        charge_potency : int = env.unit.charge_potency
        dmg_bonus : float = ((charge_potency + 4) * charge_count_consumed) * 0.01
        if dmg_bonus > 1.80 : dmg_bonus = 1.80
        env.dynamic += dmg_bonus
        env.effects[self] = [dmg_bonus, -1]
        env.unit.charge = 0
    
    def MCFaustS3DamageBonus(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        bonus : float
        if env.unit.charge_potency >= 3:
            bonus = env.unit.charge_potency * 0.08
            if bonus > 0.4 : bonus = 0.4
            if bonus < 0 : bonus = 0.0
        else:
            bonus = 0.0

        env.dynamic += bonus
        env.effects[self] = [bonus, -1]
    
    def MCFaustPassiveMidUpdate(self : SkillEffect, env : Environment):
        target_pot : int = env.unit.charge_consumed // 10
        env.unit.charge_potency = 1 + target_pot
        if env.unit.charge_potency >= 2:
            if self.special_data:
                bonus = env.unit.charge_potency * 0.05
                if bonus > 0.25: bonus = 0.25
            else:
                bonus = env.unit.charge_potency * 0.03
                if bonus > 0.15: bonus = 0.15
        else:
            bonus = 0.0
        env.effects[self][0] = bonus
        env.dynamic += bonus

    def MCFaustPassiveMegalateUpdate(self : SkillEffect, env : Environment):
        env.dynamic -= env.effects[self][0]
        env.effects[self][0] = 0
    
    def PhotoelectricityLateUpdate(self : SkillEffect, env : Environment):
        if self.special_data: return
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0

        charge_count : int = self.value
        if env.unit.charge <= 5:
            charge_count += 3

        env.unit.charge += charge_count
        self.special_data = True

    def PhotoelectricityOnSkillEnd(self : SkillEffect, env : Environment):
        self.special_data = False

    def EchoesOnStatusApplied(self : SkillEffect, env : Environment, status_name : str, potency : int, count : int):
        if status_name != StatusNames.sinking: return
        if random() < 0.5:
            env.enemy.apply_status(StatusNames.sinking, 0, 1)

    def ButlerOutisS3Bonus(self : SkillEffect, env : Environment):
        if not env.enemy.has_status(StatusNames.echoes_of_the_manor):
            env.effects[self] = [0, -1]
            return
        sinking : StatusEffect|None = env.enemy.statuses.get('Sinking', None)
        if not sinking:
            env.effects[self] = [0, -1]
            return
        if not sinking.is_active():
            env.effects[self] = [0, -1]
            return
        
        bonus_damage = sinking.potency
        if bonus_damage > 30: bonus_damage = 30
        if bonus_damage < 0 : bonus_damage = 0
        env.current_damage += bonus_damage
        env.effects[self] = [bonus_damage, -1]

    def ButlerOutisPassive(self : SkillEffect, env : Environment):
        if not hasattr(env.enemy, 'sp'): env.enemy.sp = 0
        if env.enemy.sp < 0 and self.value : bonus = 0.2
        else: bonus = 0.0
        if env.enemy.has_status(StatusNames.echoes_of_the_manor):
            bonus += 0.3
        
        env.dynamic += bonus
        env.effects[self] = [bonus, -1]
        if self.value: env.unit.apply_status_next_turn(StatusNames.offense_level_up, 0, 3)
    
    def WarpOutisPassiveMidUpdate(self : SkillEffect, env : Environment):
        target_pot : int = env.unit.charge_consumed // 10
        env.unit.charge_potency = 1 + target_pot
    
    def WarpOutisChargeBarrier(self : SkillEffect, env : Environment):
        target_pot : int = getattr(env.unit, 'charge_consumed', 0) // 10
        env.unit.charge_potency = 1 + target_pot
        charge_barrier_count : int = env.unit.charge_potency + 2
        if charge_barrier_count < 0: charge_barrier_count = 0
        if charge_barrier_count > 8: charge_barrier_count = 8
        if not hasattr(env.unit, 'charge_barrier'): env.unit.charge_barrier = 0
        env.unit.charge_barrier += charge_barrier_count
        env.unit.apply_status(StatusNames.charge_barrier, 0, charge_barrier_count)
        env.effects[self] = [0, -1]
    
    def WarpOutisCoinpowerS3(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        
        if env.unit.charge >= 15:
            env.unit.charge -= 15
            env.unit.charge_consumed += 15
            env.coin_power += 2
            env.effects[self] = [2, -1]
        elif env.unit.charge >= 7 and env.unit.charge_potency >= 2:
            consumed_charge = env.unit.charge
            env.unit.charge -= consumed_charge
            env.unit.charge_consumed += consumed_charge
            env.coin_power += 2
            env.effects[self] = [2, -1]
        else:
            env.effects[self] = [0, -1]
    
    def WarpOutisChargeGainS3(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0
        
        charge_bonus : int = 5 - env.unit.charge_potency
        if charge_bonus < 0: charge_bonus = 0
        if charge_bonus > 5: charge_bonus = 5
        env.unit.charge += charge_bonus
        if env.unit.charge > 20: env.unit.charge = 20
    
    def MidDonResonanceBonus(self : SkillEffect, env : Environment):
        abs_res : int|None = getattr(env.unit, 'abs_res', None)
        abs_res_type : str|None = getattr(env.unit, 'abs_res_type', None)
        is_focused_encounter : bool = getattr(env.unit, 'is_focused_encounter', True)
        if (not abs_res) or (not abs_res_type):
            env.effects[self] = [0, -1]
            return
        ol_bonus : int = abs_res // 2
        if ol_bonus > 6: ol_bonus = 6
        if abs_res_type == 'Envy': ol_bonus = floor(ol_bonus * 1.5)
        if is_focused_encounter: ol_bonus *= 2
        env.ol += ol_bonus
        env.effects[self] = [ol_bonus, -1]
    
    def MidDonPassive(self : SkillEffect, env : Environment):
        if getattr(env.enemy, 'vengeance_mark', False):
            env.coin_power += 1
            env.effects[self] = [1, -1]
        else:
            env.effects[self] = [0, -1]
    
    def MidMeurPassive(self : SkillEffect, env : Environment):
        if getattr(env.enemy, 'vengeance_mark', False):
            env.base += 1
            env.effects[self] = [1, -1]
        else:
            env.effects[self] = [0, -1]
    
    def ResetAttackWeight(self : SkillEffect, env : Environment):
        env.effects[self] = [self.value, -1]
        env.unit.atk_weight = self.value

    def RegretBurst(self : SkillEffect, env : Environment):
        enemy_tremor : int = getattr(env.enemy, 'tremor', 0)
        if not enemy_tremor: env.effects[self] = [0, -1]; return
        bonus : int = floor(0.3 * enemy_tremor)
        if bonus > 20: bonus = 20
        wrath_dmg : int = bonus * env.enemy.sin_res['Wrath']
        env.current_damage += wrath_dmg
        env.effects[self] = [wrath_dmg, -1]
    
    def LiuDyaS2Burn(self : SkillEffect, env : Environment):
        burn_status : StatusEffect|None = env.enemy.statuses.get("Burn", None)
        if (not burn_status) or (not env.skill.condition_state[0]):
            env.effects[self] = [0, -1]
            return
        if burn_status.count < 6:
            env.effects[self] = [0, -1]
            return
        
        env.enemy.apply_status("Burn", 3, 0)
        env.effects[self] = [3, -1]
    
    def LiuDyaS3Burst(self : SkillEffect, env : Environment):
        if not env.enemy.has_status(StatusNames.burn):
            env.effects[self] = [0, -1]
            return
        burn : StatusEffect = env.enemy.statuses.get('Burn', None)
        
        bonus_damage = burn.potency
        if bonus_damage > 30: bonus_damage = 30
        if bonus_damage <= 0: bonus_damage = 0
        else: burn.consume_count(2)
        final_bonus : int = floor(bonus_damage * env.enemy.sin_res['Wrath'])
        env.current_damage += final_bonus
        env.effects[self] = [final_bonus, -1]
    
    def LiuDyaS3Bonus(self : SkillEffect, env : Environment):
        name = self.name
        val = self.value
        op = self.operation
        time = self.duration
        burn_status : StatusEffect|None = env.enemy.statuses.get('Burn', None)
        if not burn_status:
            total = 0
        else:
            total = 0.3 if (burn_status.potency >= 6 and burn_status.count >= 6) else 0
        if op == "add" or True:
            env.add('dynamic', total)
            env.effects[self] = [total, time]
    
    def LiuDyaS3BonusCleanup(self : SkillEffect, env : Environment):
        offset = env.effects[self][0]
        env.dynamic -= offset

    def LiuDyaPassiveSkillStart(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if self.special_data:
            env.base += 1
            env.dynamic += 0.1
    
    def LiuDyaPassive(self : SkillEffect, env : Environment):
        if not env.enemy.has_status("Burn"):
            total = 0
        else:
            burn_status : StatusEffect = env.enemy.statuses.get("Burn")
            total = 0.1 * (burn_status.potency // 6)
            if total > 0.3: total = 0.3
        env.effects[self][0] = total
        env.dynamic += total
    
    def LiuDyaPassiveCleanup(self : SkillEffect, env : Environment):
        offset = env.effects[self][0]
        env.dynamic -= offset
    
    def HuntCliffS3Sinking(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if env.enemy.ruin:
            env.enemy.apply_status(StatusNames.sinking, 0, 2)
    
    def HuntCliffS4Bonus(self : SkillEffect, env : Environment):
        if not env.enemy.has_status(StatusNames.sinking):
            env.effects[self] = [0, -1]
            return
        
        sinking_status : StatusEffect = env.enemy.statuses.get("Sinking")
        bonus : int = sinking_status.potency
        if bonus > 30 : bonus = 30
        if bonus < 0: bonus = 0
        total : int = floor(bonus * env.enemy.sin_res['Gloom'])
        env.current_damage += total
        env.effects[self] = [total, -1]
    
    def HuntCliffSpBonus(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        sp_difference : int = abs(45 - env.unit.sp)
        bonus : float = sp_difference * 0.003
        if bonus > 0.21: bonus = 0.21
        env.dynamic += bonus
    
    def HuntCliffS4Regen(self : SkillEffect, env : Environment):
        if env.unit.sp >= 0: return
        distance : int = 0 - env.unit.sp
        regen : int = distance * 2
        if regen > 50: regen = 50
        if regen < 0: regen = 0
        env.unit.sp += 10
        env.unit.sp += regen
    
    def MCHeathS3ChargeGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0

        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        charge_offset : int = env.unit.charge_potency * 3
        if charge_offset > 9: charge_offset = 9

        env.unit.charge += charge_offset
        
        if env.unit.charge < 0: env.unit.charge = 0
        if env.unit.charge > 20: env.unit.charge = 20

        env.effects[self] = [charge_offset, -1]
    
    def PirateGregS3Bonus(self : SkillEffect, env : Environment):
        env.unit.ammo = getattr(env.unit, 'ammo', 0) or 7
        env.unit.coins = getattr(env.unit, 'coins', 0)

        this_coin_dmg = env.current_damage
        bonus_mult : float = clamp(0.25 * env.unit.coins, 0.0, 1.0)
        bonus_dmg : int = floor(this_coin_dmg * bonus_mult)
        env.total += bonus_dmg
        env.enemy.hp -= bonus_dmg
        env.unit.ammo -= 1
    
    def PirateGregPassiveMegaLateUpdate(self : SkillEffect, env : Environment):
        curr_coin = env.current_coin_index
        env.unit.coins = getattr(env.unit, 'coins', 0)
        if env.sequence[curr_coin] == "Heads" and env.enemy.has_status('Bleed'):
            env.unit.coins += 1
        env.unit.coins = clamp(env.unit.coins, 0, 4)

    def SwordplayOfTheHomeland(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if env.skill.skill_type == 1 or env.skill.skill_type == 2:
            if env.unit.poise_potency < 5: return

            new_effect = skc.OnCritRoll(skc.DynamicBonus(0.3 / env.skill.coin_amount, duration=1))
            new_effect.duration = -1
            env.apply_queue.append(new_effect)

            coin_power_buff : int = floor(3 / env.skill.coin_amount)
            if coin_power_buff < 1: coin_power_buff = 1
            env.coin_power += coin_power_buff
        else:
            if env.unit.poise_potency < 7: return
            new_effect = skc.DynamicBonus(0.3 / env.skill.coin_amount)
            new_effect.duration = -1
            env.apply_queue.append(new_effect)

            new_effect = skc.OnCritRoll(skc.DynamicBonus(0.5 / env.skill.coin_amount, duration=1))
            new_effect.duration = -1
            env.apply_queue.append(new_effect)

    def RedPlumBlossomEarlyUpdate(self : SkillEffect, env : Environment):
        red_plum : StatusEffect = self.special_data
        self.value = red_plum.count
        if self.value <= 0: env.effects[self][0] = [0,0]; return
        dynamic_bonus : float = clamp(0.03 * red_plum.count, 0, 0.3)
        crit_odd_bonus : float = 0.1
        env.effects[self][0] = [crit_odd_bonus, dynamic_bonus]
        env.crit_odds_bonus += crit_odd_bonus
        env.dynamic += dynamic_bonus

    def RedPlumBlossomLateUpdate(self : SkillEffect, env : Environment):
        pass

    def RedPlumBlossomMegaLateUpdate(self : SkillEffect, env : Environment):
        crit_odd_bonus_offset, dynamic_offset = env.effects[self][0]
        env.crit_odds_bonus -= crit_odd_bonus_offset
        env.dynamic -= dynamic_offset
        env.effects[self][0][0] = 0
        env.effects[self][0][1] = 0

    def BlFaustS3Conversion(self : SkillEffect, env : Environment):
        half_poise_count : int = env.unit.poise_count // 2
        half_poise_count = clamp(half_poise_count, 0, 10)
        env.unit.consume_poise(half_poise_count)
        env.unit.add_poise(half_poise_count, 0)
        env.effects[self] = [half_poise_count, -1]
    
    def BlFaustPassive(self : SkillEffect, env : Environment):
        if env.did_crit:
            if not env.enemy.has_status(StatusNames.red_plum_blossom):
                env.enemy.apply_status(StatusNames.red_plum_blossom, 0, 1)
            elif env.enemy.statuses[StatusNames.red_plum_blossom].count < 10:
                env.enemy.apply_status(StatusNames.red_plum_blossom, 0, 1)
            else:
                env.ol += 1

    def WarpSangS3CoinPower(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'charge'):
            env.unit.charge = 0
        if not hasattr(env.unit, 'charge_potency'):
            env.unit.charge_potency = 0
        if not hasattr(env.unit, 'charge_consumed'):
            env.unit.charge_consumed = 0

        if (env.unit.charge > 0) and (env.unit.charge_potency <= 0): env.unit.charge_potency = 1

        charge_consumed : int
        coin_power_bonus : int

        if env.unit.charge >= 15:
            charge_consumed = 15
            coin_power_bonus = 2
        elif env.unit.charge >= 10:
            charge_consumed = 10
            coin_power_bonus = 1
        else:
            coin_power_bonus = 0
            charge_consumed = 0
        
        env.coin_power += coin_power_bonus

        env.effects[self] = [charge_consumed, -1]
        env.unit.charge -= charge_consumed
        env.unit.charge_consumed += charge_consumed

    def SevenFaustPassive(self : SkillEffect, env : Environment):
        phys_type : str = env.skill.type[0]
        sin_type : str = env.skill.type[1]

        if (env.enemy.phys_res[phys_type] > 1 or env.enemy.sin_res[sin_type] > 1) and env.enemy.has_status("Rupture"):
            rupture_status : StatusEffect = env.enemy.statuses.get('Rupture')
            poise_pot_gain : int = clamp(rupture_status.potency, 0, 20)
            env.unit.add_poise(poise_pot_gain, 0)
            env.effects[self] = [poise_pot_gain, -1]
        else:
            env.effects[self] = [0, -1]

    def RingOutisS2Reuse(self : SkillEffect, env : Environment):
        if self.special_data >= 2: return
        
        reuse_odds : float = 0.4 + env.enemy.get_status_count() * 0.2

        if random() <= reuse_odds:
            env.skill.coins.append(env.skill.copy_coin(1))
            self.special_data += 1
        
        if env.current_coin_index == 2:
            env.apply_queue.append(skc.ApplyAdditionalStatus('Bleed', 0, 1))
        
    def RingOutisS2End(self : SkillEffect, env : Environment):
        env.skill.coins = [env.skill.coins[0], env.skill.coins[1]]
        self.special_data = 0
    
    def RingOutisS3Bonus(self : SkillEffect, env : Environment):
        dynamic_bonus : float = clamp(0.125 * env.enemy.get_status_count(), 0, 0.5)
        env.dynamic += dynamic_bonus
        env.effects[self][0] = dynamic_bonus
    
    def DawnClairS4Bonus(self : SkillEffect, env : Environment):
        wrath_res : int = getattr(env.unit, 'wrath_res', 0)
        if wrath_res:
            dynamic_bonus : float = clamp(wrath_res * 0.1, 0, 0.6)
            if getattr(env.unit, 'is_ares', False) and wrath_res >= 4:
                dynamic_bonus *= 2
            env.dynamic += dynamic_bonus
            env.effects[self] = [dynamic_bonus, -1]
        else:
            env.effects[self] = [0, -1]
    
    def DawnClairCoinPower(self : SkillEffect, env : Environment):
        if not getattr(env.unit, 'ego', 0):
            env.effects[self] = [0, -1]
            return
        
        coin_power_buff : int = clamp(env.unit.sp // 20, 0, 2)
        if env.unit.sp >= 45:
            coin_power_buff += 1

        env.coin_power += coin_power_buff
        env.effects[self] = [coin_power_buff, -1]

    def MBOutisS2BulletGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'bullet'):
            env.unit.bullet = 0
        bullet_gain : int = 1 if env.unit.bullet < 4 else 0
        env.effects[self] = [bullet_gain, -1]
        env.unit.bullet += 1
    
    def MBOutisS3BeforeAttack(self : SkillEffect, env : Environment):
        #Bullet Gain
        if not hasattr(env.unit, 'bullet'):
            env.unit.bullet = 0
        env.effects[self] = [1, -1]
        env.unit.bullet += 1

        bullet_count : int = env.unit.bullet
        env.unit.atk_weight = bullet_count #Atk weight gain
        sp_loss : int = (bullet_count - 1) * 5
        env.unit.sp -= sp_loss #SP Loss
        env.unit.clamp_sp()
        if env.unit.sp <= 10:#Indiscrimate check
            env.unit.random = True if random() < 0.5 else False 
        
        if not env.enemy.has_status("Burn"): return
        env.dynamic += clamp(env.enemy.statuses['Burn'].potency * 0.01, 0, 0.3) #Burn dmg bonus
        #All that is left is dark flame application on the skill 3 and the after attack effects

        if bullet_count <= 3:
            pass
        elif bullet_count <= 6:
            env.base += 2
            env.coin_power += 2
        elif bullet_count >= 7:
            env.base += 15
            env.coin_power += 6
    
    def MBOutisS3AfterAttack(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'bullet'):
            env.unit.bullet = 0
        if env.unit.bullet >= 7:
            env.unit.bullet = 0
        #bullet reset

    def MBOutisPassive(self : SkillEffect, env : Environment):
        env.effects[self] = [0, 1]
        if not env.enemy.has_status("Burn") : return
        burn_status : StatusEffect = env.enemy.statuses['Burn']
        if env.def_level_mod <= -4:
            env.unit.add_poise(clamp(burn_status.potency, 0, 20), 0)

    def BlDonS3Bonus(self : SkillEffect, env : Environment):
        dynamic_bonus : float = 0
        if env.sequence[0] == "Heads": dynamic_bonus += 0.1
        if env.sequence[1] == "Heads": dynamic_bonus += 0.1
        env.dynamic += dynamic_bonus
        env.effects[self] = [dynamic_bonus, -1]

    def MolarIshPassive(self : SkillEffect, env : Environment):
        if env.enemy.has_status("Tremor"):
            env.enemy.apply_status(StatusNames.sinking, 0, 1)

    def LDonS2Rupture(self : SkillEffect, env : Environment):
        count_applied : int
        if not env.enemy.has_status('Rupture'):
            count_applied = 3
        elif env.enemy.statuses['Rupture'].count <= 2:
            count_applied = 3
        else:
            count_applied = 0
            env.effects[self] = [0, -1]
            return
        env.effects[self] = [count_applied, -1]
        env.enemy.apply_status("Rupture", 0, count_applied)
    
    def MolarClairS3Spend(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if not hasattr(env.unit, 'tremor'): return
        if env.unit.tremor >= 10: env.unit.tremor = 0

    def NCliffS3Bonus(self : SkillEffect, env : Environment):
        mult : float = 0.1 if env.sequence[env.current_coin_index] == "Heads" else 0.0
        bonus : int = floor(env.current_damage * mult)
        env.total += bonus
        env.enemy.take_damage(bonus, env)
        env.effects[self] = [bonus, -1]

    def LiuGregorPassive(self : SkillEffect, env : Environment):
        if not (env.current_coin_index >= 2): return
        env.enemy.apply_status('Burn', 1, 0)
    
    def RedEyesGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'red_eyes'): env.unit.red_eyes = 0
        if env.unit.ashes: return
        env.unit.red_eyes += self.value
        if env.unit.passive and env.enemy.has_status('Bleed'): env.unit.red_eyes += 1
        env.unit.red_eyes = clamp(env.unit.red_eyes, 0, 20)
    
    def RedEyesBonus(self : SkillEffect, env : Environment):
        if not env.unit.passive: return
        bonus : float = (env.unit.red_eyes / 2) * 0.01
        if env.unit.speed >= 3: bonus += (env.unit.red_eyes / 2) * 0.01
        env.dynamic += bonus
        env.effects[self][0] = bonus
    
    def RedEyesS2Gain(self : SkillEffect, env : Environment):
        if not env.enemy.has_status('Bleed'): return
        if env.unit.ashes: return
        bleed_potency : int = env.enemy.statuses['Bleed'].potency
        if not hasattr(env.unit, 'red_eyes'): env.unit.red_eyes = 0
        env.unit.red_eyes += clamp(bleed_potency // 2, 0, 3)
        if env.unit.passive and env.enemy.has_status('Bleed'): env.unit.red_eyes += 1
        env.unit.red_eyes = clamp(env.unit.red_eyes, 0, 20)
    
    def PenitenceGain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'penitence'): env.unit.penitence = 0
        gain : int = self.value
        if not env.unit.ashes:
            env.unit.penitence += gain
        else:
            env.unit.sp += gain // 2      
        env.unit.sp += 2
        env.unit.clamp_sp()
        if env.unit.passive and env.unit.sp >= 20: env.unit.penitence += 1
        env.unit.penitence = clamp(env.unit.penitence, 0, 20)
    
    def PenitenceS1Gain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'penitence'): env.unit.penitence = 0
        gain : int = 3
        if env.sequence[env.current_coin_index] == "Heads": gain += 1
        if env.unit.passive and env.unit.sp >= 20: gain += 1
        if not env.unit.ashes:
            env.unit.penitence += gain
        else:
            env.unit.sp += gain // 2
        env.unit.sp += 2
        env.unit.clamp_sp()
        env.unit.penitence = clamp(env.unit.penitence, 0, 20)
    
    def PenitenceS3Gain(self : SkillEffect, env : Environment):
        if not hasattr(env.unit, 'penitence'): env.unit.penitence = 0
        gain : int = 0
        if env.sequence[env.current_coin_index] == "Heads": gain += 2
        if env.unit.passive and env.unit.sp >= 20: gain += 1
        if not env.unit.ashes:
            env.unit.penitence += gain
        else:
            env.unit.sp += gain // 2
        env.unit.sp += 2
        env.unit.clamp_sp()
        env.unit.penitence = clamp(env.unit.penitence, 0, 20)
    
    def PenitenceBonus(self : SkillEffect, env : Environment):
        if not env.unit.passive: return
        bonus : float = (env.unit.penitence / 2) * 0.01
        if env.unit.sp > env.enemy.sp: bonus += (env.unit.penitence / 2) * 0.01
        env.dynamic += bonus
        env.effects[self][0] = bonus
    
    def RedRyoS4PowerGain(self : SkillEffect, env : Environment):
        eyes : int = env.unit.red_eyes
        skull : int = env.unit.penitence
        env.unit.red_eyes = 0
        env.unit.penitence = 0
        env.unit.eyes_consumed = eyes
        env.unit.skull_consumed = skull
        coin_power_boost : int = clamp(eyes // 5, 0, 4)
        base_power_boost : int = clamp(skull // 5, 0, 4)
        env.coin_power += coin_power_boost
        env.base += base_power_boost
        env.effects[self] = [(base_power_boost, coin_power_boost), -1]
    
    def RedRyoS4Bonus(self : SkillEffect, env : Environment):
        the_sum : int = env.unit.eyes_consumed + env.unit.skull_consumed
        bonus : float = clamp(the_sum * 0.04, 0, 1.6)
        env.dynamic += bonus
        env.effects[self] = [bonus, -1]
    
    def RedRyoS4AfterAttack(self : SkillEffect, env : Environment):
        env.unit.sp += clamp(env.unit.skull_consumed - 5, 0, 15)
        env.unit.clamp_sp()
        env.unit.ashes = 2
        env.unit.sp -= 15
        env.unit.clamp_sp()
        del env.unit.eyes_consumed
        del env.unit.skull_consumed
        env.effects[self] = [0, -1]
    
    def RedRyoS4Bleed(self : SkillEffect, env : Environment):
        bleed_applied : int = clamp(env.unit.eyes_consumed - 15, 0, 5)
        env.enemy.apply_status('Bleed', bleed_applied, 0, env)
        env.effects[self] = [bleed_applied, -1]
    
    def RedRyoBonusBleed(self : SkillEffect, env : Environment, status_type : str, potency : int, count : int):
        if not env.unit.red_eyes : return
        if status_type == 'Bleed':
            bonus_bleed : int = clamp((env.unit.red_eyes // 8) + 1, 1, 3)
            env.enemy.apply_status(status_type, bonus_bleed, 0)
    
    def RedRyoBaseSpHeal(self : SkillEffect, env : Environment):
        if not env.unit.penitence: return
        bonus_sp : int = 2 * clamp((env.unit.penitence // 8) + 1, 1, 3)
        env.unit.sp += bonus_sp
        env.unit.clamp_sp()

    def YuroRyoS2Count(self : SkillEffect, env : Environment):
        transfer : int = clamp(env.unit.tremor, 0, 5)
        env.enemy.tremor_count += transfer
        env.unit.tremor -= transfer
        env.effects[self] = [transfer, -1]

    def GCorpGregorS3Bonus(self : SkillEffect, env : Environment):
        mult : float = 0.3 if env.enemy.has_status('Rupture') else 0.0
        bonus : int = floor(env.current_damage * mult)
        env.enemy.take_damage(bonus, env)
        env.total += bonus
        env.effects[self] = [bonus, -1]
    
    def GainCourrierTrunk(self : SkillEffect, env : Environment):
        trunk_gain : int = self.value if not getattr(env.unit, 'fixed_trunk', False) else 0
        env.unit.trunk += trunk_gain
        env.effects[self] = [trunk_gain, -1]
    
    def DevyatRodyaCoinPower(self : SkillEffect, env : Environment):
        rupture_potency : int = env.enemy.statuses['Rupture'].potency if env.enemy.has_status('Rupture') else 0
        trunk : int = env.unit.trunk
        coin_power_bonus : int = clamp((trunk // 10) + (rupture_potency // 6), 0, 2)
        env.coin_power += coin_power_bonus
        env.effects[self] = [coin_power_bonus, -1]
    
    def DVRRuptureCondCheck(self : SkillEffect, env : Environment):
        state : bool
        if not env.enemy.has_status('Rupture'):
            state = False
        elif env.enemy.statuses['Rupture'].potency < 15:
            state = False
        elif env.enemy.statuses['Rupture'].count < 3:
            state = False
        else:
            state = True
        env.global_state['DevyatRuptureCond'] = state
        env.effects[self] = [state, -1]
    
    def FLuRuptureCondCheck(self : SkillEffect, env : Environment):
        state : bool
        if not env.enemy.has_status('Rupture'):
            state = False
        elif env.enemy.statuses['Rupture'].potency < 15:
            state = False
        elif env.enemy.statuses['Rupture'].count < 3:
            state = False
        else:
            state = True
        env.global_state['FangLuRuptureCond'] = state
        env.effects[self] = [state, -1]
        
    def StopRuptureDrain(self : SkillEffect, env : Environment):
        env.CONSUME_RUPTURE = False
        env.effects[self] = [0, -1]

    def GainErudition(self : SkillEffect, env : Environment):
        env.unit.erudition += self.value
        if env.unit.erudition > 6: env.unit.erudition = 6
        env.effects[self] = [self.value, -1]
    
    def DeiciMeurS3Insight(self : SkillEffect, env : Environment):
        env.unit.insight += env.unit.erudition
        env.unit.erudition = 0
        env.effects[self] = [self.value, -1]
    
    def DeiciMeurS3Sinking(self : SkillEffect, env : Environment):
        potency : int = 0
        count : int = 0
        for _ in range(env.unit.insight):
            if randint(1, 2) == 1: potency += 1
            else: count += 1
        env.enemy.apply_status('Sinking', potency, count)
        env.effects[self] = [0, -1]
    
    def DeiciMeurResetInsight(self : SkillEffect, env : Environment):
        if env.unit.insight >= 4:
            if getattr(env.unit, 'did_kill', False):
                env.unit.insight = 3
            else:
                env.unit.insight = 1
        env.effects[self] = [0, -1]
    
    def HeirGregorS3Bonus(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if randint(1, 2) == 2:
            env.unit.apply_status_next_turn(StatusNames.plus_coin_boost, 0, 1)
            env.unit.apply_status_next_turn(StatusNames.damage_up, 0, 3)
            return
        if not env.enemy.has_status('Sinking'): return
        sinking_potency : int = env.enemy.statuses['Sinking'].potency
        if sinking_potency >= 10:
            env.unit.apply_status_next_turn(StatusNames.plus_coin_boost, 0, 1)
            env.unit.apply_status_next_turn(StatusNames.damage_up, 0, 3)
            env.enemy.statuses['Sinking'].potency -= 10
            return

    def ZweiIshS3Bonus(self : SkillEffect, env : Environment):
        current_tremor : int = env.unit.tremor
        env.unit.tremor = 0
        bonus : float
        if current_tremor > 20:
            bonus : float = clamp((current_tremor - 20) * 0.05, 0, 0.5)
            env.dynamic += bonus
        else:
            bonus = 0.0
        env.effects[self] = [bonus, -1]

    def SpicebushS3Bonus(self : SkillEffect, env : Environment):
        mult : float = 0.4 if env.unit.tremor >= 10 else 0.0
        bonus : int = floor(env.current_damage * mult)
        env.enemy.take_damage(bonus, env)
        env.total += bonus
        env.effects[self] = [bonus, -1]
    
    def SpiceBushSinkingDeluge(self : SkillEffect, env : Environment):
        if not env.enemy.has_status('Sinking'): return
        the_sinking : StatusEffect = env.enemy.statuses['Sinking']
        if the_sinking.potency >= 6:
            bonus : int = the_sinking.potency * the_sinking.count
            bonus = floor(bonus * env.enemy.sin_res['Gloom'])
            if not env.ignore_fixed_damage:
                env.total += bonus
                env.enemy.take_damage(bonus, env)
        
        the_sinking.potency = 0
        the_sinking.count = 0
        env.effects[self] = [0, -1]

    def SpicebushS2AOE(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if env.unit.tremor < 6: 
            env.unit.atk_weight = 1
            return
        env.unit.tremor -= 6
        env.unit.atk_weight = 3
        if getattr(env.unit, 'passive', False):
            if env.unit.max_aoe > 1:
                env.dynamic += 0.3

    def StopPoiseDrain(self : SkillEffect, env : Environment):
        env.CONSUME_POISE = False
        env.effects[self] = [0, -1]
    
    def WeaknessAnalyzed(self : SkillEffect, env : Environment):
        chosen_type : str = ['Slash', 'Blunt', 'Pierce'][randint(0, 2)]
        env.enemy.phys_res[chosen_type] += 0.2
        env.effects[self] = [chosen_type, -1]
    
    def WeaknessAnalyzedCleanup(self : SkillEffect, env : Environment):
        chosen_type : str = env.effects[self][0]
        env.enemy.phys_res[chosen_type] -= 0.2
    
    def SevenOutisS3Bonus(self : SkillEffect, env : Environment):
        mult : float = 0.15
        bonus : int = floor(env.current_damage * mult * env.enemy.phys_res['Slash'])
        env.enemy.take_damage(bonus, env)
        env.total += bonus
        env.effects[self] = [bonus, -1]

    def TremorEarlyUpdate(self : SkillEffect, env : Environment):
        tremor : StatusEffect = self.special_data
        self.value = tremor.potency
        if self.value <= 0: env.effects[self][0] = 0; return
        def_mod : int = tremor.potency // 4 if env.enemy.has_tremor_flavor(TremorFlavors.decay) else 0
        env.effects[self][0] = def_mod
        env.def_level_mod -= def_mod
    
    def TremorCleanup(self : SkillEffect, env : Environment):
        def_mod : int = env.effects[self][0]
        env.effects[self][0] = 0
        env.def_level_mod += def_mod

    def TremorDecayConversion(self : SkillEffect, env : Environment):
        current_flavor : None|str|list[str] = getattr(env.enemy, 'tremor_flavor', None)
        if current_flavor is None or type(current_flavor) == str:
            env.enemy.tremor_flavor = TremorFlavors.decay
        elif TremorFlavors.decay not in current_flavor:
            env.enemy.tremor_flavor.append(TremorFlavors.decay)
        env.effects[self] = [0, -1]
    
    def ReverbEntanglement(self : SkillEffect, env : Environment):
        current_flavor : None|str|list[str] = getattr(env.enemy, 'tremor_flavor', None)
        if current_flavor is None or current_flavor == TremorFlavors.reverb:
            env.enemy.tremor_flavor = [TremorFlavors.reverb]
        elif type(current_flavor) == str:
            env.enemy.tremor_flavor = [TremorFlavors.reverb, env.enemy.tremor_flavor]
        elif TremorFlavors.decay not in current_flavor:
            env.enemy.tremor_flavor.append(TremorFlavors.reverb)
        env.effects[self] = [0, -1]
    
    def TremorBurst(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if not env.enemy.has_status('Tremor'): return
        tremor_pot : int = env.enemy.statuses['Tremor'].potency
        env.enemy.raise_stagger_treshold(tremor_pot, env)
        if env.enemy.has_tremor_flavor(TremorFlavors.reverb):
            sloth_damage : int = floor(tremor_pot * env.enemy.sin_res['Sloth'])
            env.enemy.take_damage(sloth_damage, env)
            if not env.ignore_fixed_damage:
                env.total += sloth_damage
        
        env.on_tremor_burst()
        env.enemy.statuses['Tremor'].consume_count(self.value)
        
    

    def ZweiSinclairWestS3Tremor(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if not hasattr(env.unit, 'tremor'): return
        consumed : int = clamp(env.unit.tremor, 0, 8)
        env.unit.tremor -= consumed
    
    def CinqMeurS3HeadsBonus(self : SkillEffect, env : Environment):
        bonus : float = 0.0
        if env.sequence[0] == 'Heads':
            bonus += 0.10
        if env.sequence[1] == 'Heads':
            bonus += 0.10
        env.dynamic += bonus
        env.effects[self] = [bonus, -1]

    def TRodyaS3CoinPower(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if env.unit.tremor >= 8:
            env.global_state['ConsumedTremor'] = 1
            env.coin_power += 1
            env.unit.tremor -= 8
        else:
            env.global_state['ConsumedTremor'] = 0
        
    def TRodyaMoratium(self : SkillEffect, env : Environment):
        if getattr(env.unit, 'borrowed_time', 0):
            env.enemy.moratium = 2
        env.effects[self] = [0, -1]
    
    def TDonMoratium(self : SkillEffect, env : Environment):
        if getattr(env.enemy, 'tremor', 0) >= 5:
            env.enemy.moratium = 2
            if getattr(env.unit, 'borrowed_time', 0):
                env.enemy.tremor += 5
            else:
                env.enemy.tremor -= 5 
        env.effects[self] = [0, -1]
    
    def ButterflySangConsumeAmmo(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        ammo_consumed : int = self.value
        ammo_sum : int = env.unit.the_living + env.unit.the_departed
        if ammo_consumed > ammo_sum:
            env.CANCEL_ATTACK = True
            env.unit.attack_cancel = True
            return
        current_living : int = env.unit.the_living
        current_departed : int = env.unit.the_departed
        living_consumed : int = 0
        departed_consumed : int = 0
        for _ in range(ammo_consumed):
            if (current_living > 0) and (current_departed > 0):
                if randint(1,2) == 1: 
                    living_consumed += 1
                    current_living -= 1
                else: 
                    departed_consumed += 1
                    current_departed -= 1
            elif current_living > 0:
                living_consumed += 1
                current_living -= 1
            else:
                departed_consumed += 1
                current_departed -= 1
        env.global_state['living_consumed'] = living_consumed
        env.global_state['departed_consumed'] = departed_consumed
        env.global_state['ammo_consumed'] = ammo_consumed
        env.global_state['total_consumed'] = ammo_consumed + env.global_state.get('total_consumed', 0)
        env.unit.the_living -= living_consumed
        env.unit.the_departed -= departed_consumed
    
    def ButterflySangS3ConsumeAmmo(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        ammo_sum : int = env.unit.the_living + env.unit.the_departed
        current_living : int = env.unit.the_living
        current_departed : int = env.unit.the_departed
        living_consumed : int = current_living
        departed_consumed : int = current_departed

        env.global_state['living_consumed'] = living_consumed
        env.global_state['departed_consumed'] = departed_consumed
        env.global_state['ammo_consumed'] = ammo_sum
        env.global_state['total_consumed'] = ammo_sum + env.global_state.get('total_consumed', 0)
        env.unit.the_living -= living_consumed
        env.unit.the_departed -= departed_consumed
        dynamic_bonus : float = env.global_state['total_consumed'] * 0.04
        env.apply_queue.append(skc.DynamicBonus(dynamic_bonus, duration=1))
    
    def ButterflySangS3Bonus(self : SkillEffect, env : Environment):
        the_butterfly : StatusEffect = env.enemy.statuses[StatusNames.butterfly]
        base_damage : int = the_butterfly.potency + the_butterfly.count
        total_damage : int = floor(base_damage * env.enemy.sin_res['Gloom'])
        env.enemy.take_damage(total_damage, env)
        env.total += total_damage
    
    def InflictBulletButterfly(self : SkillEffect, env : Environment):
        living : int = env.global_state['living_consumed']
        departed : int = env.global_state['departed_consumed']
        env.enemy.apply_status(StatusNames.butterfly, living, departed)
        env.effects[self] = [0, -1]
    
    def ButterflySangReload(self : SkillEffect, env : Environment):
        env.unit.sp -= (30 - (env.unit.the_living + env.unit.the_departed)) // 2
        departing_weight : float
        if env.unit.sp >= 0:
            departing_weight = 0.7
        else:
            departing_weight = 0.3
        env.unit.the_living = 0
        env.unit.the_departed = 0
        for _ in range(20):
            if random() <= departing_weight:
                env.unit.the_departed += 1
            else:
                env.unit.the_living += 1
        if env.unit.the_departed <= 0:
            env.unit.the_departed = 1
            env.unit.the_living -= 1
        elif env.unit.the_living <= 0:
            env.unit.the_living = 1
            env.unit.the_departed -= 1
        env.effects[self] = [0, -1]
        if env.debug_mode:
            print('Reloading')

    def ButterflyEffect(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
    
    def ButterflyEffectLateUpdate(self : SkillEffect, env : Environment):
        butterfly_status : StatusEffect = self.value
        env.unit.sp += clamp(butterfly_status.potency // 4, 1, 999)
        env.unit.clamp_sp()
        if not env.enemy.has_status('Sinking'): return
        gloom_dmg : int
        sinking_potency : int = env.enemy.statuses['Sinking'].potency
        enemy_sp : int|None = getattr(env.enemy, 'sp', None)
        if enemy_sp is None:
            gloom_dmg = clamp(floor(sinking_potency // 5 * butterfly_status.count) // 2, 0, 30)
        elif enemy_sp < 0:
            gloom_dmg = clamp(floor(sinking_potency // 5 * butterfly_status.count), 0, 30)
        else:
            gloom_dmg = 0
        total_damage : int = floor(gloom_dmg * env.enemy.sin_res['Gloom'])
        env.enemy.take_damage(total_damage, env)
        if not env.ignore_fixed_damage:
            env.total += total_damage

    def TCorpLuPassive(self : SkillEffect, env : Environment):
        self.special_data = 0
        env.effects[self] = [0, -1]
    
    def TCorpLuPassiveOnTremorBurst(self : SkillEffect, env : Environment):
        if self.special_data < 3:
            env.unit.apply_status_next_turn(StatusNames.damage_up, 0, 1)
            self.special_data += 1
    
    def TCorpLuS3CoinPower(self : SkillEffect, env : Environment):
        if env.unit.tremor >= 15:
            env.coin_power += 3
            env.unit.tremor -= 15
            env.global_state['ConsumedTremor'] = 15
        elif env.unit.tremor >= 10:
            env.coin_power += 2
            env.unit.tremor -= 10
            env.global_state['ConsumedTremor'] = 10
        else: env.global_state['ConsumedTremor'] = 0

    def FangLuPassiveMidUpdate(self : SkillEffect, env : Environment):
        dynamic_bonus : float
        if SkillConditionals.BloodfiendOrBloodbag(self, env):
            dynamic_bonus = 0.1
        elif not env.enemy.has_status('Rupture'):
            dynamic_bonus = 0.0
        elif env.enemy.statuses['Rupture'].potency >= 10:
            dynamic_bonus = 0.1
        else:
            dynamic_bonus = 0.0
        env.dynamic += dynamic_bonus
        env.effects[self][0] = dynamic_bonus
    
    def FangLuPassiveLateUpdate(self : SkillEffect, env : Environment):
        env.global_state['passive_procs_flu'] = env.global_state.get('passive_procs_flu', 0)
        if env.global_state.get('passive_procs_flu') >= 2: return
        if getattr(env.unit, 'has_bleed', False) or env.unit.has_status("Bleed"):
            env.enemy.apply_status('Rupture', 3, 0)
        env.global_state['passive_procs_flu'] += 1
    
    def FangLuPassiveMegalateUpdate(self : SkillEffect, env : Environment):
        dynamic_bonus =  env.effects[self][0] 
        env.dynamic -= dynamic_bonus
        env.effects[self][0] = 0
        
    def BarberOutisS1Bloodfeast(self : SkillEffect, env : Environment):
        current_blood : int = env.unit.bloodfeast
        potential_blood_consumed : int = clamp(current_blood, 0, 40)
        intervals : int = potential_blood_consumed // 8
        if intervals > 0:
            blade_gain : int = intervals * 1
            env.unit.blades += blade_gain
            if env.unit.blades > 30: env.unit.blades = 30
            blood_consumed : int = intervals * 8
            env.unit.bloodfeast -= blood_consumed
            env.unit.total_blood += blood_consumed
        else:
            pass
        env.effects[self] = [0, -1]
    
    def BarberOutisS2Bloodfeast(self : SkillEffect, env : Environment):
        current_blood : int = env.unit.bloodfeast
        potential_blood_consumed : int = clamp(current_blood, 0, 60)
        intervals : int = potential_blood_consumed // 6
        if intervals > 0:
            blade_gain : int = intervals * 1
            env.unit.blades += blade_gain
            if env.unit.blades > 30: env.unit.blades = 30
            blood_consumed : int = intervals * 6
            env.unit.bloodfeast -= blood_consumed
            env.unit.total_blood += blood_consumed
        else:
            pass
        env.effects[self] = [0, -1]

    def BarberOutisS3Bonus(self : SkillEffect, env : Environment):
        dynamic_bonus : float
        if env.unit.blades >= 20:
            dynamic_bonus = clamp(env.unit.blades * 0.04, 0, 1.2)
        elif env.unit.blades >= 10:
            dynamic_bonus = clamp(env.unit.blades * 0.03, 0, 0.57)
        else:
            dynamic_bonus = 0
        env.dynamic += dynamic_bonus
        env.effects[self] = [dynamic_bonus, -1]
    
    def BarberOutisS3AtkWeight(self : SkillEffect, env : Environment):
        env.unit.atk_weight = 1
        blades_to_consume : int = 0
        if env.unit.blades >= 10:
            env.unit.atk_weight += 1
            blades_to_consume += 10
        if env.unit.blades >= 20:
            env.unit.atk_weight += 1
            blades_to_consume += 10
        env.effects[self] = [env.unit.atk_weight, -1]
        env.global_state['BladeToConsume'] = blades_to_consume
    
    def BarberOutisResetAtkWeight(self : SkillEffect, env : Environment):
        blades_consumed : int = env.global_state['BladeToConsume']
        env.unit.blades -= blades_consumed
        if env.unit.blades < 1: env.unit.blades = 1
        env.effects[self] = [0, -1]
    
    def BarberOutisPassiveEarlyUpdate(self : SkillEffect, env : Environment):
        dynamic_bonus : float = clamp(0.015 * (env.unit.total_blood // 10), 0, 0.3)
        if env.enemy.has_status('Bleed'):
            dynamic_bonus += clamp(0.005 * env.enemy.statuses['Bleed'].potency, 0, 0.1)
        env.dynamic += dynamic_bonus
        env.effects[self][0] = dynamic_bonus
    
    def FixedDamage(self : SkillEffect, env : Environment):
        if not env.ignore_fixed_damage:
            env.total += self.value
        env.enemy.take_damage(self.value, env)
        env.effects[self] = [self.value, -1]

    def GainBloodiedHand(self : SkillEffect, env : Environment):
        env.unit.hand += self.value
        env.unit.hand = clamp(env.unit.hand, 0, 30)
        env.effects[self] = [0, -1]
    
    def PriestGregorS1OnUse(self : SkillEffect, env : Environment):
        env.unit.bloodfeast += 10
        if env.unit.missing_hp < 0.5:
            env.unit.bloodfeast += 10
        env.effects[self] = [0, -1]
    
    def PriestGregorS2OnUse(self : SkillEffect, env : Environment):
        if env.unit.heart >= 5:
            current_blood : int = env.unit.bloodfeast
            potential_blood_consumed : int = clamp(current_blood, 0, 60)
            intervals : int = potential_blood_consumed // 6
            if intervals > 0:
                hand_gain : int = intervals * 1
                env.unit.hand += hand_gain
                if env.unit.hand > 30: env.unit.hand = 30
                blood_consumed : int = intervals * 6
                env.unit.bloodfeast -= blood_consumed
                env.unit.total_blood += blood_consumed
        else:
            env.unit.hand += 3
            if env.unit.hand > 30: env.unit.hand = 30
            env.unit.bloodfeast += 10
        env.unit.bloodfeast += 10
        env.effects[self] = [0, -1]
    
    def PriestGregorS3OnUse(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        env.global_state['S3Reuse'] = False
        if env.unit.hand <= 10: return
        excess : int = env.unit.hand - 10
        env.unit.hand -= excess
        if excess >= 10:
            env.coin_power += 1
        if excess >= 20:
            env.global_state['S3Reuse'] = True      
        env.unit.bloodfeast += 10
    
    def PriestGregorInnatePassiveOnHit(self : SkillEffect, env : Environment):
        if env.unit.hand >= 20:
            env.enemy.apply_status('Bleed', 1, 0, env)
            env.enemy.apply_status('Rupture', 1, 0, env)

    def GainBloomingThorn(self : SkillEffect, env : Environment):
        env.unit.thorns = clamp(env.unit.thorns + self.value, 0, 30)
        env.effects[self] = [self.value, -1]
    
    def DulcRodyaS1OnUse(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        if env.unit.bloodfeast < 10:
            env.unit.bloodfeast += 5
        else:
            potential_bloodfeast : int = clamp(env.unit.bloodfeast, 0, 20)
            thorn_gain = clamp(potential_bloodfeast // 10, 0, 2)
            bloodfeast_consumed = thorn_gain * 10
            thorn_gain += 1
            env.unit.bloodfeast -= bloodfeast_consumed
            env.unit.total_blood += bloodfeast_consumed
            env.unit.thorns = clamp(env.unit.thorns + thorn_gain, 0, 30)
        
    def DulcRodyaS2OnUse(self : SkillEffect, env : Environment):
        env.base += 2
        env.effects[self] = [0, -1]
        if env.unit.bloodfeast < 10:
            env.unit.bloodfeast += 5
        else:
            potential_bloodfeast : int = clamp(env.unit.bloodfeast, 0, 30)
            thorn_gain = clamp(potential_bloodfeast // 10, 0, 3)
            bloodfeast_consumed = thorn_gain * 10
            thorn_gain += 2
            env.unit.bloodfeast -= bloodfeast_consumed
            env.unit.total_blood += bloodfeast_consumed
            env.unit.thorns = clamp(env.unit.thorns + thorn_gain, 0, 30)
    
    def DulcRodyaS3OnUse(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        env.unit.thorns = clamp(env.unit.thorns + 3, 0, 30)
        festive_fever_count : int = clamp(3 + env.unit.total_blood // 50, 3, 10)
        env.unit.apply_status(StatusNames.festive_fever, 0, festive_fever_count)
        env.unit.apply_status_next_turn(StatusNames.festive_fever, 0, festive_fever_count)
    
    def DulcRodyaS4OnUse(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        env.unit.thorns = clamp(env.unit.thorns + 5, 0, 30)
        festive_fever_count : int = clamp(5 + env.unit.total_blood // 50, 5, 10)
        env.unit.apply_status(StatusNames.festive_fever, 0, festive_fever_count)
        env.unit.apply_status_next_turn(StatusNames.festive_fever, 0, festive_fever_count)
        env.dynamic += clamp((env.unit.total_blood // 5) * 0.01, 0, 0.5)
        env.unit.atk_weight = 3
    
    def DulcRodyaS4AfterAttack(self : SkillEffect, env : Environment):
        env.effects[self] = [0, -1]
        env.unit.thorns = 0
    
    def DulcRodyaInnatePassive(self : SkillEffect , env : Environment, status_type : str, potency : int, count : int):
        if (status_type == StatusNames.rupture) or (status_type == StatusNames.bleed):
            bonus_status : int = clamp(env.unit.thorns // 10, 0, 2)
            if bonus_status > 0:
                env.enemy.apply_status(status_type, bonus_status, 0)

SkillConditional = Callable[[SkillEffect, Environment], bool]
AnySkillConditional = Union[int, SkillConditional]

class SkillConditionalConstructors:
    @staticmethod
    def has_sewing_target():
        return SkillConditionals(SkillConditionals.has_status, {"StatusName" : StatusNames.sewing_target})

scc = SkillConditionalConstructors

class SkillConditionals:
    def __init__(self, method : Callable[[SkillEffect, Environment, dict|None], bool], data : dict) -> None:
        self.eval_func : Callable[[SkillEffect, Environment, dict|None], bool] = method
        self.data : dict = data

    def __call__(self, effect : SkillEffect, env : Environment, *args, **kwargs) -> bool:
        return self.eval_func(effect, env, self.data)
    
    @staticmethod
    def IncludeFixedDamage(self : SkillEffect, env : Environment) -> bool:
        return not env.ignore_fixed_damage
    
    @staticmethod
    def IgnoreFixedDamage(self : SkillEffect, env : Environment) -> bool:
        return env.ignore_fixed_damage

    @staticmethod
    def has_status(self : SkillEffect, env : Environment, data : dict) -> bool:
        return env.enemy.has_status(data['StatusName'])

    @staticmethod
    def Union(self : SkillEffect, env : Environment, data : dict) -> bool:
        eval_func : SkillConditional
        for eval_func in data['methods']:
            if eval_func(self, env, data) == False: return False 
        return True
    
    @staticmethod
    def HasEgoHeadsHit(self : SkillEffect, env : Environment, data = None) -> bool:
        if getattr(env.unit, 'ego', False) and env.sequence[env.current_coin_index] == "Heads":
            return True
        return False
    
    @staticmethod
    def HasMark(self : SkillEffect, env : Environment, data = None) -> bool:
        if getattr(env.enemy, 'vengeance_mark', False):
            return True
        return False
    
    @staticmethod
    def RoseRodyaReuse(self : SkillEffect, env : Environment, data = None) -> bool:
        if getattr(env.unit, 'charge', 0) >= 3 and env.sequence[env.current_coin_index] == "Heads":
            return True
        return False
    
    @staticmethod
    def DevRodyaRuptureCond(self : SkillEffect, env : Environment, data = None) -> bool:
        return env.global_state.get('DevyatRuptureCond', False)
    
    @staticmethod
    def DevRodyaRuptureCondInverted(self : SkillEffect, env : Environment, data = None) -> bool:
        return not env.global_state.get('DevyatRuptureCond', False)
    
    @staticmethod
    def CourrierTrunkBelow15(self : SkillEffect, env : Environment, data = None):
        return (getattr(env.unit, 'trunk', 0) < 15)
    
    @staticmethod
    def HasDefensiveStance(self : SkillEffect, env : Environment, data = None) -> bool:
        return True if getattr(env.unit, 'defense_stance', 0) else False
    
    @staticmethod
    def EnemyPhysResWeakOrFatal(self : SkillEffect, env : Environment, data = None) -> bool:
        return True if env.enemy.phys_res[env.skill.type[0]] > 1 else False
    
    @staticmethod
    def TremorSumAbove20(self : SkillEffect, env : Environment, data = None) -> bool:
        if not env.enemy.has_status('Tremor'): return False
        the_tremor : StatusEffect = env.enemy.statuses['Tremor']
        return (the_tremor.potency + the_tremor.count >= 20)
    
    @staticmethod
    def ButterSangAttackCancelled(self : SkillEffect, env : Environment, data = None) -> bool:
        return getattr(env.unit, 'attack_cancel', False)
    
    @staticmethod
    def PassiveActive(self : SkillEffect, env : Environment, data = None) -> bool:
        return getattr(env.unit, 'passive', False)
    
    @staticmethod
    def ConsumedTremor(self : SkillEffect, env : Environment, data = None) -> bool:
        return True if env.global_state.get('ConsumedTremor', 0) else False
    
    @staticmethod
    def Enemy6PlusTremor(self : SkillEffect, env : Environment, data = None) -> bool:
        if not env.enemy.has_status('Tremor'): return False
        return env.enemy.statuses['Tremor'].potency >= 6
    
    @staticmethod
    def FLuRuptureCond(self : SkillEffect, env : Environment, data=None) -> bool:
        return env.global_state.get('FangLuRuptureCond', False)
    
    @staticmethod
    def FLuRuptureCondInverted(self : SkillEffect, env : Environment, data=None) -> bool:
        return not env.global_state.get('FangLuRuptureCond', False)
    
    @staticmethod
    def BloodfiendOrBloodbag(self : SkillEffect, env : Environment, data = None) -> bool:
        return getattr(env.enemy, 'is_bloodfiend', False)
    
    @staticmethod
    def FangLuS3Reuse(self : SkillEffect, env : Environment, data = None) -> bool:
        if (getattr(env.enemy, 'hp_percent', None) or (env.enemy.hp / env.enemy.max_hp)) < 0.3:
            return True
        if not env.enemy.has_status("Rupture"): return False
        return env.enemy.statuses["Rupture"].potency >= 15
    
    @staticmethod
    def PriestGregorS3Reuse(self : SkillEffect, env : Environment, data = None) -> bool:
        return env.global_state['S3Reuse']
    
    
    
GetterMethod = Callable[[SkillEffect, Environment], float|int|Any]
SetterMethod = Callable[[SkillEffect, Environment, float|int|Any], None]
class GetterMethods:
    @staticmethod
    def RedRyoSum(self : SkillEffect, env : Environment) -> int:
        return env.unit.red_eyes + env.unit.penitence
    
    @staticmethod
    def ButterflySangAmmoSum(self : SkillEffect, env : Environment) -> int:
        return env.unit.the_living + env.unit.the_departed

    @staticmethod
    def ButterflySinkingSum(self : SkillEffect, env : Environment) -> int:
        the_sum : int = 0
        if env.enemy.has_status('Sinking'):
            the_sum += env.enemy.statuses['Sinking'].potency
        if env.enemy.has_status(StatusNames.butterfly):
            the_sum += env.enemy.statuses[StatusNames.butterfly].potency
            the_sum += env.enemy.statuses[StatusNames.butterfly].count
        return the_sum
    
    
    

sk = SkillEffect
skc = SkillEffectConstructors

class StatusNames:
    echoes_of_the_manor = 'Echoes of the Manor'
    butterfly = 'Butterfly'
    sinking = 'Sinking'
    rupture = 'Rupture'
    bleed = 'Bleed'
    tremor = 'Tremor'
    burn = 'Burn'
    bind = 'Bind'
    haste = 'Haste'
    offense_level_up = 'Offense Level Up'
    defense_level_down = 'Defense Level Down'
    defense_level_up = 'Defense Level Up'
    fragile = "Fragile"
    damage_up = "Damage Up"
    atk_power_up = 'Attack Power Up'
    plus_coin_boost = 'Plus Coin Boost'

    photoelectricity = 'Photoelectricity'
    charge_barrier = 'Charge Barrier'
    red_plum_blossom = "Red Plum Blossom"
    rpm = red_plum_blossom
    dark_flame = "Dark Flame"
    BM = 'BM'
    weakness_analyzed = 'Weakness Analyzed'

    slash_fragile = "Slash Fragility"
    blunt_fragile = "Blunt Fragility"
    pierce_fragile = "Pierce Fragility"

    slash_dmg_up = "Slash Damage Up"
    blunt_dmg_up = "Blunt Damage Up"
    pierce_dmg_up = "Pierce Damage Up"
    
    wrath_fragile = "Wrath Fragility"
    lust_fragile = "Lust Fragility"
    sloth_fragile = "Sloth Fragility"
    gluttony_fragile = "Gluttony Fragility"
    gloom_fragile = "Gloom Fragility"
    pride_fragile = "Pride Fragility"
    envy_fragile = "Envy Fragility"

    nails = "Nails"
    gaze = "Gaze"
    sewing_target = 'Sewing Target'
    festive_fever = 'Festive Fever'
    
class StatusEffect:
    @classmethod
    def new(cls, type : str, pot_and_count : tuple[int, int], owner : Unit|Enemy):
        new_effect = StatusEffect(type, owner)
        intensity_set : bool = False
        match type:
            case 'Sinking':
                new_effect.on_hit = SpecialStatusEffects.drain_count
            case 'Tremor':
                new_effect.on_turn_end = SpecialStatusEffects.drain_count
                new_effect.on_skill_start = SpecialStatusEffects.apply_tremor
            case 'Rupture':
                new_effect.on_hit = SpecialStatusEffects.rupture_when_hit
            case 'Bleed':
                pass
            case 'Burn':
                new_effect.on_turn_end = SpecialStatusEffects.drain_count                    
            case 'Bind'|'Haste':
                new_effect._has_potency = False
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Offense Level Up':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_ol_up
                new_effect.on_turn_end = SpecialStatusEffects.consume_all           
            case 'Defense Level Down':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_def_down
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Defense Level Up':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_def_up
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Attack Power Up':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_atk_power_up
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Plus Coin Boost':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_coin_power
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Fragile':
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_skill_start = SpecialStatusEffects.apply_fragile
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case StatusNames.festive_fever:
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_skill_start = SpecialStatusEffects.apply_festive_fever
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case "Damage Up":
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_skill_start = SpecialStatusEffects.apply_damage_up
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Photoelectricity':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_photoelectricity
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case "BM":
                new_effect._has_potency = False
                new_effect.on_turn_end = SpecialStatusEffects.drain_count 
            case 'Echoes of the Manor':
                new_effect._has_potency = False
                new_effect._max_count = 3
                new_effect.on_skill_start = SpecialStatusEffects.apply_manors
                new_effect.on_turn_end = SpecialStatusEffects.drain_count
            case StatusNames.butterfly:
                new_effect._max_potency = 15
                new_effect._max_count = 15
                new_effect.on_skill_start = SpecialStatusEffects.apply_butterfly
                new_effect.on_turn_end = SpecialStatusEffects.butterfly_turn_end
            case StatusNames.weakness_analyzed:
                new_effect._has_potency = False
                new_effect._max_count = 1
                new_effect.on_skill_start = SpecialStatusEffects.apply_weakness_analyzed
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case 'Charge Barrier':
                new_effect._has_potency = False
                new_effect.on_turn_end = SpecialStatusEffects.charge_barrier_turn_end            
            case "Red Plum Blossom":
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_hit = SpecialStatusEffects.drain_count
                new_effect.on_skill_start = SpecialStatusEffects.apply_blossom           
            case "Dark Flame":
                new_effect._has_potency = False
                new_effect._max_count = 7
                new_effect.on_skill_start = SpecialStatusEffects.apply_dark_flame
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case (StatusNames.blunt_fragile|StatusNames.slash_fragile|StatusNames.pierce_fragile|StatusNames.wrath_fragile|StatusNames.lust_fragile|
            StatusNames.sloth_fragile|StatusNames.gluttony_fragile|StatusNames.gloom_fragile|StatusNames.pride_fragile|StatusNames.envy_fragile):
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_skill_start = SpecialStatusEffects.apply_typed_fragile
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case (StatusNames.slash_dmg_up|StatusNames.blunt_dmg_up|StatusNames.pierce_dmg_up):
                new_effect._has_potency = False
                new_effect._max_count = 10
                new_effect.on_skill_start = SpecialStatusEffects.apply_typed_damage_up
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case "Nails":
                new_effect._has_potency = False
                new_effect.on_turn_end = SpecialStatusEffects.drain_half_count
            case "Gaze":
                new_effect._has_potency = False
                new_effect._max_count = 1
                new_effect.on_skill_start = SpecialStatusEffects.apply_gaze
                new_effect.on_turn_end = SpecialStatusEffects.consume_all
            case StatusNames.sewing_target:
                new_effect._has_potency = False
                new_effect._max_count = 1
                new_effect.on_turn_end = SpecialStatusEffects.drain_count
                new_effect.on_skill_start = SpecialStatusEffects.apply_sewing_target
            case 'Fanatic':
                new_effect._has_potency = False
                new_effect.on_skill_start = SpecialStatusEffects.apply_fanatic
                new_effect.on_turn_end = SpecialStatusEffects.consume_all

            case _:
                pass
        
        if not intensity_set:
            new_effect.add(*pot_and_count)
        return new_effect


    def __init__(self, type : str, owner : Unit|Enemy, has_potency : bool = True) -> None:
        self._has_potency : bool = has_potency
        self._max_count : int = 99
        self._max_potency : int = 99
        self.potency = 0
        self.count = 0
        self.type : str = type
        self.owner : Unit|Enemy = owner
    
    def check_numbers(self):
        if self.count > self._max_count:
            self.count = self._max_count
        if not self._has_potency:
            self.potency = 0
        elif self.potency > self._max_potency:
            self.potency = self._max_potency
    
    def add_potency(self, potency : int):
        if not self._has_potency: return
        self.potency += potency
        if self.count <= 0:
            self.count = 1
        if self.potency <= 0 and self._has_potency:
            self.potency = 1
        self.check_numbers()

    def add_count(self, count : int):
        self.count += count
        if self.count <= 0:
            self.count = 1
        if self.potency <= 0 and self._has_potency:
            self.potency = 1
        self.check_numbers()
    
    def add(self, potency : int, count : int):
        if self.potency + self.count + potency + count <= 0:
            self.potency = 0
            self.count = 0
            return
        if self._has_potency: self.potency += potency
        self.count += count
        if self.count <= 0:
            self.count = 1
        if self.potency <= 0 and self._has_potency:
            self.potency = 1
        
        self.check_numbers()
    
    def consume_potency(self, potency : int):
        if not self._has_potency: return
        self.potency -= potency
        if self.count <= 0:
            self.potency = 0
            self.count = 0
        if self.potency <= 0 and self._has_potency:
            self.potency = 0
            self.count = 0
        self.check_numbers()

    def consume_count(self, count : int):
        self.count -= count
        if self.count <= 0:
            self.potency = 0
            self.count = 0
        if self.potency <= 0 and self._has_potency:
            self.potency = 0
            self.count = 0
        self.check_numbers()
    
    def consume_either(self, potency : int, count : int):
        if self._has_potency: self.potency -= potency
        self.count -= count
        if self.count <= 0:
            self.potency = 0
            self.count = 0
        if self.potency <= 0 and self._has_potency:
            self.potency = 0
            self.count = 0
        self.check_numbers()
    
    def is_active(self) -> bool:
        if self.count <= 0:
            return False
        if self._has_potency and self.potency <= 0:
            return False
        return True
        
    
    @staticmethod
    def on_hit(self : 'StatusEffect', env : Environment):
        pass

    @staticmethod
    def when_first_applied(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        pass

    @staticmethod
    def when_added(self : 'StatusEffect', amount : tuple[int, int], env : Environment, is_defending : bool = True):
        pass

    @staticmethod
    def on_skill_start(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        pass

    @staticmethod
    def on_skill_end(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        pass

    @staticmethod
    def on_turn_start(self : 'StatusEffect'):
        pass

    @staticmethod
    def on_turn_end(self : 'StatusEffect'):
        pass

class SpecialStatusEffects:
    @staticmethod
    def drain_count(self : StatusEffect, env : Environment|None = None):
        self.consume_count(1)
    
    @staticmethod
    def rupture_when_hit(self : StatusEffect, env : Environment):
        if not env.CONSUME_RUPTURE: return
        self.consume_count(1)

    @staticmethod
    def drain_half_count(self : StatusEffect, env : Environment|None = None):
        self.consume_count(ceil(self.count / 2))
    
    @staticmethod
    def consume_all(self : StatusEffect, env : Environment|None = None):
        self.consume_count(self.count)
    
    @staticmethod
    def butterfly_turn_end(self : StatusEffect):
        self.count = 0
        self.owner.apply_status('Sinking', self.potency, 0)
        self.count = self.potency
        self.potency = 0

    @staticmethod
    def charge_barrier_turn_end(self : StatusEffect):
        count = self.count
        self.consume_count(self.count)
        if not hasattr(self.owner, 'charge'):
            self.owner.charge = 0
        self.owner.charge += count
        if self.owner.charge > 20: self.owner.charge = 20
        if self.owner.charge < 0: self.owner.charge = 0
    
    @staticmethod
    def apply_photoelectricity(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.Photoelectricity(self.count)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_manors(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.EchoesOfTheManor()
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_butterfly(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.Butterfly(self)
        env.apply_queue.append(new_effect)
        
    @staticmethod
    def apply_weakness_analyzed(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.WeaknessAnalyzed()
        env.apply_queue.append(new_effect)
        
    @staticmethod
    def add_sinking(self : StatusEffect, potency : int, count : int):
        self.potency += potency
        self.count += count
        
        if self.count <= 0:
            self.count = 1
        if self.potency <= 0:
            self.potency = 1
        
        self.check_numbers()
    
    @staticmethod
    def apply_ol_up(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.OffenseLevelUp(self.count)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_atk_power_up(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.BasePowerUp(self.count)
        env.apply_queue.append(new_effect)

    @staticmethod
    def apply_coin_power(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.CoinPower(self.count)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_festive_fever(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.FestiveFever(self.count, self)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_def_down(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.DefenseLevelDown(self.count)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_def_up(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.DefenseLevelDown(-self.count)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_fragile(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.Fragile(self.count, self)
        env.apply_queue.append(new_effect)
    
    def apply_sewing_target(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.DAddXForEachY(0.005, 'dynamic', 1, 'enemy.statuses.Bleed.potency', 0, 0.1)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_fanatic(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.Fanatic(self.count, self)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_typed_fragile(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        physical_type : str = env.skill.type[0]
        sin_type : str = env.skill.type[1]
        frag_type : str = self.type.split()[0]
        if not (frag_type == physical_type or frag_type == sin_type): return
        new_effect = skc.Fragile(self.count, self)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_damage_up(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        new_effect = skc.Fragile(self.count, self)
        env.apply_queue.append(new_effect)

    @staticmethod
    def apply_typed_damage_up(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if is_defending: return
        physical_type : str = env.skill.type[0]
        sin_type : str = env.skill.type[1]
        frag_type : str = self.type.split()[0]
        if not (frag_type == physical_type or frag_type == sin_type): return
        new_effect = skc.Fragile(self.count, self)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_gaze(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        physical_type : str = env.skill.type[0]
        if physical_type != "Blunt" and physical_type != "Pierce": return
        new_effect = skc.DynamicBonus(0.2)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_blossom(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.RedPlumBlossom(self.count, self)
        env.apply_queue.append(new_effect)
    
    @staticmethod
    def apply_dark_flame(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.DefenseLevelDown(self.count)
        env.apply_queue.append(new_effect)

    @staticmethod
    def apply_tremor(self : 'StatusEffect', env : Environment, is_defending : bool = True):
        if not is_defending: return
        new_effect = skc.Tremor(self.count, self)
        env.apply_queue.append(new_effect)


class DamageTypes:
    blunt = "Blunt"
    pierce = "Pierce"
    slash = "Slash"

    wrath = "Wrath"
    lust = "Lust"
    sloth = "Sloth"
    gluttony = 'Gluttony'
    gloom = "Gloom"
    pride = "Pride"
    envy = "Envy"

class TremorFlavors:
    decay = 'Decay'
    reverb = 'Reverb'

class SkillTagNames:
    spends_charge = 'SpendsCharge'
    does_bloodfeast = 'ConsumesOrGainsBloodfeast'

dgt = DamageTypes
X : int = 0
B : int = 0
C : int = 0
Y : int = 0
Z : int = 0
SKILLS = {
"Coerced Judgement" : Skill((8, -2, 2), 5, 'Coerced Judgement', ("Blunt", "Gloom"), [[], [sk.new("OnTailsHit", skc.ApplyFanatic(1))]]),
"Amoral Enactement" : Skill((16, -4, 4), 5, "Amoral Enactement", ("Blunt", "Lust"), [[], [], [], []], [SkillEffect("dynamic", "add", 0.10, condition=0)]),
"Self-Destrutive Purge" : Skill((30, -12, 3), 5, "Self-Destrutive Purge", ("Blunt", "Wrath"), [[], [], []], [SkillEffect("dynamic", "add", 0.15, condition=0)]),



"Remise" : Skill((3, 4, 2), 2, "Remise", ("Pierce", "Gluttony"), [[], []], [sk.new("GainPoise", (0, 2)), skc.AddXForEachY(1, "coin_power", 2, "unit.speed")]),
"Engagement" : Skill((4, 4, 3), 2, "Engagement", ("Pierce", "Pride"), [[sk.new("GainPoise", (0, 1))], [sk.new("GainPoise", (0, 1))], []], 
[sk.new("GainPoise", (0, 2), condition=0), sk.new("AddXForEachY", (1, "coin_power", 2, "unit.speed", (0,2)))]),
"Contre Attaque" : Skill((5, 4, 3), 2, "Contre Attaque", ("Pierce", "Lust"), 
[[sk.new("Fragile", 1, condition=1)],[sk.new("Fragile", 1 , condition=1)], [sk.new("CinqClairS3CritBonus", None)]], 
[sk.new('CinqClairS3Conversion', None, condition=0), sk.new("AddXForEachY", (1, "coin_power", 2, "unit.speed", (0,3)))]),


"Graze The Grass" : Skill((4, 2, 3), 5, "Graze The Grass", ("Pierce", "Wrath"), [[], [], []]),
"Concentrated Fire" : Skill((4, 2, 4), 5, "Concentrated Fire", ("Pierce", "Gluttony"), [[], [], [], []], 
[skc.AddXForEachY(1, 'coin_power', 6, 'unit.speed')]),
"Quick Suppression" : Skill((3, 2, 5), 5, "Quick Suppression", ("Pierce", "Envy"),
[[sk.new("Fragile", 2)], [sk.new("Fragile", 2)], [], [], []], [skc.AddXForEachY(2, 'coin_power', 6, 'unit.speed', 0, 2)]),


"Mind Strike" : Skill((4, 5, 2), 1, "Mind Strike", ("Blunt", "Gloom"), 
[[sk.new("GainCharge", 2)], [sk.new("GainCharge", 2)]], [sk.new("GainCharge", 2)]),
"Flying Surge" : Skill((6, 12, 1), 1, "Flying Surge", ("Blunt", "Envy"), [[]], [sk.new("GainCharge", 7)]),
"Mind Whip" : Skill((2, 6, 4), 1, "Mind Whip", ("Blunt", "Wrath"), [[], [], [], []], 
    [sk.new("SpendX", (8, "unit.charge", 8))]),


"Umbrella Thwack" : Skill((6, -2, 3), 2, "Umbrella Thwack", ("Blunt", "Envy"), [[], [], []]),
"Puddle Stomp" : Skill((10, -3, 4), 3, "Puddle Stomp", ("Blunt", "Gloom"), [[], [], [], [skc.DynamicBonus(0.2, 0)]], 
[skc.AddXForEachY(3, 'base', -15, 'unit.sp', 0, 3), skc.AddXForEachY(2, 'base', -25, 'unit.sp', 0, 2)]),
"Spread Out!" : Skill((18, -7, 3), 3, "Spread Out!", ("Pierce", "Sloth"), [[], [], [skc.OnTailsHit(skc.ApplyStatusCountNextTurn('Fragile', 1))]]),


"Stalk Prey" : Skill((3, 4, 2), 1, "Stalk Prey", ("Pierce", "Pride"), [[], []]),
"Snagharpoon" : Skill((4, 4, 3), 1, "Snagharpoon", ("Pierce", "Envy"), [[], [], []]),
"Sever Knot" : Skill((4, 3, 4), 3, "Sever Knot", ("Pierce", "Envy"), [[], [], [], []],
                     [sk.new("CoinPower", 1, condition=0), sk.new("CoinPower", 1, condition=1)]),


"Illuminate Thy Vacuity" : Skill((3, 2, 3), -1, "Illuminate Thy Vacuity", ("Blunt", "Gloom"), [[], [], []],
                                 [sk.new("AddXForEachY", (1, "coin_power", 1, "unit.insight", (0,2), 1))]),
"Weight of Knowledge" : Skill((3, 3, 4), 1, "Weight of Knowledge", ("Blunt", "Envy"), [[] for _ in range(4)]),
"Excruciating Study" : Skill((4, 3, 4), 2, "Excruciating Study", ("Blunt", "Sloth"), [[] for _ in range(4)],
                             [sk.new("CoinPower", 1, condition=0)]),

"PC" : Skill((4, 3, 2), 3, "PC", ("Slash", "Wrath"), [[], []]),
"IH" : Skill((3, 5, 3), 3, "IH", ("Pierce", "Envy"), [[],[],[]]),

"I Can Cook Anything" : Skill((3, 3, 4), 3, "I Can Cook Anything", ("Slash", "Lust"),
                              [[],[],[], [sk.new("ICCALastCoinBonus", None)]], [sk.new("ICCA", None)]),


"Wait Up!" : Skill((4, 7, 1), 1, "Wait Up!", ("Slash", "Wrath"), [[]], 
[sk('unit.tremor', 'add', 2), sk.new("AddXForEachY", (2, "base", 6, "unit.tremor", (0,2), 0))]),
"Slice" : Skill((3, 5, 3), 4, "Slice", ("Blunt", "Lust"), [[sk('enemy.tremor', 'add', 2)],[sk('enemy.tremor', 'add', 2)],[sk.new("MolarBurst", None)]]),
"Daring Decision" : Skill((4, 3, 4), 5, "Daring Decision", ("Blunt", "Sloth"), 
[[sk('enemy.tremor', 'add', 4)], [sk.new("MolarBurst", None)], [sk.new("MolarBurst", None)], [sk.new("MolarBurst", None)]],
[sk.new("AddXForEachY", (2, "coin_power", 10, "unit.tremor", (0,2))), sk.new("SpendX", (10, "unit.tremor", 10))]),

"Expend Knowledge" : Skill((5, 5, 1), 2, 'Expend Knowledge', ('Slash', 'Wrath'), [[]], [sk.new('DeiciLuReuse', 0)]),
"Unveil" : Skill((4, 4, 3), 2, 'Unveil', ('Slash', 'Gloom'), [[], [], []], [sk.new("AddXForEachY", (1, "coin_power", 1, "unit.insight", (0,2), 1))]),
"Cyclical Knowledge" : Skill((5, 3, 3), 4, 'Cyclical Knowledge', ('Blunt', 'Sloth'), [[], [], []],
[sk.new("AddXForEachY", (1, "coin_power", 1, "unit.insight", (0,2), 1)), sk.new("AddXForEachY", (1, "coin_power", 1, "unit.insight", (0,1), 1))]),

"Paint Over" : Skill((2, 3, 3), 3, 'Paint Over', ('Pierce', 'Gloom'), [[], [sk.new("RingRandomStatus", (0, 2))], [sk.new("ApplyStatus", ('Bleed', 2, 0))]]),
"Sanguine Pointillism": Skill((8, 8, 1), 3, 'Sanguine Pointillism', ('Pierce', 'Lust'), 
[[sk.new("ApplyStatus", ('Bleed', 0, 1)), sk.new("RingRandomStatus", (0, 3))]], 
[sk.new("DAddXForEachY", (1, "coin_power", 3, "enemy.statuses.Bleed.count", (0,2), 0)), sk.new('RingSangReuse', 0)]),
"Hematic Coloring" : Skill((3, 3, 4), 3, "Hematic Coloring", ('Pierce', 'Sloth'),
[[], [sk.new("ApplyStatus", ('Bleed', 0, 1)), sk.new("RingRandomStatus", (0, 3))], 
[sk.new("ApplyStatus", ('Bleed', 1, 0)), sk.new("RingRandomStatus", (2, 0))], [sk.new("RingSangS3Bonus", None)]], 
[sk.new("DAddXForEachY", (1, "coin_power", 3, "enemy.statuses.Bleed.count", (0,2), 0))]),

"Red Kick" : Skill((4, 3, 2), 2, "Red Kick", ("Blunt", "Lust"), [[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))],[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))]], 
[skc.DAddXForEachY(1, "coin_power", 3, "enemy.statuses.Burn.potency", 0, 2, 0)]),

"Frontal Assault" : Skill((4, 4, 3), 2, "Frontal Assault", ("Blunt", "Wrath"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.LiuIshS2Burn())]],
[skc.DAddXForEachY(1, "coin_power", 6, "enemy.statuses.Burn.potency", 0, 2, 0)]),

"Inner Gate Elbow Strike" : Skill((3, 3, 4), 2, "Inner Gate Elbow Strike", ("Blunt", "Envy"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 0, 2))], []], [sk.new("LiuIshS3Bonus", 0)]),

'Rip(Don)' : Skill((5, 6, 1), 3, "Rip(Don)", ('Slash', 'Sloth'), [[skc.OnHeadsHit(skc.GainCharge(4))]], 
[skc.DAddXForEachY(2, 'coin_power', 5, 'unit.charge', 0, 2)]),
'Leap(Don)' : Skill((4, 4, 3), 3, 'Leap(Don)', ('Pierce', 'Gloom'), [[skc.OnHit(skc.GainCharge(4))], [skc.OnHit(skc.GainCharge(4))], []],
[skc.DAddXForEachY(1, 'coin_power', 7, 'unit.charge')]),
'Rip Space' : Skill((1, 2, 5), 3, 'Rip Space', ('Slash', 'Envy'), [[] for _ in range(5)],
[skc.ConsumeChargeTrigger(10, skc.CoinPower(4))]),

'EC' : Skill((3, 2, 3), 5, "EC", ('Slash', 'Lust'), [[skc.OnHit(skc.GainCharge(2))], [skc.OnHit(skc.GainCharge(2))], []],
[skc.DAddXForEachY(0.1, "dynamic", 10, "unit.charge", 0, 0.1), skc.DAddXForEachY(0.1, "dynamic", 15, "unit.charge", 0, 0.1)]),
'Leap(Ryoshu)' : Skill((2, 5, 3), 5, "Leap(Ryoshu)", ('Slash', 'Pride'), 
[[skc.OnHit(skc.AddXForEachY(0.2, "dynamic", 10, "unit.charge", 0, 0.2))], [], [sk('dynamic', 'add', 0.3, condition=0)]],
[skc.GainCharge(7), skc.DAddXForEachY(1, "coin_power", 5, "unit.charge", 0, 2, 5)]),
'DDEDR' : Skill((3, 2, 4), 5, "DDEDR", ('Slash', 'Lust'), [[], [], [], [sk.new("DDEDRLastCoinBouns", None)]], [sk.new('DDEDRCoinPowerBonus', None)]),

'Throat Slit': Skill((5, 8, 1), 3, 'Throat Slit', ('Slash', 'Envy'), [[]]),
'Shank' : Skill((3, 5, 3), 3, 'Shank', ('Pierce', 'Lust'), 
[[skc.OnHeadsHit(skc.FixedDamage(3))], [skc.OnHeadsHit(skc.FixedDamage(3))], 
 [sk.new("ShankDamageBonus", None), sk.new("OnHeadsHit", sk.new("ReuseCoin", 1), condition=0)]]),
'Mutilate' : Skill((5, 25, 1), 3, 'Mutilate', ('Slash', 'Gluttony'), 
[[skc.OnHeadsHit(skc.FixedDamage(7)), sk.new("OnHeadsRoll", sk('dynamic', 'add', 1), condition=0), 
sk.new("OnHeadsRoll", sk.new("AddXForEachY", (0.5, "dynamic", 10, "enemy.statuses.Bleed.potency", (0, 0.5))), condition=0)]]),

"Draw of the Sword" : Skill((3, 4, 2), 3, "Draw of the Sword", ('Slash', 'Pride'), 
[[sk.new("OnHit", sk.new("GainPoise", (1, 0)))], [sk.new("OnHit", sk.new("GainPoise", (1, 0)))]],
[sk.new("DAddXForEachY", (1, "coin_power", 5, "unit.poise_potency", (0,1), 0)), sk.new("GainPoise", (0, 2))]),
"Acupuncture" : Skill((3, 5, 3), 3, "Acupuncture", ('Slash', 'Pride'),
[[sk.new("OnHit", sk.new("GainPoise", (3, 0)))], [], [sk.new("CriticalDamageBonus", 0.6)]],
[sk.new("DAddXForEachY", (1, "coin_power", 7, "unit.poise_potency", (0,1), 0)), sk.new("GainPoise", (0, 3))]),
"Yield My Flesh" : Skill((20, -8, 1), 0, "Yield My Flesh", ('Slash', "Wrath"), 
[[sk.new("CriticalDamageBonus", 0.3), sk.new("OnCritRoll", sk.new("AddXForEachY", (0.03, "dynamic", 1, 'unit.poise_potency', (0, 0.75)), the_duration=1))]], 
[sk.new("GainPoise", (5, 0)), sk.new('AddXForEachY', (0.005, 'dynamic', 0.01, 'unit.missing_hp', (0, 0.25)))]),
"To Claim Their Bones" : Skill((4, 4, 4), 5, "To Claim Their Bones", ('Slash', 'Pride'), 
[[sk.new("OnCritRoll", sk.new("AddXForEachY", (0.02, "dynamic", 1, 'unit.poise_potency', (0, 0.5)), the_duration=1))] for _ in range(4)],
[sk('dynamic', 'add', 1, condition=0), sk.new('AddXForEachY', (0.005, 'dynamic', 0.01, 'unit.missing_hp', (0, 0.25))), sk.new("CriticalDamageBonus", 0.3)]),

"RA1 : The Hunt" : Skill((3, 4, 2), 2, "RA1 : The Hunt", ('Slash', 'Lust'), [[skc.OnHit(skc.GainPoise(0, 2))], [skc.OnHit(skc.ApplyBM(2))]], [skc.GainPoise(0, 2)]),
"RA7 : Capture" : Skill((4, 6, 2), 3, "RA7 : Capture", ('Slash', 'Pride'), 
[[skc.GainPoise(3, 0), skc.GainPoise(3, 0, 0), skc.GainPoise(3, 0, 1), skc.OnCrit(skc.ApplyBM(1))], [skc.OnHit(skc.ApplyBM(2))]]),
"RA2 : SYNC" : Skill((4, 7, 2), 5, "RA2 : SYNC", ('Slash', 'Wrath'), 
[[skc.OnHit(skc.GainPoise(5, 0)), skc.ApplyStatusNextTurn('Bind', 0, 1), skc.OnCrit(skc.ApplyBM(1))], [skc.OnHit(skc.ApplyBM(2))]], 
[skc.AddXForEachY(1, 'coin_power', 2, 'unit.speed', 0, 2), skc.GainPoise(0, 7)]),

"40Y-3 Activation" : Skill((3, 4, 2), 1, "40Y-3 Activation", ('Slash', 'Lust'), [[], [skc.OnHit(skc.GainCharge(3))]], [skc.ConsumeChargeTrigger(5, skc.CoinPower(2))]),
"Charge Countercurrent" : Skill((4, 4, 3), 4, "Charge Countercurrent", ('Blunt', 'Envy'), [[], [], [skc.MCFaustS2DamageBonus(condition=0)]], 
[skc.MCFaustS2ChargeGain(), skc.ConsumeChargeTrigger(10, skc.CoinPower(2))]),
"40Y-3 Charge" : Skill((4, 3, 4), 3, "40Y-3 Charge", ('Blunt', 'Gloom'), [[skc.MCFaustS3ChargeGain()], [skc.MCFaustS3ChargeGain()], [], [skc.MCFaustS3DamageBonus()]],
[skc.DAddXForEachY(1, 'coin_power', 1, 'unit.charge_potency', 0, 4)]),

"Knocking" : Skill((3, 4, 2), 2, "Knocking", ('Blunt', 'Pride'), [[], [skc.OnHit(skc.ApplyStatus('Sinking', 2, 0))]], 
[skc.AddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Sinking.potency', 0, 1)]),
"Dusting" : Skill((4, 4, 3), 2, "Dusting", ('Blunt', 'Gloom'), [[], [skc.OnHit(skc.ApplyStatus('Sinking', 3, 0))], [skc.OnHit(skc.ApplyStatus('Sinking', 2, 0))]],
[skc.AddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Sinking.potency', 0, 1), skc.ApplyStatus('Sinking', 0, 2, condition=0)]),
"As Mistress Commands" : Skill((4, 3, 4), 4, "As Mistress Commands", ('Blunt', 'Lust'), 
[[], [], [], [skc.ButlerOutisS3Bonus(), skc.ApplyStatusNextTurn('Echoes of the Manor', 0, 3)]],
[skc.AddXForEachY(1, 'coin_power', 7, 'enemy.statuses.Sinking.potency', 0, 1), skc.ApplyStatus('Sinking', 0, 3, condition=0)]),

"Ripple" : Skill((3, 4, 2), 0, "Ripple", ('Blunt', 'Pride'), [[], [skc.OnHit(skc.GainCharge(2))]], 
[skc.AddXForEachY(1, 'base', 4, 'unit.charge', 0, 1), skc.GainCharge(2)]),
"Charged Leap" : Skill((5, 6, 2), 0, "Charged Leap", ('Blunt', 'Envy'), [[skc.OnHit(skc.GainCharge(2))], [skc.OnHit(skc.GainCharge(2))]],
[skc.AddXForEachY(1, 'coin_power', 6, 'unit.charge', 0, 1), skc.ConsumeChargeTrigger(6, skc.WarpOutisChargeBarrier()), skc.GainCharge(2)]),
"Rip Dimension" : Skill((4, 3, 4), 0, "Rip Dimension", ('Slash', 'Gloom'), [[], [], [], [skc.WarpOutisChargeGainS3()]], 
[skc.AddXForEachY(0.05, 'dynamic', 1, 'unit.charge_potency', 0, 0.3), skc.WarpOutisCoinpowerS3()]),

"Checking the Book" : Skill((4, 3, 2), 2, "Checking the Book", ("Blunt", "Wrath"), [[], []], []),
"Proof of Loyalty" : Skill((4, 6, 2), 3, "Proof of Loyalty", ("Blunt", "Envy"), [[], []], [skc.MidDonResonanceBonus()]),
"A Just Vengeance" : Skill((4, 3, 4), 3, "A Just Vengeance", ("Blunt", "Pride"), [[] for _ in range(4)], [skc.MidDonResonanceBonus()]),
"A Just Vengeance(Counter)" : Skill((4, 3, 4), 3, "A Just Vengeance(Counter)", ("Blunt", "Envy"), [[] for _ in range(4)],
                                    [skc.MidDonResonanceBonus(), skc.CounterBasepowerGain()]),
"Contracting Straight-jacket" : Skill((4, 7, 1), 3, "Contracting Straight-jacket", ("Blunt", "Sloth"), 
[[skc.OnHit(skc.GainTremor(3))]], [skc.ResetAttackWeight(), skc.GainTremor(3)]),
"Metallic Ringing" : Skill((4, 4, 3), 3, "Metallic Ringing", ("Blunt", "Pride"), 
[[skc.OnHeadsHit(skc.AddXForEachY(1, 'unit.tremor', 1, 'unit.atk_weight', 1, 2))], [], []],
[skc.ResetAttackWeight(), skc.ConsumeRessourceTrigger('unit.tremor', 5, 5, SkillEffect('unit.atk_weight', 'add', 1)), skc.GainTremor(4)]),
"Unleashed Violence" : Skill((3, 5, 3), 3, "Unleashed Violence", ("Blunt", "Wrath"), [[skc.RegretBurst(), skc.OnHit(skc.OffenseLevelUp(2))] for _ in range(3)],
[skc.ConsumeRessourceTrigger('unit.tremor', 5, 5, SkillEffect('unit.atk_weight', 'add', 1)), 
 skc.ConsumeRessourceTrigger('unit.tremor', 5, 5, SkillEffect('unit.atk_weight', 'add', 1)), 
 skc.AddXForEachY(0.06, 'dynamic', 1, 'enemy.fake_status_count', 0.0, 0.3)]),

"Deflect" : Skill((4, 7, 1), 0, "Deflect", ("Slash", "Gloom"), [[]]),
"End-stop Stab" : Skill((4, 4, 2), 0, "End-stop Stab", ("Pierce", "Envy"), [[], []]),
"Enjamb" : Skill((6, 2, 3), 0, "Enjamb", ("Slash", "Sloth"), [[],[],[]]),

"Downward Slash" : Skill((4, 7, 1), -1, "Downward Slash", ("Blunt", "Pride"), [[]]),
"Upward Slash" : Skill((5, 4, 2), -1, "Upward Slash", ("Blunt", "Sloth"), [[], []]),
"Drilling Stab" : Skill((7, 2, 2), -1, "Drilling Stab", ("Pierce", "Gluttony"), [[], []]),

"Joust" : Skill((4, 7, 1), 2, "Joust", ("Pierce", "Lust"), [[]]),
"Galloping Tilt" : Skill((4, 12, 1), 2, "Galloping Tilt", ("Pierce", "Envy"), [[]]),
"For Justice!" : Skill((3, 3, 3), 2, "For Justice!", ("Pierce", "Gluttony"), [[] for _ in range(3)], [skc.AddXForEachY(2, 'coin_power', 10, 'unit.speed', 0, 2,0)]),

"Paint" : Skill((4, 7, 1), 2, "Paint", ("Slash", "Gluttony"), [[]]),
"Splatter" : Skill((4, 5, 2), 2, "Splatter", ("Slash", "Lust"), [[skc.DynamicBonus(0.3, 0, 1)], [skc.DynamicBonus(0.3)]]),
"Brushstroke" : Skill((5, 3, 3), 2, "Brushstroke", ("Slash", "Pride"), [[],[],[]], [skc.DynamicBonus(0.2)]),

"Un, Deux" : Skill((3, 4, 2), -3, "Un, Deux", ("Blunt", "Sloth"), [[],[]]),
"Nailing Fist" : Skill((6, 9, 1), -3, "Nailing Fist", ("Blunt", "Pride"), [[]]),
"Des Coups" : Skill((4, 2, 4), -3, "Des Coups", ("Blunt", "Gloom"), [[] for _ in range(4)]),

"Downward Cleave" : Skill((4, 7, 1), 2, "Downward Cleave", ("Blunt", "Pride"), [[]]),
"Dual Strike" : Skill((4, 4, 2), 2, "Dual Strike", ("Slash", "Sloth"), [[],[]], [skc.CoinPower(1, 0)]),
"Whirlwind" : Skill((6, 4, 2), 2, "Whirlwind", ("Blunt", "Lust"), [[],[]], [skc.CoinPower(2, 0)]),

"Bat Bash" : Skill((4, 7, 1), 0, "Bat Bash", ("Blunt", "Envy"), [[]]),
"Smackdown" : Skill((4, 4, 2), 0, "Smackdown", ("Blunt", "Wrath"), [[], []]),
"Upheaval" : Skill((4, 8, 2), 0, "Upheaval", ("Blunt", "Lust"), [[skc.OnHeadsHit(SkillEffect('coin_power', 'add', 2))], []]),

"Loggerhead" : Skill((4, 7, 1), -1, "Loggerhead", ("Blunt", "Wrath"), [[]]),
"Slide" : Skill((6, 9, 1), -1, "Slide", ("Blunt", "Gluttony"), [[]]),
"Shield Bash" : Skill((8, 12, 1), -1, "Shield Bash", ("Blunt", "Gloom"), [[]]),

"Strike Down" : Skill((4, 7, 1), 0, "Strike Down", ("Slash", "Gluttony"), [[]]),
"Axe Combo" : Skill((4, 4, 2), 0, "Axe Combo", ("Slash", "Pride"), [[],[]]),
"Slay" : Skill((4, 2, 4), 0, "Slay", ("Slash", "Wrath"), [[],[],[],[skc.AddXForEachY(0.2, 'dynamic', 6, 'enemy.bleed', 0, 0.2)]],[skc.BasePowerUp(1, 0)]),

"Downward Swing" : Skill((4, 7, 1), 3, "Downward Swing", ("Slash", "Pride"), [[]]),
"Halberd Combo" : Skill((4, 2, 3), 3, "Halberd Combo", ("Slash", "Wrath"), [[],[],[]], [skc.DynamicBonus(0.3, 0)]),
"Ravaging Cut" : Skill((5, 3, 3), 3, "Ravaging Cut", ("Slash", "Envy"), [[],[],[]], [skc.BasePowerUp(1, 0)]),

"Pulled Blade" : Skill((3, 2, 3), 3, "Pulled Blade", ("Pierce", "Sloth"), [[],[],[]]),
"Backslash" : Skill((5, 4, 2), 3, "Backslash", ("Slash", "Pride"), [[], []], [skc.DynamicBonus(0.2, 0)]),
"Piercing Thrust" : Skill((7, 14, 1), 3, "Piercing Thrust", ("Pierce", "Gloom"), [[]], [skc.DynamicBonus(0.2, 0)]),

"Swipe" : Skill((4, 7, 1), -1, "Swipe", ("Slash", "Gloom"), [[]]),
"Jag" : Skill((5, 10, 1), -1, "Jag", ("Pierce", "Gluttony"), [[]]),
"Chop Up" : Skill((6, 4, 2), -1, "Chop Up", ("Pierce", "Sloth"), [[], []], [skc.DynamicBonus(0.1, 0)]),

"Flaming Fists" : Skill((3, 4, 2), 2, "Red Kick", ("Blunt", "Lust"), [[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))],[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))]], 
[skc.DAddXForEachY(1, "coin_power", 3, "enemy.statuses.Burn.potency", 0, 2, 0)]),
"Fiery Knifehand-Combust" : Skill((4, 4, 3), 2, "Frontal Assault", ("Blunt", "Wrath"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHeadsHit(skc.ApplyStatus('Burn', 0, 1)),skc.OnHit(skc.LiuDyaS2Burn())]],
[skc.DAddXForEachY(1, "coin_power", 6, "enemy.statuses.Burn.potency", 0, 2, 0)]),
"Pinpoint Blitz" : Skill((4, 3, 4), 2, "Inner Gate Elbow Strike", ("Blunt", "Envy"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 0, 2))], 
 [skc.LiuDyaS3Burst()]], [skc.DAddXForEachY(1, "coin_power", 6, "enemy.statuses.Burn.potency", 0, 1, 0), skc.LiuDyaS3Bonus()]),

"Striker's Stance" : Skill((6, 7, 1), 5, "Striker's Stance", ("Slash", "Pride"), [[]], [skc.GainPoise(0, 2)]),
"Heel Turn" : Skill((7, 2, 2), 5, "Heel Turn", ("Slash", "Wrath"), [[], []]),
"Flank Trust" : Skill((8, 2, 3), 5, "Flank Trust", ("Slash", "Envy"), [[],[],[skc.OnCritRoll(skc.DynamicBonus(0.7))]]),

"Beheading" : Skill((3, 4, 2), 2, "Beheading", ("Slash", "Wrath"), [[],[skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 3, 0))]], 
                    [skc.AddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Sinking.potency', 0, 2)]),
"Memorial Procession" : Skill((5, 3, 3), 2, "Memorial Procession", ("Slash", "Envy"), 
[[], [skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 2, 0))], [skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 3, 0))]],
[skc.AddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Sinking.potency', 0, 2), skc.ResetAttackWeight(), 
 skc.AddXForEachY(1, 'unit.atk_weight', 4, 'unit.coffin', 0, 2), skc.AddXForEachY(1, 'unit.atk_weight', 1, 'unit.horse', 0, 1)]),
"Requiem" : Skill((6, 6, 2), 5, "Requiem", ("Blunt", "Gloom"), 
[[skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 0, 4)), skc.HuntCliffS3Sinking()], [skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 3, 0))]],
[skc.HealSP(10, -1, 0), skc.AddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Sinking.potency', 0, 4), skc.AddXForEachY(0.12, 'dynamic', 1, 'unit.coffin', 0, 1.2),
SkillEffect('unit.coffin', 'add', 1), SkillEffect('unit.coffin', 'add', 3, condition=1)]),
"O Dullahan…!" : Skill((5, 4, 2), 3, "O Dullahan…!", ("Slash", "Lust"), [[], [skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 2, 1))]],
                       [skc.AddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Sinking.potency', 0, 2)]),
"Lament, Mourn, and Despair" : Skill((31, -13, 2), 5, "Lament, Mourn, and Despair", ("Blunt", "Gloom"), 
[[skc.OnHit(skc.ApplyStatus(StatusNames.sinking, 5, 2))], [skc.HuntCliffS4Bonus(), skc.HuntCliffS4Regen()]], 
[skc.LoseSP(15), skc.AddXForEachY(1, 'base', 5, 'enemy.statuses.Sinking.potency', 0, 4), skc.AddXForEachY(0.1, 'dynamic', 1, 'unit.coffin', 0, 1), skc.HuntCliffSpBonus(),
 skc.AddXForEachY(0.2, 'dynamic', 1, 'unit.horse', 0, 0.6), SkillEffect('unit.coffin', 'add', 2), SkillEffect('unit.coffin', 'add', 4, condition=0)]),

"Rip(Meursault)" : Skill((5, 6, 1), 0, "Rip(Meursault)", ("Slash", "Envy"), [[skc.OnHit(skc.GainCharge(3))]], [skc.GainCharge(3)]),
"Energy Cycle(Meursault)" : Skill((5, 2, 3), 0, "Energy Cycle(Meursault)", ("Slash", "Gloom"), [[], [], [skc.OnHit(skc.ConsumeCharge(3))]], 
                       [skc.DAddXForEachY(1, 'coin_power', 5, 'unit.charge', 0, 1)]),
"Energy Current" : Skill((5, 2, 4), 0, "Energy Current", ("Slash", "Pride"), [[skc.OnHit(skc.ConsumeChargeTrigger(2, skc.OffenseLevelUp(2)))] for _ in range(4)],
                         [skc.DAddXForEachY(1, 'coin_power', 5, 'unit.charge', 0, 1)]),

"Energy Cycle" : Skill((4, 8, 1), -1, "Energy Cycle", ("Blunt", "Envy"), [[skc.OnHit(skc.GainCharge(2))]], [skc.GainCharge(2)]),
"Leap(Faust)" : Skill((6, 4, 2), -1, "Leap(Faust)", ("Blunt", "Gloom"), [[skc.OnHit(skc.GainCharge(3))], [skc.ConsumeCharge(3)]], [skc.GainCharge(3)]),
"Overcharge" : Skill((6, 3, 3), -1, 'Overcharge', ("Blunt", "Wrath"), [[],[],[skc.OnHit(skc.ConsumeCharge(5))]]),

"40S-2 Activation" : Skill((3, 4, 2), 0, "40S-2 Activation", ("Slash", "Wrath"), [[skc.OnHit(skc.GainCharge(2))] for _ in range(2)],
                           [skc.ConsumeChargeTrigger(5, skc.CoinPower(1))]),
"Photoelectric Mark" : Skill((4, 3, 3), 1, "Photoelectric Mark", ("Blunt", "Envy"), 
[[skc.OnHit(skc.AddXForEachY(2, 'ol', 5, 'coin_power', 0, 2))], [skc.OnHit(skc.AddXForEachY(2, 'ol', 5, 'coin_power', 0, 2))], []],
[skc.MCFaustS2ChargeGain(), skc.ConsumeChargeTrigger(10, skc.CoinPower(2))]),
"Photoelectric Harpoon" : Skill((5, 2, 4), 2, "Photoelectric Harpoon", ("Blunt", "Gloom"), 
[[], [skc.OnHit(skc.GainCharge(7))], [skc.OnHit(skc.MCHeathS3ChargeGain())], []], [skc.DAddXForEachY(1, 'coin_power', 2, 'unit.charge_potency', 0, 2)]),

"Impale" : Skill((3, 4, 2), 2, "Impale", ("Pierce", "Pride"), [[], []], [skc.GainPoise(0,2)]),
"Relentless Stabbing" : Skill((4, 4, 2), 2, "Relentless Stabbing", ("Pierce", "Envy"), [[skc.OnHit(skc.GainPoise(2, 0))], [skc.OnCrit(skc.PeqSangReuseCoin(3))]],
                              [skc.GainPoise(0, 2)]),
"Ambush" : Skill((4, 6, 2), 2, "Ambush", ("Pierce", "Gluttony"), [[skc.GainPoise(0, 2)], []], 
                 [skc.GainPoise(5, 0), skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency', 0, 1)]),

"Standoff" : Skill((4, 3, 2), 0, "Standoff", ("Slash", "Sloth"), [[],[]], [SkillEffect('unit.def_level', 'add', 2)]),
"Flexible Suppression" : Skill((3, 3, 4), 0, "Flexible Suppression", ("Slash", "Gluttony"), 
[[],[],[],[skc.AddXForEachY(0.4, 'dynamic', 6, 'unit.def_level', 0, 0.4)]], [SkillEffect('unit.def_level', 'add', 3)]),
"Guardian" : Skill((5, 3, 3), 0, "Guardian", ("Slash", "Gloom"), [[],[],[]], 
[SkillEffect('unit.def_level', 'add', 3), skc.AddXForEachY(0.5, 'dynamic', 10, 'unit.def_level', 0, 0.5), skc.AddXForEachY(1, 'coin_power', 6, 'unit.def_level', 0, 3)]),

"Remise" : Skill((4, 3, 2), 4, "Remise", ("Pierce", "Lust"), [[], []], 
[SkillEffect('unit.haste', 'add', 1, condition=0), skc.AddXForEachY(2, 'coin_power', 7, 'unit.speed', 0, 2)]),
"Flèche" : Skill((5, 5, 2), 4, "Flèche", ("Pierce", "Gloom"), [[], []],
[SkillEffect('unit.haste', 'add', 2), skc.AddXForEachY(0.05, 'dynamic', 1, 'unit.clash_count', 0, 0.5)]),
"Salut!" : Skill((6, 6, 2), 4, "Salut!", ("Pierce", "Pride"), [[], []],
[skc.AddXForEachY(3, 'coin_power', 10, 'unit.speed', 0, 3), skc.AddXForEachY(0.1, 'dynamic', 1, 'unit.clash_count', 0, 1)]),

"Impede the Intruder" : Skill((5, 6, 1), 0, "Impede the Intruder", ("Slash", "Pride"), [[]], 
    [skc.AddXForEachY(3, 'coin_power', 5, "enemy.rupture", 0, 3)]),
"Decay Blade" : Skill((6, 5, 2), 0, "Decay Blade", ("Blunt", "Gluttony"), [[], []]),
"Excise Target" : Skill((8, 4, 2), 0, "Excise Target", ("Slash", "Sloth"), 
[[], [skc.AddXForEachY(0.05, 'dynamic', 1, 'unit.ampule', 0, 0.2)]], [skc.CoinPower(2 ,0)]),

"Weighty Bash" : Skill((5, 6, 1), 0, "Weighty Bash", ("Blunt", "Envy"), [[skc.OnHit(skc.GainCharge(2))]], 
[skc.GainCharge(2), skc.AddXForEachY(1, 'base', 10, 'unit.charge', 0, 1), skc.AddXForEachY(0.25, 'dynamic', 7, 'unit.speed', 0, 0.25)]),
"Demolish" : Skill((5, 3, 3), 0, "Demolish", ("Slash", "Gloom"), [[skc.OnHit(skc.GainCharge(4))], [],[]], [skc.GainCharge(4)]),
"Rhino Ram" : Skill((6, 3, 3), 0, "Rhino Ram", ("Slash", "Lust"), 
[[skc.ConsumeCharge(2),skc.ConsumeCharge(3)],[skc.ConsumeCharge(2),skc.ConsumeCharge(3)],[]], 
[skc.AddXForEachY(2, 'coin_power', 10, 'unit.charge', 0, 2)]),

"Flying Sword" : Skill((3, 4, 2), 1, "Flying Sword", ("Slash", "Envy"), [[skc.OnHit(skc.GainPoise(2, 0))], []], [skc.GainAdditionalPoise(3, 0, 0)]),
"Flashing Strike" : Skill((5, 4, 2), 1, "Flashing Strike", ("Slash", "Lust"), 
[[skc.OnHit(skc.GainPoise(0, 2))], [skc.OnHit(skc.GainPoise(0, 2)), skc.ReuseCoin(2, 0)]]),
"Catch Breath" : Skill((6, 6, 2), 1, "Catch Breath", ("Slash", "Wrath"), 
    [[skc.OnHeadsHit(skc.GainPoise(2, 0)), skc.OnCritRoll(skc.AddXForEachY(0.5, 'dynamic', 5, 'unit.poise_count', 0, 0.5, duration=1))],
     [skc.OnCritRoll(skc.AddXForEachY(0.5, 'dynamic', 5, 'unit.poise_count', 0, 0.5, duration=1))]]),
    
"Cleave" : Skill((4, 7, 1), 0, "Cleave", ("Slash", "Lust"), [[]]),
"Cloud Cutter" : Skill((5, 4, 2), 0, "Cloud Cutter", ("Slash", "Pride"), [[],[skc.ReuseCoin(2, 0)]]),
"Cloudburst" : Skill((7, 2, 3), 0, "Cloudburst", ("Slash", "Sloth"), [[], [], []]),

"Careful Obstruction" : Skill((4, 2, 2), -2, "Careful Obstruction", ("Blunt", "Wrath"), [[skc.OnHit(skc.GainPoise(0, 1))] for _ in range(2)]),
"Focused Defense" : Skill((6, 4, 2), -2, "Focused Defense", ("Blunt", "Sloth"), 
[[skc.OnHit(skc.GainPoise(0, 2))], []], [skc.GainPoise(0, 2), skc.AddXForEachY(2, 'unit.poise_count', 15, 'unit.shield', 0, 2)]),
"Subdue Threat" : Skill((5, 2, 3), -2, "Subdue Threat", ("Blunt", "Gloom"), [[], [], [skc.OnCrit(SkillEffect('enemy.next_frag', 'add', 1))]],
[skc.AddXForEachY(2, 'coin_power', 15, 'unit.shield', 0, 2)]),

"Baton" : Skill((4, 6, 1), -2, "Baton", ("Blunt", "Gloom"), [[]]),
"Suppress" : Skill((6, 2, 2), -2, "Suppress", ("Blunt", "Wrath"), [[], []]),
"Strong Strike" : Skill((7, 13, 1), -2, "Strong Strike", ("Blunt", "Sloth"), [[]]),

"Lenticular Rend" : Skill((5, 5, 1), 1, "Lenticular Rend", ("Slash", "Sloth"), [[]]),
"Shadow Cloud" : Skill((5, 5, 2), 2, "Shadow Cloud", ("Slash", "Lust"), [[], []]),
"Shadowcloud Shattercleave" : Skill((4, 3, 3), 2, "Shadowcloud Shattercleave", ("Slash", "Gloom"), [[], [], []], [skc.CoinPower(1, 0)]),

"Negotiation Start" : Skill((4, 3, 2), 2, "Negotiation Start", ("Pierce", "Sloth"), 
[[skc.OnHit(skc.GainPoise(0, 1)), skc.OnCrit(skc.ApplyStatus('Bleed', 2, 0))], [skc.OnCrit(skc.ApplyStatus('Bleed', 2, 0))]], 
[skc.GainPoise(3, 0), skc.DAddXForEachY(1, 'coin_power', 7, 'enemy.statuses.Bleed.potency', 0, 1)]),
"Unilateral Business" : Skill((4, 6, 2), 3, "Unilateral Business", ("Pierce", "Pride"), 
[[skc.OnHit(skc.GainPoise(4, 0)), skc.OnCrit(skc.ApplyStatus('Bleed', 2, 0))], [skc.OnHit(skc.ApplyStatus('Bleed', 3, 0)), skc.OnCrit(skc.ApplyStatus('Bleed', 2, 0))]],
[skc.GainPoise(0, 3), skc.DAddXForEachY(1, 'coin_power', 7, 'enemy.statuses.Bleed.potency', 0, 2)]),
"Foregone Conclusion" : Skill((5, 6, 2), 5, "Foregone Conclusion", ("Pierce", "Gloom"), 
[[skc.OnCrit(skc.ApplyStatus('Bleed', 0, 2))], [skc.OnCritRoll(skc.DynamicBonus(1)), skc.PirateGregS3Bonus()]],
[skc.AddXForEachY(1, 'unit.poise_potency', 3, 'enemy.statuses.Bleed.potency', 0, 10), skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency', 0, 3)]),

"Sharp Edge" : Skill((5, 6, 1), 2, "Sharp Edge", ("Slash", "Gloom"), [[skc.OnHit(skc.GainPoise(4, 0))]], 
[skc.AddXForEachY(2, 'coin_power', 4, 'unit.poise_potency', 0, 2)]),
"Scattering Slash" : Skill((6, 3, 2), 2, "Scattering Slash", ("Slash", "Lust"), [[skc.OnHit(skc.GainPoise(2, 0))], [skc.OnHit(skc.GainPoise(3, 0))]], 
[skc.GainPoise(0, 2), skc.DAddXForEachY(2, 'coin_power', 5, 'unit.poise_potency', 0, 2)]),
"Sky-clearing Cut" : Skill((7, 18, 1), 2, "Sky-clearing Cut", ("Slash", "Pride"), [[skc.OnCritRoll(skc.AddXForEachY(1, 'dynamic', 10, 'unit.poise_potency', 0, 1))]],
[skc.AddXForEachY(1, 'crit_odds_mult', 6, 'enemy.bleed', 0, 1)]),

"Moonlit Blade Dance" : Skill((3, 2, 3), 2, "Moonlit Blade Dance", ("Slash", "Sloth"), 
[[], [skc.OnHeadsHit(skc.GainPoise(1, 0))], [skc.OnCrit(skc.ApplyStatusCount(StatusNames.red_plum_blossom, 1))]], 
[skc.DAddXForEachY(1, 'coin_power', 5, 'unit.poise_potency', 0, 1)]),
"Acupuncture" : Skill((4, 6, 2), 2, "Acupuncture", ("Pierce", "Pride"), 
[[skc.OnHit(skc.GainPoise(0, 2)), skc.OnCritRoll(skc.DynamicBonus(0.3))], [skc.OnHit(skc.ApplyStatusCount(StatusNames.red_plum_blossom, 2))]],
[skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency', 0, 1), skc.GainPoise(0, 2)]),
"Red Plum Blossoms Scatter" : Skill((5, 6, 2), 2, "Red Plum Blossoms Scatter", ("Slash", "Gloom"),
[[skc.OnCrit(skc.ApplyStatusCount(StatusNames.red_plum_blossom, 5)), skc.OnCrit(skc.AddXForEachY(0.1, 'dynamic', 10, 'enemy.statuses.Red Plum Blossom.count', 0, 0.1))], 
[skc.OnCrit(skc.ApplyStatusCount(StatusNames.red_plum_blossom, 5))]],
[skc.DAddXForEachY(0.03, 'dynamic', 1, 'enemy.statuses.Red Plum Blossom.count', 0, 0.3), skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency', 0, 3),
skc.OnCrit(skc.ApplyStatusCount(StatusNames.red_plum_blossom, 1), duration=-1), skc.BlFaustS3Conversion(condition=0)]),

"Dimensional Slit" : Skill((5, 6, 1), 3, "Dimensional Slit", ("Slash", "Sloth"), 
[[skc.OnHit(skc.GainCharge(2))]], [skc.GainCharge(2), skc.AddXForEachY(2, 'coin_power', 10, 'unit.charge', 0, 2)]),
"Energy Cycle" : Skill((5, 5, 2), 3, "Energy Cycle", ("Pierce", "Gluttony"), [[],[]], 
[skc.GainCharge(7), skc.DAddXForEachY(1, 'coin_power', 10, 'unit.charge', 0, 1)]),
"Dimensional Rift" : Skill((5, 4, 3), 5, "Dimensional Rift", ("Pierce", "Gloom"), [[] for _ in range(3)], [skc.WarpSangS3CoinPower()]),

"Rev Up" : Skill((3, 4, 2), 1, "Rev Up", ("Slash", "Gluttony"), [[], []]),
"Grease Chains" : Skill((4, 12, 1), 1, "Grease Chains", ("Slash", "Envy"), [[]]),
"Let's Grind 'Em" : Skill((4, 3, 3), 1, "Let's Grind 'Em", ("Slash", "Gloom"), 
[[],[skc.DynamicBonus(0.1, 0)],[]], [skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.tremor_count', 0, 1)]),

"Marche" : Skill((3, 4, 2), -1, "Marche", ("Pierce", "Pride"), [[skc.OnHit(skc.GainPoise(0, 1))], [skc.OnHit(skc.GainPoise(0, 1))]]),
"Punition" : Skill((4, 5, 2), -1, "Punition", ("Pierce", "Gloom"), [[skc.OnHit(skc.GainPoise(2, 0))], []], [skc.GainPoise(0, 2), skc.CoinPower(2, 0)]),
"Balestra Fente" : Skill((8, 14, 1), -1, "Balestra Fente", ("Pierce", "Lust"), [[skc.OnCritRoll(skc.DynamicBonus(0.7))]], 
[skc.AddXForEachY(1, 'unit.poise_potency', 1, 'unit.clash_count', 0, 10), skc.AddXForEachY(4, 'base', 7, 'unit.poise_potency', 0, 4)]),

"Predictive Analysis" : Skill((4, 3, 2), 3, "Predictive Analysis", ("Slash", "Envy"), [[], [skc.OnHit(skc.ApplyStatus(StatusNames.rupture, 3, 0))]],
[skc.DAddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Rupture.potency', 0, 2)]),
"Dissect Target" : Skill((4, 4, 3), 3, "Dissect Target", ("Slash", "Gloom"), 
[[skc.OnHit(skc.ApplyStatus(StatusNames.rupture, 3, 0))], [skc.AddXForEachY(1, 'enemy.analyzed', 6, 'enemy.statuses.Rupture.potency', 0, 1)], []],
[skc.ApplyStatus(StatusNames.rupture, 0, 3, 0) ,skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency', 0, 2)]),
"Profiling" : Skill((5, 4, 3), 3, "Profiling", ("Slash", "Gluttony"), [[], [skc.OnHit(skc.ApplyStatus(StatusNames.rupture, 3, 0))], []],
[skc.AddXForEachY(0.1, 'dynamic', 3, 'enemy.statuses.Rupture.potency', 0, 0.5), skc.ApplyStatus(StatusNames.rupture, 0, 2, 0)]),

"Dotting" : Skill((3, 4, 2), 0, "Dotting", ("Pierce", "Lust"), [[skc.ApplyStatus('Bleed', 1, 0)] for _ in range(2)], 
[skc.AddXForEachY(1, 'coin_power', 10, 'enemy.statuses.Bleed.potency')]),
"Sanguine Painting" : Skill((5, 4, 2), 0, "Sanguine Painting", ("Pierce", "Wrath"), [[], [skc.RingOutisReuse(), skc.OnHit(skc.ApplyStatusCount('Bleed', 1))]]),
"Artwork Inspection" : Skill((4, 6, 2), 2, "Artwork Inspection", ("Pierce", "Gluttony"), 
[[], [skc.OnHit(skc.ApplyStatus('Bleed', 3, 0)), skc.OnHit(skc.RingRandomStatus(3, 0))]], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency'), skc.RingOutisS3Bonus()]),

"Fierce Charge" : Skill((3, 7, 1), 2, "Fierce Charge", ("Slash", "Gloom"), 
[[skc.OnHit(skc.ApplyStatus("Burn", 2, 0)), skc.ReuseCoinConditional(1, SkillConditionals.HasEgoHeadsHit, 0)]]),
"Sunset Blade" : Skill((5, 3, 3), 2, 'Sunset Blade', ("Slash", "Envy"), [[skc.OnHit(skc.ApplyStatusCount("Burn", 1))] for _ in range(3)],
[skc.ResetAttackWeight(), SkillEffect('unit.atk_weight', 'add', 1, condition=0), skc.AddXForEachY(1, 'unit.atk_weight', 45, 'unit.sp', condition=0)]),
"Stigmatize" : Skill((4, 7, 2), 3, "Stigmatize", ("Pierce", "Wrath"), [[skc.OnHit(skc.ApplyStatus('Burn', 3, 0))] for _ in range(2)], 
[skc.DAddXForEachY(1, 'coin_power', 7, 'enemy.statuses.Burn.potency', 0, 2)]),
"Blazing Strike" : Skill((13, 15, 1), 5, "Blazing Strike", ("Slash", "Wrath"), 
[[skc.AddXForEachY(0.04, 'dynamic', 1, 'enemy.statuses.Burn.potency', 0, 1.2), skc.OnHit(skc.ApplyStatus("Burn", 10, 0))]],
[skc.AddXForEachY(2, 'coin_power', 4, 'enemy.all_burn', 0, 8), skc.DawnClairS4Bonus()]),

"Ignition" : Skill((3, 4, 2), 3, "Ignition", ("Blunt", "Wrath"), [[skc.OnHit(skc.NextTurnDarkFlame(1))], [skc.OnHit(skc.MBOutisBurn())]],
[skc.DAddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Burn.potency', 0, 3)]),
"Detonate Magic Bullet" : Skill((4, 6, 2), 3, "Detonate Magic Bullet", ("Blunt", "Pride"), 
[[skc.OnHit(skc.MBOutisS2BulletGain()), skc.OnHit(skc.NextTurnDarkFlameBullet())], [skc.OnHit(skc.MBOutisBurn())]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.potency', 0, 3)]),    
"Magic Bullet Fire" : Skill((15, 4, 1), 5, "Magic Bullet Fire", ("Pierce", "Pride"), [[skc.NextTurnDarkFlameBullet()]], [skc.MBOutisS3Effects()]),

"Focus Strike" : Skill((5, 6, 1), 3, "Focus Strike", ("Pierce", "Gluttony"), [[]], [skc.DAddXForEachY(0.2, 'dynamic', 2, 'enemy.statuses.Bleed.count', 0, 0.2)]),
"Clean Up" : Skill((5, 5, 2), 3, "Clean Up", ("Pierce", "Pride"), [[skc.OnHit(skc.ApplyStatus('Bleed', 2, 0))], [skc.OnHit(skc.ApplyStatus('Bleed', 0, 3))]],
[skc.DAddXForEachY(0.2, 'dynamic', 5, 'enemy.statuses.Bleed.count', 0, 0.2)]),
"Lenticular Swirl" : Skill((8, 4, 2), 3, "Lenticular Swirl", ("Pierce", "Lust"), [[skc.OnHeadsHit(skc.ApplyStatus('Bleed', 2, 0))], 
[skc.OnHit(skc.ApplyStatus('Bleed', 0, 3))]], [skc.DAddXForEachY(0.4, 'dynamic', 9, 'enemy.statuses.Bleed.count', 0, 0.4)]),

"Draw Of The Sword(Don)" : Skill((3, 4, 2), 1, "Draw Of The Sword(Don)", ("Slash", "Pride"), [[skc.OnHit(skc.GainPoise(1, 0))] for _ in range(2)],
[skc.DAddXForEachY(1, 'coin_power', 5, 'unit.poise_potency'), skc.GainPoise(0, 2)]),
"Blade Arc" : Skill((4, 5, 2), 1, "Blade Arc", ("Slash", "Envy"), [[skc.OnHit(skc.GainPoise(2, 0))], [skc.OnCrit(skc.GainPoise(4, 0), 0)]],
[skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency'), skc.GainPoise(0, 2)]),
"Fare Thee Well!" : Skill((4, 3, 3), 4, "Fare Thee Well!", ("Slash", "Sloth"), 
[[], [], [skc.OnCritRoll(skc.DynamicBonus(0.3)), skc.OnCrit(skc.GainPoise(0, 4), 0), skc.BlDonS3Bonus()]],
[skc.GainPoise(5, 0), skc.DAddXForEachY(1, 'coin_power', 10, 'unit.poise_potency')]),

"Ready to Crush" : Skill((4, 3, 2), 3, "Ready to Crush", ("Pierce", "Pride"), 
[[skc.OnHit(skc.GainTremor(3))], [skc.OnHit(skc.ApplyStatusCount('Sinking', 2))]], [skc.GainTremor(3)]),
"Explosive Blast" : Skill((5, 5, 2), 3, "Explosive Blast", ("Pierce", "Sloth"), [[skc.OnHit(skc.ApplyStatusCount('Tremor', 3)), skc.OnHit(skc.GainTremor(2))], 
[skc.OnHit(skc.ApplyStatus('Sinking', 6, 0)), skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.defense_level_down, 4))]],
[skc.DAddXForEachY(1, 'coin_power', 5, 'unit.tremor', 0, 1)]),
"Risky Judgement" : Skill((3, 5, 3), 5, "Risky Judgement", ("Pierce", "Gloom"), [[skc.ApplyStatusCount("Sinking", 5)], 
[skc.ApplyStatus("Sinking", 3, 0), skc.ConsumeRessourceTrigger('unit.tremor', 5, 5, skc.ApplyStatusCountNextTurn('Fragile', 1))],
[skc.ApplyStatus("Sinking", 3, 0), skc.ConsumeRessourceTrigger('unit.tremor', 5, 5, skc.ApplyStatusCountNextTurn('Fragile', 2))]],
[skc.DAddXForEachY(0.4, 'dynamic', 6, 'enemy.statuses.Sinking.potency', 0, 0.4), skc.DAddXForEachY(1, 'coin_power', 5, 'unit.tremor', 0, 2)]),
"I Shall Nibble Thee!" : Skill((5, 7, 1), -1, "I Shall Nibble Thee!", ("Slash", "Gluttony"), [[skc.OnHit(skc.ApplyStatusCount('Rupture', 2))]]),
"Flashing Lure" : Skill((4, 3, 3), -1, "Flashing Lure", ("Slash", "Lust"), 
[[skc.OnHit(skc.ApplyStatusPot("Rupture", 1))], [skc.OnHit(skc.ApplyStatusPot("Rupture", 1))], 
[skc.OnHit(skc.ApplyStatusPot("Rupture", 2)), skc.OnHit(skc.LDonS2Rupture())]], [skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),
"Whirlwind Om-Nom-Nom!" : Skill((4, 3, 3), 1, "Whirlwind Om-Nom-Nom!", ("Pierce", "Gloom"), 
[[skc.OnHit(skc.ApplyStatusCount('Rupture', 3))], [], [skc.ReuseCoin(1, 0)]], [skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),

"Magnify Wound" : Skill((5, 5, 1), 0, "Magnify Wound", ("Blunt", "Gluttony"), [[]]),
"Proliferating Talismans" : Skill((4, 3, 3), 0, "Proliferating Talismans", ("Blunt", "Pride"), [[], [], []]),
"Rupturing Talisman" : Skill((5, 6, 2), 0, "Rupturing Talisman", ("Pierce", "Lust"), [[], []]),

"Sweeping Redirection" : Skill((3, 4, 2), 1, "Sweeping Redirection", ("Blunt", "Sloth"), [[skc.OnHit(skc.GainPoise(2, 0))], []],
[skc.CoinPower(1, 0), skc.GainPoise(0, 2)]),
"Housekeeping" : Skill((4, 5, 2), 1, "Housekeeping", ("Slash", "Gluttony"), 
[[skc.OnHit(skc.DefenseLevelDown(2)), skc.OnCrit(skc.DefenseLevelDown(1), 1)], []], [skc.CoinPower(1, 0), skc.GainPoise(0, 2), skc.GainPoise(2, 0, 2)]),
"Restraining Technique" : Skill((4, 3, 3), 3, "Restraining Technique", ("Slash", "Gloom"), 
[[], [], [skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.slash_fragile, 1)), skc.OnCrit(skc.ApplyStatusCountNextTurn(StatusNames.slash_fragile, 1), 1)]],
[skc.CoinPower(1, 0), skc.GainPoise(6, 0)]),

"Energy Cycle" : Skill((3, 4, 2), -1, "Energy Cycle", ("Pierce", "Pride"), [[], []]),
"Cleanup Support" : Skill((6, 4, 2), -1, "Cleanup Support", ("Pierce", "Wrath"), [[], []]),
"Deploy Charge Barrier" : Skill((5, 4, 3), -1, "Deploy Charge Barrier", ("Slash", "Gluttony"), [[], [], []]),

"Extreme Edge" : Skill((4, 6, 1), 1, "Extreme Edge", ("Slash", "Lust"), [[]], [skc.BasePowerUp(2, 0), skc.GainPoise(0, 3)]),
"Flying Sword" : Skill((5, 10, 1), 1, "Flying Sword", ("Pierce", "Wrath"), [[]], [skc.BasePowerUp(2, 0), skc.GainPoise(3, 0)]),
"Flashing Strike" : Skill((5, 6, 2), 1, "Flashing Strike", ("Slash", "Envy"), [[], []], 
[skc.DynamicBonus(0.5), skc.AddXForEachY(2, 'base', 10, 'unit.poise_count', 0, 2), skc.ResetAttackWeight(), SkillEffect('unit.atk_weight', 'add', 1, condition=0)]),

"Order" : Skill((4, 6, 1), -1, "Order", ("Pierce", "Sloth"), [[]], [skc.CoinPower(2, 0)]),
"Onslaught Command" : Skill((6, 10, 1), -1, "Onslaught Command", ("Blunt", "Gluttony"), [[]], [skc.BasePowerUp(1, 0)]),
"Focus" : Skill((6, 16, 1), -1, "Focus", ("Blunt", "Gloom"), [[]]),

"Track" : Skill((3, 4, 2), 1, "Track", ("Pierce", "Wrath"), [[], []], [skc.AddXForEachY(1, 'base', 2, 'unit.statuses.Haste.count')]),
"Goin' First" : Skill((4, 3, 3), 2, "Goin' First", ("Pierce", "Lust"), [[], [], []], 
[skc.GainStatusNextTurn("Haste", 0, 2), skc.AddXForEachY(1, 'coin_power', 6, 'unit.speed')]),
"Rampage" : Skill((4, 2, 4), 3, "Rampage", ("Pierce", "Pride"), [[], [], [], []], 
[skc.AddXForEachY(1, 'coin_power', 6, 'unit.speed'), skc.AddXForEachY(0.005, 'dynamic', 0.01, 'enemy.missing_hp', 0, 0.5)]),

"Catch Breath" : Skill((4, 7, 1), 3, "Catch Breath", ("Slash", "Wrath"), [[]]),
"Dual Strike" : Skill((4, 6, 2), 3, "Dual Strike", ("Slash", "Envy"), [[], []]),
"Overbreathe" : Skill((4, 21, 1), 3, "Overbreathe", ("Slash", "Lust"), [[]], [skc.BasePowerUp(5, 0)]),

"Assault" : Skill((3, 4, 2), 1, "Assault", ("Blunt", "Lust"), [[], []]),
"Stalwart Stance" : Skill((7, 2, 2), 1, "Stalwart Stance", ("Blunt", "Sloth"), [[], []]),
"Perfected Death Fist" : Skill((5, 3, 3), 1, "Perfected Death Fist", ("Pierce", "Wrath"), [[], [], []], [skc.CoinPower(1, 0)]),

"Shove" : Skill((5, 5, 1), 1, "Shove", ("Blunt", "Lust"), [[]], [skc.GainPoise(0, 2), skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency')]),
"T.N." : Skill((4, 5, 2), 1, "T.N.", ("Blunt", "Gluttony"), [[skc.OnHit(skc.GainPoise(2, 0))], [skc.OnHit(skc.GainPoise(1, 0))]], 
[skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency')]),
"O.O.F." : Skill((4, 3, 3), 3, "O.O.F.", ("Pierce", "Pride"), [[skc.OnCrit(skc.GainPoise(0, 1))], [skc.OnCrit(skc.GainPoise(0, 1))], []],
[skc.GainPoise(4, 0), skc.DAddXForEachY(1, 'coin_power', 7, 'unit.poise_potency', 0, 2)]),

"Patrolling" : Skill((3, 4, 2), -1, "Patrolling", ("Pierce", "Envy"), [[], []]),
"Client Protection" : Skill((4, 3, 3), -1, "Client Protection", ("Slash", "Gloom"), [[], [], []]),
"Law and Order" : Skill((6, 5, 2), -1, "Law and Order", ("Slash", "Lust"), [[], []], [skc.CoinPower(1, 0)]),

"Shove" : Skill((4, 6, 1), -1, "Shove", ("Blunt", "Gluttony"), [[]], [skc.BasePowerUp(2, 0)]),
"Quake Rounds" : Skill((4, 3, 3), -1, "Quake Rounds", ("Blunt", "Gloom"), [[], [], []]),
"Suppress" : Skill((4, 2, 4), -1, "Suppress", ("Blunt", "Pride"), [[], [], [], []], [skc.CoinPower(1, 0)]),

"Cackle" : Skill((4, 3, 2), 4, "Cackle", ("Pierce", "Envy"), [[skc.OnHit(skc.ApplyStatusCount("Nails", 1))], []]),
"The Gripping" : Skill((4, 4, 3), 4, "The Gripping", ("Pierce", "Lust"), 
[[skc.OnHit(skc.ApplyStatusCount("Nails", 2))], [skc.OnHit(skc.ApplyStatusCount("Nails", 3))], [skc.OnHit(skc.ApplyStatusCountNextTurn("Gaze", 1))]]),
"Execution" : Skill((6, 2, 3), 4, "Execution", ("Blunt", "Pride"), 
[[skc.OnHit(skc.ApplyStatusCount("Nails", 2))], [skc.OnHeadsHit(skc.ApplyStatusCount("Nails", 2))], 
[skc.AddXForEachY(0.7, 'dynamic', 5, 'enemy.statuses.Nails.count', 0, 0.7)]]),

"It's Heavy...!" : Skill((4, 6, 1), -1, "It's Heavy...!", ("Blunt", "Gloom"), [[]]),
"It's Churning...!" : Skill((5, 4, 2), -1, "It's Churning...!", ("Blunt", "Wrath"), [[], []]),
"Corrosive Splash" : Skill((6, 16, 1), -1, "Corrosive Splash", ("Blunt", "Gluttony"), [[]]),

"Flèche" : Skill((5, 7, 1), 0, "Flèche", ("Pierce", "Gloom"), [[]]),
"Riposte" : Skill((5, 4, 2), 0, "Riposte", ("Pierce", "Gluttony"), [[], [skc.ApplyStatusCountNextTurn("Fragile", 1)]]),
"Moulinet" : Skill((5, 3, 3), 0, "Moulinet", ("Blunt", "Sloth"), [[], [], [skc.ApplyStatusCountNextTurn(StatusNames.pierce_fragile, 3)]]),

"Bat Strike" : Skill((5, 6, 1), 1, "Bat Strike", ("Blunt", "Lust"), [[skc.OnHit(skc.ApplyStatus("Rupture", 2, 0))]]),
"Smackdown" : Skill((4, 5, 2), 1, "Smackdown", ("Pierce", "Wrath"), [[], [skc.OnHit(skc.ApplyStatus("Rupture", 2, 0))]],
[skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency'), skc.ApplyStatusCount("Rupture", 2, 0)]),
"Relentless" : Skill((4, 2, 4), 3, "Relentless", ("Blunt", "Gluttony"), [[], [], [], [skc.OnHit(skc.ApplyStatus("Rupture", 4, 0))]],
[skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),

"Fierce Assault" : Skill((2, 1, 4), 1, "Fierce Assault", ("Blunt", "Gloom"), [[], [skc.GainTremor(2)], [], [skc.GainTremor(2)]],
[skc.DAddXForEachY(1, 'coin_power', 10, 'unit.tremor')]),
"Steady..." : Skill((4, 12, 1), 1, "Steady...", ("Pierce", "Envy"), [[]], [skc.GainTremor(6)]),
"Gamble" : Skill((4, 6, 2), 1, "Gamble", ("Pierce", "Gluttony"), [[skc.MolarClairS3Spend()], []], [skc.DAddXForEachY(1, 'coin_power', 10, 'unit.tremor', 0, 2)]),

"Gawky Nailing" : Skill((3, 4, 2), 0, "Gawky Nailing", ("Pierce", "Envy"), [[], []]),
"Puri…fy!" : Skill((6, 8, 1), 0, "Puri…fy!", ("Blunt", "Gloom"), [[]]),
"Infirm Retribution" : Skill((4, 4, 3), 0, "Infirm Retribution", ("Blunt", "Lust"), [[skc.OnHit(skc.NCliffS3Bonus())] for _ in range(3)]),

"Bludgeon" : Skill((5, 6, 1), 5, "Bludgeon", ("Blunt", "Pride"), [[]], [skc.CoinPower(2, 0)]),
"Thrust" : Skill((6, 1, 2), 5, "Thrust", ("Blunt", "Gluttony"), [[], []], [skc.CoinPower(2, 0)]),
"Suppress" : Skill((7, 2, 2), 5, "Suppress", ("Blunt", "Envy"), [[skc.OnHit(skc.DefenseLevelDown(4))], []], [skc.CoinPower(3, 0, 1)]),

"Warm Up" : Skill((3, 4, 2), 0, "Warm Up", ("Blunt", "Gloom"), [[], [skc.OnHit(skc.ApplyStatus('Burn', 3, 0))]]),
"Flowing Flame" : Skill((6, 2, 2), 0, "Flowing Flame", ("Blunt", "Lust"), 
[[skc.OnHit(skc.AddStatusPotForEachY(1, 'Burn', 1, 'enemy.statuses.Burn.potency')), skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], 
[skc.OnHit(skc.ApplyStatusCount('Burn', 1, condition = i)) for i in range(3)]], [skc.DAddXForEachY(2, 'coin_power', 6, 'enemy.statuses.Burn.potency', 0, 2)]),
"Crimson Blaze Fist" : Skill((5, 6, 2), 0, "Crimson Blaze Fist", ("Blunt", "Wrath"), 
[[skc.OnHit(skc.AddStatusPotForEachY(1, 'Burn', 1, 'enemy.statuses.Burn.potency')), skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], []],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.count')]),

"Stay Calm" : Skill((3, 4, 2), -2, "Stay Calm", ("Pierce", "Lust"), [[], []], [skc.GainTremor(2), skc.AddXForEachY(1, 'coin_power', 5, 'unit.tremor')]),
"Gamble(Yi Sang)" : Skill((4, 12, 1), 2, "Gamble", ("Blunt", "Sloth"), [[]]),
"Grinding the Molars" : Skill((4, 3, 3), 5, "Grinding the Molars", ("Blunt", "Wrath"), 
[[skc.OnHit(SkillEffect('enemy.tremor', 'add', 4)), skc.OnHit(skc.AddXForEachY(-1, 'def_level_mod', 4, 'enemy.tremor', -5, 0))], [], []], 
[skc.ConsumeRessourceTrigger('unit.tremor', 10, 10, skc.CoinPower(2))]),

"To Me!" : Skill((4, 4, 2), 3, "To Me!", ("Pierce", "Envy"), [[], []]),
"Pursue Them to the End!" : Skill((4, 4, 3), 3, "Pursue Them to the End!", ("Pierce", "Pride"), [[], [], []], []),
"Harpoon of Obsession" : Skill((4, 3, 4), 3, "Harpoon of Obsession", ("Pierce", "Wrath"), [[], [], [], []],
[skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.bleed', 0, 2), skc.AddXForEachY(0.003, 'dynamic', 0.01, 'enemy.missing_hp', 0, 0.3)]),

"Single-point Stab" : Skill((4, 2, 2), 5, "Single-point Stab", ("Blunt", "Wrath"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0)), skc.OnHeadsHit(skc.ApplyStatus('Burn', 1, 0))] for _ in range(2)],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.potency')]),
"Rush Down" : Skill((5, 2, 3), 5, "Rush Down", ("Blunt", "Lust"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 3, 0))]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.potency')]),
"Perfected Palm Strike" : Skill((4, 2, 4), 5, "Perfected Palm Strike", ("Blunt", "Sloth"), [[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], 
[skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 1, 0))], [skc.OnHit(skc.ApplyStatus('Burn', 3, 0))]],
[skc.DAddXForEachY(0.1, 'dynamic', 6, 'enemy.statuses.Burn.potency', 0, 0.1)]),

"Confiscation" : Skill((3, 4, 2), 1, "Confiscation", ('Slash', 'Gloom'), [[], [skc.OnHit(skc.ApplyStatus('Sinking', 2))]], 
[skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Sinking.potency')]),
"Interloper Reception" : Skill((4, 5, 2), 2, "Interloper Reception", ('Blunt', 'Lust'), 
[[], [skc.OnHit(skc.ApplyStatusCount('Sinking', 3))]], [skc.AddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Sinking.count')]),
"RA4: Heartseal" : Skill((4, 2, 4), 4, "RA4: Heartseal", ('Slash', 'Wrath'), 
[[skc.OnHit(skc.ApplyStatusCount('Sinking', 3))], [], [], [skc.AddStatusCountForEachY(3, 'Sinking', 1, 'enemy.statuses.Echoes of the Manor.count', 0, 3), 
skc.ApplyStatusCountNextTurn('Echoes of the Manor', 2)]], [skc.AddXForEachY(2, 'coin_power', 5, 'enemy.statuses.Sinking.count', 0, 2)]),

"Intuition" : Skill((3, 4, 2), 1, "Intuition", ("Slash", "Wrath"), 
[[skc.OnHit(skc.ApplyStatus('Rupture', 1)), skc.OnHeadsHit(skc.ApplyStatus('Rupture', 1))] for _ in range(2)],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),
"The Wrap-Up" : Skill((6, 10, 1), 1, "The Wrap-Up", ("Pierce", "Envy"), 
[[skc.OnHit(skc.ApplyStatusCount('Rupture', 2)), skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.defense_level_down, 3))]], 
[skc.ApplyStatusCount('Rupture', 1, 0)]),
"Forensics" : Skill((4, 2, 4), 1, "Forensics", ("Slash", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatusCount('Rupture', 3))]] + [[skc.OnHeadsHit(skc.ApplyStatus('Rupture', 1))] for _ in range(3)],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),

"Rightful Purge" : Skill((3, 4, 2), 1, "Rightful Purge", ("Pierce", "Lust"), [[], []]),
"Enactment!" : Skill((4, 12, 1), 1, "Enactment!", ("Blunt", "Gluttony"), [[skc.AddXForEachY(0.3, 'dynamic', 5, 'enemy.nails', 0, 0.3)]]),
"Fanatical Judgement" : Skill((5, 3, 3), 1, "Fanatical Judgement", ("Blunt", "Wrath"), [[], [], []]),

"All-out War" : Skill((3, 4, 2), 1, "All-out War", ("Slash", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1))], [skc.OnHeadsHit(skc.ApplyStatus('Burn', 1)), skc.OnHit(skc.ApplyStatus('Burn', 1))]],
[skc.DAddXForEachY(1, 'coin_power', 10, 'enemy.statuses.Burn.potency')]),
"Fiery Knifehand" : Skill((4, 5, 2), 1, "Fiery Knifehand", ("Pierce", "Wrath"),
[[skc.OnHit(skc.ApplyStatus('Burn', 2))], [skc.AddXForEachY(0.5, 'dynamic', 6, 'enemy.statuses.Burn.potency', 0, 0.5)]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.potency')]),
"Flame Cleave" : Skill((4, 2, 4), 3, "Flame Cleave", ("Slash", "Lust"), 
[[skc.OnHit(skc.ApplyStatus('Burn', 1))] for _ in range(3)] + [[skc.AddXForEachY(0.4, 'dynamic', 10, 'enemy.statuses.Burn.potency', 0, 0.4)]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Burn.potency')]),

"Slash" : Skill((4, 8, 1), 5, "Slash", ("Blunt", "Sloth"), [[]]),
"Upper Slash" : Skill((4, 14, 1), 5, "Upper Slash", ("Slash", "Pride"), [[skc.GainStatusNextTurn(StatusNames.atk_power_up, 0, 1, 0)]],
[skc.AddXForEachY(2, 'base', 1, f'enemy.statuses.{StatusNames.slash_fragile}.count', 0, 2)]),
"Swash" : Skill((4, 5, 3), 5, "Swash", ("Slash", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.slash_fragile, 3)), skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.slash_fragile, 2, 0))], [], []]),

"Saddled Tasks" : Skill((4, 6, 1), 1, "Saddled Tasks", ("Blunt", "Gloom"), [[]], [skc.AddXForEachY(2, 'coin_power', 5, 'enemy.tremor_count', 0, 2)]),
"Forced Break" : Skill((5, 4, 2), 1, "Forced Break", ("Blunt", "Pride"), [[], []], [skc.AddXForEachY(1, 'base', 7, 'enemy.tremor_count')]),
"Finishing Runup" : Skill((4, 2, 4), 1, "Finishing Runup", ("Blunt", "Sloth"), [[], [], [], [skc.OnHit(SkillEffect('enemy.tremor_count', 'add', -3))]], 
[skc.DAddXForEachY(1, 'coin_power', 10, 'enemy.tremor_count')]),

"Both of You, Shut Up" : Skill((4, 4, 2), 1, "Both of You, Shut Up", ("Blunt", "Envy"), 
[[skc.RedRyoS1PenitenceGain()], [skc.RedEyesGain(2), skc.ApplyStatus('Bleed', 1)]], [skc.DAddXForEachY(1, 'coin_power', 7, 'unit.red_eyes')]),
"S.H. / S.F." : Skill((4, 4, 3), 2, "S.H. / S.F.", ("Blunt", "Gloom"), 
[[skc.PenitenceGain(4)], [skc.RedEyesGain(3), skc.ApplyStatus('Bleed', 2)], [skc.RedRyoS2RedEyesGain()]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency'), skc.DAddXForEachY(1, 'coin_power', 15, GetterMethods.RedRyoSum)]),
"Skullbuster" : Skill((5, 4, 3), 3, "Skullbuster", ("Blunt", "Lust"), 
[[skc.PenitenceGain(7), skc.RedEyesGain(7), skc.ApplyStatus('Bleed', 3)], [skc.RedRyoS3PenitenceGain()], [
skc.OnHit(skc.AddXForEachY(-15, 'unit.sp', 45, 'unit.sp', -15, 0))]], 
[skc.AddXForEachY(1, 'coin_power', 45, 'unit.sp'), skc.AddXForEachY(1, 'coin_power', 1, 'unit.speed')]),
"Serious Skullbuster" : Skill((5, 4, 3), 5, "Serious Skullbuster", ("Blunt", "Lust"), 
[[skc.OnHit(skc.RedRyoS4Bleed())], [], [skc.RedRyoS4Bonus(), skc.OnHit(skc.RedRyoS4AfterAttack())]], [skc.RedRyoS4PowerGain()]),

"Got a Screw Loose?" : Skill((3, 4, 2), 1, "Got a Screw Loose?", ("Blunt", "Lust"), 
[[skc.OnHit(skc.AddXForEachY(1, 'unit.tremor', 1, 'enemy.tremor_count', 0, 4))], [skc.OnHit(skc.InflictTremorCount(2))]], [skc.GainTremor(2)]),
"Compression Wind-up Spanner" : Skill((4, 3, 3), 1, "Compression Wind-up Spanner", ("Pierce", "Sloth"),
[[], [skc.OnHit(skc.InflictTremorCount(1))], [skc.OnHit(skc.YuroRyoS2Count())]], [skc.GainTremor(2), skc.DAddXForEachY(1, 'coin_power', 4, 'unit.tremor')]),
"Percussive Maintenance" : Skill((4, 3, 3), 1, "Percussive Maintenance", ("Pierce", "Gluttony"),
[[skc.OnHit(skc.InflictTremor(2))], [skc.OnHit(skc.InflictTremor(2))], [skc.OnHit(SkillEffect('enemy.tremor_count', 'add', -1))]],
[skc.GainTremor(2), skc.ConsumeRessourceTrigger('unit.tremor', 8, 8, skc.CoinPower(1)), skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.tremor')]),

"Sole Strike" : Skill((3, 8, 1), 3, "Sole Strike", ("Slash", "Lust"), [[]], [skc.GainPoiseCount(2)]),
"Deep Cuts" : Skill((5, 3, 3), 3, "Deep Cuts", ("Pierce", "Gloom"), [[skc.OnHit(skc.GainPoiseNextTurn(1))] for _ in range(3)]),
"Opportunistic Slash" : Skill((4, 8, 2), 3, "Opportunistic Slash", ("Slash", "Envy"), [[], []], [skc.CoinPower(3, 0)]),

"Rev Up" : Skill((4, 3, 2), 3, "Rev Up", ("Blunt", "Pride"), [[skc.OnHit(skc.GainCharge(4))], []], [skc.GainCharge(2), skc.ResetAttackWeight(0)]),
"Vibration Compression" : Skill((6, 3, 2), 3, "Vibration Compression", ("Pierce", "Gloom"), 
[[], [SkillEffect('unit.atk_weight', 'add', 1), skc.ReuseCoinConditional(2, SkillConditionals.RoseRodyaReuse)]], 
[skc.ResetAttackWeight(-2), skc.DAddXForEachY(1, 'coin_power', 10, 'enemy.tremor_count')]),
"Let's Rack Up Some Scores" : Skill((5, 4, 3), 3, "Let's Rack Up Some Scores", ("Blunt", "Envy"), [[] for _ in range(3)], 
[skc.GainCharge(6), skc.ResetAttackWeight(2)]),

"Draw of the Sword(Outis)" : Skill((4, 6, 1), 1, "Draw of the Sword(Outis)", ("Slash", "Wrath"), 
[[skc.OnHit(skc.GainPoise(4))]], [skc.DAddXForEachY(1, 'coin_power', 5, 'unit.poise_potency')]),
"Acupuncture(Outis)" : Skill((5, 4, 2), 1, "Acupuncture(Outis)", ("Pierce", "Lust"), [[], [skc.OnHeadsHit(skc.GainStatusNextTurn(StatusNames.slash_dmg_up, 0, 2))]],
[skc.GainPoiseCount(2, 0)]),
"Decisive Dive" : Skill((6, 4, 2), 1, "Decisive Dive", ("Slash", "Pride"), [[], []], [skc.BasePowerUp(2, 0)]),

"Hack" : Skill((4, 3, 2), 5, "Hack", ("Slash", "Gluttony"), [[], []], 
[skc.DynamicBonus(0.4, 0), skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Rupture.potency')]),
"Dismember" : Skill((6, 10, 1), 5, "Dismember", ("Slash", "Sloth"), 
[[skc.OnHit(skc.ApplyStatus('Rupture', 5))]], [skc.DAddXForEachY(0.5, 'dynamic', 5, 'enemy.statuses.Rupture.potency', 0, 0.5)]),
"Eviscerate" : Skill((4, 2, 4), 5, "Eviscerate", ("Pierce", "Lust"),
[[skc.OnHit(skc.GCorpGregorS3Bonus())] for _ in range(3)] + [[]], [skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Rupture.potency')]),

"Keep It Fresh" : Skill((4, 2, 2), 1, "Keep It Fresh", ("Blunt", "Lust"), [[], []], [skc.DynamicBonus(0.3, 0)]),
"You Fresh Enough?" : Skill((6, 8, 1), 0, "You Fresh Enough?", ("Slash", "Gluttony"), [[]], [skc.CoinPower(3, 0)]),
"Butcher Viand" : Skill((5, 1, 4), 3, "Butcher Viand", ("Slash", "Envy"), [[] for _ in range(4)], [skc.CoinPower(1, 0)]),

"CT - DK" : Skill((3, 4, 2), 2, "CT - DK", ("Slash", "Lust"), [
[skc.OnHit(skc.GainCourrierTrunk(1, SkillConditionals.CourrierTrunkBelow15)), skc.OnHit(skc.GainCourrierTrunk(1))], 
[skc.OnHit(skc.ApplyStatus('Rupture', 3, condition=SkillConditionals.DevRodyaRuptureCondInverted))]], 
[skc.DVRRuptureCondCheck(), skc.StopRuptureDrain(SkillConditionals.DevRodyaRuptureCond), skc.DevyatRodyaCoinPower()]),
"CT - GR" : Skill((4, 4, 3), 2, "CT - GR", ("Slash", "Wrath"),
[[skc.OnHit(skc.GainCourrierTrunk(2, SkillConditionals.CourrierTrunkBelow15)), skc.OnHit(skc.GainCourrierTrunk(1))], [], []],
[skc.DVRRuptureCondCheck(), skc.StopRuptureDrain(SkillConditionals.DevRodyaRuptureCond), 
skc.DAddXForEachY(0.02, 'dynamic', 1, 'unit.trunk', 0, 0.4), skc.DevyatRodyaCoinPower()]),
"I Trust Ya, Polu!" : Skill((5, 4, 3), 4, "I Trust Ya, Polu!", ("Slash", "Gluttony"), 
[[], [skc.OnHit(skc.ApplyStatusCount('Rupture', 3, condition=SkillConditionals.DevRodyaRuptureCondInverted)), 
skc.OnHit(skc.AddStatusCountForEachY(1, 'Rupture', 10, 'unit.trunk', 0, 2, condition=SkillConditionals.DevRodyaRuptureCondInverted))],
[skc.ReuseCoin(1, SkillConditionals.DevRodyaRuptureCond), skc.AddXForEachY(0.25, 'dynamic', 15, 'unit.trunk', 0, 0.25, duration=1)]],
[skc.DVRRuptureCondCheck(), skc.DevyatRodyaCoinPower(), skc.DAddXForEachY(0.04, 'dynamic', 1, 'unit.trunk', 0, 0.8)]),

"Studious Dedication" : Skill((3, 4, 2), 0, "Studious Dedication", ("Blunt", "Gluttony"), [[], [skc.OnHit(skc.ApplyStatusCount('Sinking', 2))]], 
[skc.GainErudition(2, 0)]),
"Moment of Erudition" : Skill((4, 6, 2), 1, "Moment of Erudition", ("Pierce", "Sloth"), 
[[], [skc.OnHit(skc.AddStatusPotForEachY(2, 'Sinking', 1, 'unit.insight', 2, 6))]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Sinking.potency', 0, 2), skc.DAddXForEachY(0.05, 'dynamic', 1, 'unit.insight', 0, 0.15)]),
"Scorch Knowledge" : Skill((5, 4, 3), 3, "Scorch Knowledge", ("Blunt", "Gloom"), [[], [], [skc.OnHit(skc.DeiciMeurS3Sinking())]], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Sinking.potency', 0, 2), skc.DAddXForEachY(0.05, 'dynamic', 1, 'unit.insight', 0, 0.45),
skc.DeiciMeurS3Insight(), skc.DeiciMeurResetInsight()]),

"Baile y Rola" : Skill((4, 2, 2), -3, "Baile y Rola", ("Blunt", "Sloth"), [[skc.OnHit(skc.ApplyStatus('Sinking', 4))], []], 
[skc.DAddXForEachY(1, 'coin_power', 4, 'enemy.statuses.Sinking.potency')]),
"Danza de Pasión" : Skill((5, 1, 3), -3, "Danza de Pasión", ("Blunt", "Envy"), 
[[skc.OnHit(skc.GainPoise(2)), skc.OnHit(skc.GainPoiseCount(1))], [skc.OnHit(skc.ApplyStatus('Sinking', 2)), skc.OnHit(skc.ApplyStatusCount('Sinking', 1))],
[skc.OnHit(skc.ApplyStatus('Sinking', 2))]], [skc.DAddXForEachY(2, 'coin_power', 6, 'enemy.statuses.Sinking.potency', 0, 2)]),
"Pañata Party" : Skill((8, 11, 1), -3, "Pañata Party", ("Blunt", "Gloom"), [[skc.OnCritRoll(skc.DAddXForEachY(0.3, 'dynamic', 5, 'unit.poise_count', 0, 0.3))]],
[skc.AddXForEachY(0.01, 'crit_odds_bonus', -1, 'enemy.sp', 0, 0.45)]),

"Sabre Slash" : Skill((5, 6, 1), 5, "Sabre Slash", ("Slash", "Envy"), [[skc.OnHit(skc.ApplyStatus('Sinking', 3))]], 
[skc.DAddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Sinking.potency', 0, 2)]),
"Remise" : Skill((4, 6, 2), 5, "Remise", ("Slash", "Gloom"), [[], [skc.OnHit(skc.ApplyStatusCount('Sinking', 3))]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Sinking.potency'), skc.ApplyStatusCount('Sinking', 2, condition=0)]),
"Nightmare Hunt" : Skill((4, 3, 4), 5, "Nightmare Hunt", ("Slash", "Lust"), 
[[skc.OnHit(skc.ApplyStatus("Sinking", 1))] for _ in range(3)] + [[skc.OnHit(skc.HeirGregorS3Bonus())]]),

"Zwei Knight's Greatsword Form" : Skill((3, 4, 2), 0, "Zwei Knight's Greatsword Form", ("Blunt", "Pride"),
[[skc.OnHit(skc.GainStatusNextTurn(StatusNames.defense_level_up, 0, 2))] for _ in range(2)], 
[skc.ZweiIshDlTremorConversion(3), skc.AddXForEachY(1, 'base', 4, get_dlup_str(), 0, 2)]),
"Can't Let You Through." : Skill((4, 4, 3), 1, "Can't Let You Through.", ("Blunt", "Envy"), 
[[], [skc.OnHit(skc.GainStatusNextTurn(StatusNames.defense_level_up, 0, 4))], []],
[skc.ZweiIshDlTremorConversion(5), skc.AddXForEachY(1, 'coin_power', 4, get_dlup_str()), skc.GainTremor(3, 0)]),
"Ward" : Skill((5, 4, 3), 2, "Ward", ("Blunt", "Gluttony"), [[], [], [skc.ZweiIshS3Bonus()]],
[skc.ZweiIshDlTremorConversion(5), skc.DynamicBonus(0.7, SkillConditionals.HasDefensiveStance), skc.AddXForEachY(1, 'coin_power', 4, get_dlup_str(), 0, 4), 
skc.GainTremor(3, 0)]),

"Expend Knowledge" : Skill((3, 4, 2), -1, "Expend Knowledge", ("Pierce", "Gluttony"), [[], []], [skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Sinking.potency')]),
"Seal Shut" : Skill((4, 3, 3), -1, "Seal Shut", ("Blunt", "Lust"), [[]]+[[skc.OnHit(skc.AddStatusPotForEachY(1, 'Sinking', 1, 'unit.insight', 0, 3))] for _ in [0,0]],
[skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Sinking.potency')]),
"Grace of Knowledge" : Skill((4, 2, 4), 3, "Grace of Knowledge", ("Blunt", "Sloth"), 
[[], [], [], [skc.OnHit(skc.ApplyStatusCount('Sinking', 3))]], [skc.CoinPower(1, 0)]),

"Sprouting Bud" : Skill((3, 2, 3), 4, "Sprouting Bud", ("Pierce", "Gluttony"), 
[[], [skc.OnHit(skc.ApplyStatusCountNextTurn('Sinking', 1))], [skc.OnHit(skc.ApplyStatusCountNextTurn('Sinking', 2))]], [skc.GainTremor(3)]),
"Moment's Floral Breeze" : Skill((4, 4, 3), 3, "Moment's Floral Breeze", ("Blunt", "Sloth"), [[skc.OnHit(skc.ApplyStatusNextTurn('Sinking', 2))] for _ in range(3)],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Sinking.count'), skc.ResetAttackWeight(1), skc.SpicebushS2AOE()]),
"Bloodsteeped Scent" : Skill((6, 4, 3), 5, "Bloodsteeped Scent", ("Pierce", "Pride"), 
[[skc.OnHit(skc.ApplyStatusCount('Sinking', 1))], [skc.OnHit(skc.ApplyStatusCount('Sinking', 1))], 
[skc.OnHit(skc.SpicebushS3Bonus()), skc.OnHit(skc.SpiceBushSinkingDeluge())]], [skc.GainTremor(6)]),

"Drive" : Skill((5, 1, 2), 0, "Drive", ("Pierce", "Sloth"), [[], []], [skc.CoinPower(2, 0)]),
"You Are Cleansed of Sin" : Skill((6, 3, 2), 0, "You Are Cleansed of Sin", ("Blunt", "Wrath"), [[skc.OnHit(skc.ApplyStatusCount("Nails", 3))], []]),
"Annihilate Heretics" : Skill((8, 3, 2), 0, "Annihilate Heretics", ("Pierce", "Pride"), [[skc.OnHit(skc.ApplyStatusCount("Nails", 2))], []]),

"Devoted Hammering" : Skill((3, 4, 2), 3, "Devoted Hammering", ("Pierce", "Pride"), 
[[skc.OnHit(skc.AddStatusCountForEachY(1, "Nails", 1, 'enemy.statuses.Nails.count'))] for _ in range(2)]),
"Zealous Purge" : Skill((6, 2, 2), 3, "Zealous Purge", ("Blunt", "Lust"), [[skc.OnHit(skc.ApplyStatusCountNextTurn("Nails", 1))], []],
[skc.GainStatusNextTurn("Fanatic", 0, 1, 0)]),
"Ironclad Retribution" : Skill((4, 2, 4), 3, "Ironclad Retribution", ("Blunt", "Wrath"), [[] for _ in range(4)],
[skc.AddXForEachY(0.15, 'dynamic', 1, 'unit.statuses.Fanatic.count', 0, 0.15), skc.AddXForEachY(0.05, 'dynamic', 1, 'unit.ncorp_allies', 0, 0.3)]),

"Slice then Stab" : Skill((5, 2, 2), 2, "Slice then Stab", ("Pierce", "Gluttony"), [[], [skc.OnHit(skc.GainPoiseCount(2))]], 
[skc.DAddXForEachY(1, 'coin_power', 3, 'unit.poise_count')]),
"Slash Series" : Skill((6, 2, 3), 2, "Slash Series", ("Slash", "Wrath"), [[skc.OnHit(skc.GainPoise(2))], [skc.OnHit(skc.GainPoise(1))], [skc.OnHit(skc.GainPoise(1))]],
[skc.StopPoiseDrain(0)]),
"To Claim Their Bones" : Skill((8, 18, 1), 2, "To Claim Their Bones", ("Slash", "Pride"), 
[[skc.OnCritRoll(skc.AddXForEachY(1.5, 'dynamic', 10, 'unit.poise_count', 0, 1.5)), skc.DynamicBonus(0.2, 0)]]),

"We Remember" : Skill((3, 4, 2), 1, "We Remember", ("Blunt", "Sloth"), [[], []]),
"Chains of Loyalty" : Skill((4, 5, 2), 1, "Chains of Loyalty", ("Blunt", "Envy"), [[], []]),
"Recording" : Skill((4, 3, 3), 3, "Recording", ("Blunt", "Wrath"), 
[[], [], [skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.envy_fragile, 2, SkillConditionals.HasMark))]], [skc.CoinPower(1, i) for i in range(2)]),

"Predictive Analysis" : Skill((6, 4, 1), 0, "Predictive Analysis", ("Blunt", "Gluttony"), [[skc.OnHit(skc.ApplyStatus('Rupture', 1))]]),
"Field Command" : Skill((5, 5, 2), 0, "Field Command", ("Slash", "Sloth"), 
[[skc.OnHit(skc.ApplyStatusCount('Rupture', i + 1)), skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.defense_level_down, 2))] for i in range(2)]),
"Exploit the Gap" : Skill((6, 2, 3), 0, "Exploit the Gap", ("Blunt", "Lust"), 
[[], [], [skc.OnHit(skc.SevenOutisS3Bonus()), skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.weakness_analyzed, 1))]],
[skc.DAddXForEachY(2, 'coin_power', 7, 'enemy.statuses.Rupture.potency', 0, 2)]),

"Execution Advised" : Skill((3, 4, 2), 2, "Execution Advised", ("Slash", "Envy"), [[], [skc.OnHit(skc.ApplyStatusCount('Tremor', 2))]],
[skc.DAddXForEachY(1, 'coin_power', 3, 'enemy.statuses.Tremor.potency', 0, 2)]),
"Final Warning" : Skill((4, 6, 2), 2, "Final Warning", ("Slash", "Gloom"), [[skc.OnHit(skc.ApplyStatus('Tremor', 2))], [skc.OnHit(skc.ApplyStatus('Tremor', 2))]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Tremor.potency', 0, 2)]),
"Execution Sentencing" : Skill((5, 4, 3), 2, "Execution Sentencing", ("Slash", "Pride"), 
[[skc.OnHit(skc.ApplyStatus('Tremor', 1))], [skc.OnHit(skc.ApplyStatus('Tremor', 1))], [skc.OnHit(skc.TremorDecayConversion())]]),

"Suppressing." : Skill((3, 4, 2), 0, "Suppressing.", ("Slash", "Lust"), [[], [skc.OnHit(skc.GainStatusNextTurn(StatusNames.defense_level_up, 0, 2))]],
[skc.GainStatus(StatusNames.defense_level_up, 0, 2), skc.GainTremor(3, 0)]),
"Combat Preparation" : Skill((4, 5, 2), 1, "Combat Preparation", ("Slash", "Gloom"), 
[[], []], [skc.ZweiIshDlTremorConversion(3), skc.AddXForEachY(1, 'coin_power', 4, get_dlup_str()), skc.GainTremor(3, 0)]), #never the ally with lowest HP
"Fence" : Skill((4, 3, 3), 2, "Fence", ("Blunt", "Sloth"), [[], [], [skc.OnHit(skc.ZweiSinclairWestS3Tremor())]], #never the ally with lowest HP either
[skc.ZweiIshDlTremorConversion(99), skc.AddXForEachY(1, 'coin_power', 3, get_dlup_str(), 0, 3)]),

"Allez" : Skill((3, 4, 2), 2, "Allez", ("Pierce", "Pride"), [[skc.OnHit(skc.GainPoiseCount(1))], [skc.OnHit(skc.ApplyStatus('Rupture', 1), SkillConditionals.DevRodyaRuptureCondInverted), 
skc.OnHit(skc.AddStatusPotForEachY(1, 'Rupture', 1, 'unit.rel_speed', 0, 3, condition=SkillConditionals.DevRodyaRuptureCondInverted))]], 
[skc.DVRRuptureCondCheck(), skc.StopRuptureDrain(SkillConditionals.DevRodyaRuptureCond), skc.GainPoiseCount(2), 
skc.AddXForEachY(1, 'coin_power', 3, 'unit.rel_speed', 0, 2)]),
"Fente" : Skill((4, 4, 3), 2, "Fente", ("Pierce", "Gluttony"), 
[[skc.OnHit(skc.GainPoiseCount(2))], [skc.OnHit(skc.GainPoise(2))],  #coins 1 and 2
[skc.OnCritRoll(skc.DynamicBonus(0.2), SkillConditionals.DevRodyaRuptureCond),
skc.OnCritRoll(skc.AddXForEachY(0.1, 'dynamic', 7, 'unit.speed', 0, 0.1), SkillConditionals.DevRodyaRuptureCond),
skc.OnHit(skc.ApplyStatus('Rupture', 4), SkillConditionals.DevRodyaRuptureCondInverted), 
skc.OnHit(skc.AddStatusCountForEachY(2, 'Rupture', 7, 'unit.speed', 0, 2), SkillConditionals.DevRodyaRuptureCondInverted)]],
[skc.DVRRuptureCondCheck(), skc.StopRuptureDrain(SkillConditionals.DevRodyaRuptureCond), skc.GainPoiseCount(2, 0), skc.AddXForEachY(1, 'coin_power', 3, 'unit.rel_speed')]),
"Salut" : Skill((5, 4, 3), 3, "Salut", ("Pierce", "Gloom"), [[], [], 
[skc.AddXForEachY(0.2, 'dynamic', 1, 'enemy.meur_focus', 0, 0.6), skc.OnCritRoll(skc.DynamicBonus(0.3)), 
skc.OnCritRoll(skc.AddXForEachY(0.02, 'dynamic', 1, 'enemy.statuses.Rupture.potency', 0, 0.3)), skc.CinqMeurS3HeadsBonus()]],
[skc.DVRRuptureCondCheck(), skc.StopRuptureDrain(SkillConditionals.DevRodyaRuptureCond), skc.AddXForEachY(1, 'coin_power', 2, 'unit.rel_speed', 0, 3),
skc.GainPoise(5, 0), skc.AddXForEachY(5, 'unit.poise_potency', 1, 'enemy.meur_focus', 0, 5, condition=0)]),

"Prepare to Collect" : Skill((3, 4, 2), 1, "Prepare to Collect", ("Blunt", "Envy"), [[], [skc.OnHit(skc.GainTremor(1))]], [skc.GainTremor(2)]),
"T Corp. Martial Suppression" : Skill((4, 5, 2), 1, "T Corp. Martial Suppression", ("Blunt", "Wrath"), [[skc.OnHit(skc.GainTremor(2))], 
[skc.OnHit(skc.ApplyStatusCountNextTurn('Bind', 1)), skc.OnHit(skc.AddStatusCountForEachY(1, 'Bind', 6, 'enemy.tremor', next_turn=True))]],
[skc.GainTremor(2), skc.AddXForEachY(0.05, 'dynamic', 1, 'enemy.statuses.Bind.count', 0, 0.15)]),
"Execute Collections" : Skill((2, 3, 4), 1, "Execute Collections", ("Blunt", "Sloth"), [[], [], [],
[skc.OnHit(skc.ApplyStatusCountNextTurn('Bind', 1)), skc.OnHit(skc.AddStatusCountForEachY(2, 'Bind', 1, 'global_state.ConsumedTremor', 0, 2, next_turn=True)),
skc.OnHit(skc.TRodyaMoratium())]], [skc.TRodyaS3CoinPower(), skc.AddXForEachY(0.05, 'dynamic', 1, 'enemy.statuses.Bind.count', 0, 0.2)]),

"Let Us Prepare to Collect" : Skill((3, 4, 2), 0, "Let Us Prepare to Collect", ("Blunt", "Gluttony"), [[], []], [skc.GainTremor(2)]),
"T Corp. Accelerated Amputator" : Skill((4, 4, 3), 0, "T Corp. Accelerated Amputator", ("Blunt", "Pride"),
[[skc.OnHit(skc.AddXForEachY(2, 'unit.tremor', 1, 'enemy.tremor', 0, 6))], [], []], [skc.GainTremor(3)]),
"I Command Thee, Halt!" : Skill((4, 3, 4), 0, "I Command Thee, Halt!", ("Blunt", "Sloth"), [[], [], [], [skc.OnHit(skc.TDonMoratium())]],
[skc.ConsumeRessourceTrigger('unit.tremor', 10, 10, skc.CoinPower(2))]),

"Celebration for the Departed" : Skill((4, 4, 2), 2, "Celebration for the Departed", ("Pierce", "Pride"), [[*skc.ButterflySangShortcut(1)] for _ in range(2)],
[skc.DAddXForEachY(1, 'coin_power', 6, GetterMethods.ButterflySinkingSum), skc.ApplyStatusCount('Sinking', 2, condition=0), skc.ButterflySangCondReload()]),
"Solemn Lament for the Living" : Skill((4, 6, 2), 2, "Solemn Lament for the Living", ("Pierce", "Gloom"), 
[[*skc.ButterflySangShortcut(5)], [*skc.ButterflySangShortcut(1)]], 
[skc.DAddXForEachY(1, 'coin_power', 6, GetterMethods.ButterflySinkingSum, 0, 2), skc.ApplyStatusCount('Sinking', 1, condition=0), skc.ButterflySangCondReload()]),
"Goodbye Now, A Sorrow In You" : Skill((4, 3, 4), 5, "Goodbye Now, A Sorrow In You", ("Pierce", "Sloth"), 
[[*skc.ButterflySangShortcut(1)], [*skc.ButterflySangShortcut(6)], [skc.ButterflySangS3ConsumeAmmo(), skc.InflictBulletButterfly()], [skc.OnHit(skc.ButterflySangS3Bonus())]],
[skc.DAddXForEachY(1, 'coin_power', 6, GetterMethods.ButterflySinkingSum, 0, 2), skc.AddXForEachY(1, 'base', 5, GetterMethods.ButterflySangAmmoSum, 0, 4), 
skc.ApplyStatusCount('Sinking', 3, condition=0), skc.AfterAttack(skc.ButterflySangReload())]),

"Deduction Start" : Skill((3, 4, 2), 2, "Deduction Start", ("Blunt", "Gloom"), 
[[skc.OnHit(skc.ApplyStatus('Tremor', 2))], [skc.OnHit(skc.GainTremor(2))]], [skc.GainTremor(2), skc.DAddXForEachY(1, 'coin_power', 6, 'unit.tremor')]),
"Morph Cane Technique" : Skill((4, 4, 3), 2, "Morph Cane Technique", ("Pierce", "Sloth"), 
[[skc.OnHit(skc.GainTremor(3))], [skc.OnHit(skc.ApplyStatus('Tremor', 3))], [skc.OnHit(skc.TremorBurst(1, SkillConditionals.Enemy6PlusTremor))]],
[skc.GainTremor(3), skc.DAddXForEachY(1, 'coin_power', 5, 'unit.tremor')]),
"You're the Culprit!" : Skill((3, 3, 4), 4, "You're the Culprit!", ("Pierce", "Gluttony"), [[skc.OnHit(skc.ReverbEntanglement(SkillConditionals.ConsumedTremor))], 
[skc.OnHit(skc.TremorBurst(1))], [skc.OnHit(skc.TremorBurst(1, SkillConditionals.ConsumedTremor))], [skc.OnHit(skc.TremorBurst(1, SkillConditionals.ConsumedTremor))]],
[skc.TCorpLuS3CoinPower()]),

"Slam" : Skill((3, 4, 2), 1, "Slam", ("Blunt", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatus('Rupture', 1)), skc.OnHeadsHit(skc.ApplyStatus('Rupture', 1))] for _ in range(2)],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency')]),
"Bonecrusher" : Skill((4, 5, 2), 2, "Bonecrusher", ("Blunt", "Pride"),
[[skc.OnHit(skc.ApplyStatusCount('Rupture', 1, condition=SkillConditionals.FLuRuptureCondInverted)), 
skc.OnHeadsHit(skc.ApplyStatusCount('Rupture', 1, condition=SkillConditionals.FLuRuptureCondInverted))], 
[skc.OnHit(skc.ApplyStatus('Rupture', 2, condition=SkillConditionals.FLuRuptureCondInverted))]],
#
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency'),
skc.FLuRuptureCondCheck(),
skc.CoinPower(1, SkillConditionals.FLuRuptureCond), 
skc.OnUse(skc.CoinPower(1, SkillConditionals.FLuRuptureCond), SkillConditionals.BloodfiendOrBloodbag),
skc.OnUse(skc.ApplyStatusCount('Rupture', 1, condition=SkillConditionals.FLuRuptureCondInverted), condition=0)]),
"A Cheerful Hunt's End" : Skill((4, 3, 3), 3, "A Cheerful Hunt's End", ("Blunt", "Wrath"), 
[[skc.OnHeadsHit(skc.ApplyStatus('Rupture', 1, condition=SkillConditionals.FLuRuptureCondInverted))], 
[skc.OnHeadsHit(skc.ApplyStatus('Rupture', 2, condition=SkillConditionals.FLuRuptureCondInverted))],
[skc.ReuseCoin(1, condition=SkillConditionals.FangLuS3Reuse)]],
#
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Rupture.potency'),
skc.FLuRuptureCondCheck(),
skc.CoinPower(1, SkillConditionals.FLuRuptureCond), 
skc.OnUse(skc.CoinPower(1, SkillConditionals.FLuRuptureCond), SkillConditionals.BloodfiendOrBloodbag),
skc.OnUse(skc.ApplyStatusCount('Rupture', 2, condition=SkillConditionals.FLuRuptureCondInverted), condition=0)]),

"Sewing" : Skill((3, 4, 2), 1, "Sewing", ("Slash", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatusCount('Bleed', 1, condition=scc.has_sewing_target()))] for _ in range(2)], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency', 0, 2), skc.BarberOutisS1Bloodfeast()]),
"Scission" : Skill((4, 4, 3), 3, "Scission", ("Slash", "Lust"), 
[[skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatus('Bleed', 2, condition=scc.has_sewing_target()))] for _ in range(2)] + \
[[skc.OnHit(skc.ApplyStatusCountNextTurn(StatusNames.sewing_target, 1))]], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency'), skc.BarberOutisS2Bloodfeast()]),
"I'll Make You a New Dress!" : Skill((3, 3, 4), 5, "I'll Make You a New Dress!", ("Slash", "Wrath"), 
[[skc.OnHit(skc.ApplyStatus('Bleed', 2))], [skc.OnHit(skc.ApplyStatus('Bleed', 2))], [skc.OnHit(skc.ApplyStatus('Bleed', 2))], [skc.BarberOutisS3Bonus()]],
[skc.DAddXForEachY(1, 'coin_power', 5, 'enemy.statuses.Bleed.potency'), skc.BarberOutisS3AtkWeight(), skc.AfterAttack(skc.BarberOutisResetAtkWeight())]),

"Sacrifice for the Family" : Skill((3, 4, 2), 1, "Sacrifice for the Family", ("Blunt", "Gluttony"), 
[[skc.OnHit(skc.ApplyStatus('Bleed', 2))], [skc.OnHit(skc.ApplyStatus('Rupture', 1)), skc.OnHit(skc.GainBloodiedHand(3))]], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency', 0, 2), skc.PriestGregorS1OnUse()]),
"Suffocating Guilt" : Skill((4, 6, 2), 1, "Suffocating Guilt", ("Blunt", "Pride"), 
[[skc.OnHit(skc.ApplyStatusCount('Bleed', 2))], [skc.OnHit(skc.ApplyStatus('Rupture', 1)), skc.OnHit(skc.GainBloodiedHand(3))]],
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency', 0, 2), skc.PriestGregorS2OnUse()]),
"The Unforgivable Sin" : Skill((5, 4, 3), 3, "The Unforgivable Sin", ("Blunt", "Lust"), 
[[skc.OnHit(skc.GainBloodiedHand(3))], [skc.OnHit(skc.ApplyStatusCount('Bleed', 2)), skc.OnHit(skc.ApplyStatusCount('Rupture', 2))], 
[skc.OnHit(skc.ApplyStatus('Rupture', 2)), skc.OnHit(skc.ApplyStatus('Bleed', 2)), skc.ReuseCoinConditional(1, SkillConditionals.PriestGregorS3Reuse)]], 
[skc.DAddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency'), skc.DAddXForEachY(0.015, 'dynamic', 0.01, 'unit.missing_hp', 0, 0.9),
skc.PriestGregorS3OnUse()]),

"Begone…" : Skill((3, 4, 2), 1, "Begone…", ("Pierce", "Pride"), [[], [skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatus('Rupture', 1))]],
[skc.DulcRodyaS1OnUse(), skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency', 0, 2)], [SkillTagNames.does_bloodfeast]),
"In Finely Ground Mistfall" : Skill((4, 4, 3), 2, "In Finely Ground Mistfall", ("Pierce", "Envy"), 
[[skc.OnHit(skc.ApplyStatusCount('Bleed', 2)), skc.OnHit(skc.ApplyStatusCount('Rupture', 2))], 
[], 
[skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatus('Rupture', 1))]],
[skc.DulcRodyaS2OnUse(), skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency', 0, 2)], [SkillTagNames.does_bloodfeast]),
"The Festival Will End" : Skill((4, 4, 3), 3, "The Festival Will End", ("Pierce", "Lust"), 
[[skc.OnHit(skc.ApplyStatusCount('Bleed', 1)), skc.OnHit(skc.ApplyStatusCount('Rupture', 1))], 
[skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatus('Rupture', 1))], 
[skc.OnHit(skc.ApplyStatus('Bleed', 1)), skc.OnHit(skc.ApplyStatus('Rupture', 1))]],
[skc.DulcRodyaS3OnUse(), skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency')]),
"A-DQHA - The Finale" : Skill((4, 5, 3), 5, "A-DQHA - The Finale", ("Pierce", "Lust"), 
[[skc.OnHit(skc.ApplyStatusCount('Bleed', 2)), skc.OnHit(skc.ApplyStatusCount('Rupture', 2))], 
[skc.OnHit(skc.ApplyStatus('Bleed', 2)), skc.OnHit(skc.ApplyStatus('Rupture', 2))], 
[skc.OnHit(skc.ApplyStatus('Bleed', 2)), skc.OnHit(skc.ApplyStatus('Rupture', 2))]],
[skc.DulcRodyaS4OnUse(), skc.AddXForEachY(1, 'coin_power', 6, 'enemy.statuses.Bleed.potency'), skc.AfterAttack(skc.DulcRodyaS4AfterAttack())]),
"DQHA 15: Parasol" : Skill((5, 4, 2), 2, "DQHA 15: Parasol", ("Pierce", "Lust"), 
[[skc.OnHit(skc.ApplyStatus('Bleed', 2))], [skc.OnHit(skc.ApplyStatusCount('Bleed', 1))]],
[skc.GainBloomingThorn(4, condition=0)], [SkillTagNames.does_bloodfeast]),
}


ENEMIES = {
    "Test" : Enemy(40, 100, {}, {}),
    "Lux" : Enemy(37, 598, {}, {"Lust" : 0.5}, 2),
    "GlutLux" : Enemy(31, 485, {}, {"Gluttony" : 2, "Envy" : 0.75, "Lust" : 0.75, "Pride" : 0.75, "Wrath" : 0.75}, 3),
    "Bull" : Enemy(47, 1012, {"Slash" : 2}, {"Lust" : 0.75}, 1),
    "Doll_Body" : Enemy(42, 551, {}, {"Lust" : 0.5, "Envy" : 0.5}, 3, True),
    "Bull_Body" : Enemy(47, 1012, {},  {"Wrath" : 0.75, "Lust" : 0.75, "Sloth" : 0.75, "Gluttony" : 0.5, "Gloom" : 2, "Pride" : 0.5, "Envy" : 0.75},
                        2, True, [0.25])
}

gs = Skill.get_skill

UNITS = {
    "NClair" : Unit("NClair", (gs("Coerced Judgement"), gs("Amoral Enactement"), gs("Self-Destrutive Purge"))),
    "5Clair" : Unit("5Clair", (gs("Remise"), gs("Engagement"), gs("Contre Attaque"))),
    "RCliff" : Unit("RCliff", (gs("Graze The Grass"), gs("Concentrated Fire"), gs("Quick Suppression"))),
    "RIsh"   : Unit("Rish", (gs("Mind Strike"), gs("Flying Surge"), gs("Mind Whip"))),
    "SunCliff" : Unit("SunCliff", (gs("Umbrella Thwack"), gs("Puddle Stomp"), gs("Spread Out!"))),
    "PeqCliff" : Unit("PeqCliff", (gs("Stalk Prey"), gs("Snagharpoon"), gs("Sever Knot"))),
    "Deici Rodya" : Unit("Deici Rodya", (gs("Illuminate Thy Vacuity"), gs("Weight of Knowledge"), gs("Excruciating Study"))),
    "Chef Ryo" : Unit("Chef Ryo", (gs("PC"), gs("IH"), gs("I Can Cook Anything"))),
    "Molar Outis" : Unit("Molar Outis", (gs("Wait Up!"), gs("Slice"), gs("Daring Decision")) ),
    'Deici Lu' : Unit('Deici lu', (gs("Expend Knowledge"), gs('Unveil'), gs("Cyclical Knowledge"))),
    'Ring Sang' : Unit('Ring Sang', (gs("Paint Over"), gs("Sanguine Pointillism"), gs("Hematic Coloring"))),
    'Liu Ish' : Unit('Liu Ish', (gs('Red Kick'), gs("Frontal Assault"), gs("Inner Gate Elbow Strike"))),
    'W Don' : Unit('W Don', (gs('Rip(Don)'), gs('Leap(Don)'), gs('Rip Space'))),
    'W Ryo' : Unit('W Ryo', (gs('EC'), gs('Leap(Ryoshu)'), gs('DDEDR'))),
    'TT Lu' : Unit('TT Lu', (gs('Throat Slit'), gs('Shank'), gs('Mutilate'))),
    'Bl Meur' : Unit('Bl Meur', (gs("Draw of the Sword"), gs("Acupuncture"), gs("Yield My Flesh"), gs("To Claim Their Bones"))),
    'Maid Ryo' : Unit('Maid Ryo', (gs('RA1 : The Hunt'), gs('RA7 : Capture'), gs('RA2 : SYNC'))),
    'MC Faust' : Unit('MC Faust', (gs("40Y-3 Activation"), gs("Charge Countercurrent"), gs("40Y-3 Charge"))),
    'Butler Outis' : Unit('Butler Outis', (gs("Knocking"), gs("Dusting"), gs("As Mistress Commands"))),
    'Warp Outis' : Unit('Warp Outis', (gs("Ripple"), gs("Charged Leap"), gs("Rip Dimension"))),
    'Mid Don' : Unit('Mid Don', (gs("Checking the Book"), gs("Proof of Loyalty"), gs("A Just Vengeance"), gs("A Just Vengeance(Counter)"))),
    'Regret Faust' : Unit('Regret Faust', (gs("Contracting Straight-jacket"), gs("Metallic Ringing"), gs("Unleashed Violence"))), 
    "LCB Sang" : Unit("LCB Sang", (gs("Deflect"), gs("End-stop Stab"), gs("Enjamb"))),
    "LCB Faust" : Unit("LCB Faust", (gs("Downward Slash"), gs("Upward Slash"), gs("Drilling Stab"))),
    "LCB Don" : Unit("LCB Don", (gs("Joust"), gs("Galloping Tilt"), gs("For Justice!"))),
    "LCB Ryo" : Unit("LCB Ryo", (gs("Paint"), gs("Splatter"), gs("Brushstroke"))),
    "LCB Meur" : Unit("LCB Meur", (gs("Un, Deux"), gs("Nailing Fist"), gs("Des Coups"))),
    "LCB Hong Lu" : Unit("LCB Hong Lu", (gs("Downward Cleave"), gs("Dual Strike"), gs("Whirlwind"))),
    "LCB Heath" : Unit("LCB Heath", (gs("Bat Bash"), gs("Smackdown"), gs("Upheaval"))),
    "LCB Ish" : Unit("LCB Ish", (gs("Loggerhead"), gs("Slide"), gs("Shield Bash"))),
    "LCB Rodya" : Unit("LCB Rodya", (gs("Strike Down"), gs("Axe Combo"), gs("Slay"))),
    "LCB Sinclair" : Unit("LCB Sinclair", (gs("Downward Swing"), gs("Halberd Combo"), gs("Ravaging Cut"))),
    "LCB Outis" : Unit("LCB Outis", (gs("Pulled Blade"), gs("Backslash"), gs("Piercing Thrust"))),
    "LCB Gregor" : Unit("LCB Gregor", (gs("Swipe"), gs("Jag"), gs("Chop Up"))),
    "Liu Rodya" : Unit("Liu Rodya", (gs("Flaming Fists"), gs("Fiery Knifehand-Combust"), gs("Pinpoint Blitz"))),
    "Bl Sang" : Unit("Bl Sang", (gs("Striker's Stance"), gs("Heel Turn"), gs("Flank Trust"))),
    "Wild Cliff" : Unit("Wild Cliff", (gs("Beheading"), gs("Memorial Procession"), gs("Requiem"), gs("O Dullahan…!"), gs("Lament, Mourn, and Despair"))),
    "W Meur" : Unit("W Meur", (gs("Rip(Meursault)"), gs("Energy Cycle(Meursault)"), gs("Energy Current"))),
    "W Faust" : Unit("W Faust", (gs("Energy Cycle"), gs("Leap(Faust)"), gs("Overcharge"))),
    "MC Heath" : Unit("MC Heath", (gs("40S-2 Activation"), gs("Photoelectric Mark"), gs("Photoelectric Harpoon"))),
    "Peq Sang" : Unit("Peq Sang", (gs("Impale"), gs("Relentless Stabbing"), gs("Ambush"))),
    "Zwei Greg" : Unit("Zwei Greg", (gs("Standoff"), gs("Flexible Suppression"), gs("Guardian"))),
    "Cinq Don" : Unit("Cinq Don", (gs("Remise"), gs("Flèche"), gs("Salut!"))),
    "K Hong Lu" : Unit("K Hong Lu", (gs('Impede the Intruder'), gs("Decay Blade"), gs("Excise Target"))),
    "R Meur" : Unit("R Meur", (gs("Weighty Bash"), gs("Demolish"), gs("Rhino Ram"))),
    "Shi Ish" : Unit("Shi Ish", (gs("Flying Sword"), gs("Flashing Strike"), gs("Catch Breath"))),
    "KK Hong Lu" : Unit("KK Hong Lu", (gs("Cleave"), gs("Cloud Cutter"), gs("Cloudburst"))),
    "Zwei Rodya" : Unit("Zwei Rodya", (gs("Careful Obstruction"), gs("Focused Defense"), gs("Subdue Threat"))),
    "Zwei Sinclair" : Unit("Zwei Sinclair", (gs("Baton"), gs("Suppress"), gs("Strong Strike"))),
    "KK Gregor" : Unit("KK Gregor", (gs("Lenticular Rend"), gs("Shadow Cloud"), gs("Shadowcloud Shattercleave"))),
    "Pirate Gregor" : Unit("Pirate Gregor", (gs("Negotiation Start"), gs("Unilateral Business"), gs("Foregone Conclusion"))),
    "KK Rodya" : Unit("KK Rodya", (gs("Sharp Edge"), gs("Scattering Slash"), gs("Sky-clearing Cut"))),
    "Bl Faust" : Unit("Bl Faust", (gs("Moonlit Blade Dance"), gs("Acupuncture"), gs("Red Plum Blossoms Scatter"))),
    "Warp Sang" : Unit("Warp Sang", (gs("Dimensional Slit"), gs("Energy Cycle"), gs("Dimensional Rift"))),
    "Rose Gregor" : Unit("Rose Gregor", (gs("Rev Up"), gs("Grease Chains"), gs("Let's Grind 'Em"))),
    "Cinq Outis" : Unit("Cinq Outis", (gs("Marche"), gs("Punition"), gs("Balestra Fente"))),
    "7 Faust" : Unit("7 Faust", (gs("Predictive Analysis"), gs("Dissect Target"), gs("Profiling"))),
    "Ring Outis" : Unit("Ring Outis", (gs("Dotting"), gs("Sanguine Painting"), gs("Artwork Inspection"))),
    "Dawn Clair" : Unit("Dawn Office Fixer Sinclair", (gs("Fierce Charge"), gs("Sunset Blade"), gs("Stigmatize"), gs("Blazing Strike"))),
    "MB Outis" : Unit("MB Outis", (gs('Ignition'), gs("Detonate Magic Bullet"), gs("Magic Bullet Fire"))),
    "KK Ryo" : Unit("KK Ryoshu", (gs("Focus Strike"), gs("Clean Up"), gs("Lenticular Swirl"))),
    "Bl Don" : Unit("Bl Don", (gs("Draw Of The Sword(Don)"), gs("Blade Arc"), gs("Fare Thee Well!"))),
    "Molar Ish" : Unit("Molar Ish", (gs("Ready to Crush"), gs("Explosive Blast"), gs("Risky Judgement"))),
    "L Don" : Unit("L Don", (gs("I Shall Nibble Thee!"), gs("Flashing Lure"), gs("Whirlwind Om-Nom-Nom!"))),
    "Talisman Sinclair" : Unit("Talisman Sinclair", (gs("Magnify Wound"), gs("Proliferating Talismans"), gs("Rupturing Talisman"))),
    "Butler Ish" : Unit("Butler Ish", (gs("Sweeping Redirection"), gs("Housekeeping"), gs("Restraining Technique"))),
    "W Hong Lu" : Unit("W Hong Lu", (gs("Energy Cycle"), gs("Cleanup Support"), gs("Deploy Charge Barrier"))),
    "Shi Heath" : Unit("Shi Heath", (gs("Extreme Edge"), gs("Flying Sword"), gs("Flashing Strike"))),
    "G Outis" : Unit("G Outis", (gs("Order"), gs("Onslaught Command"), gs("Focus"))),
    "Hook Lu" : Unit("Hook Lu", (gs("Track"), gs("Goin' First"), gs("Rampage"))),
    "Shi Don" : Unit("Shi Don", (gs("Catch Breath"), gs("Dual Strike"), gs("Overbreathe"))),
    "Liu Meur" : Unit("Liu Meur", (gs("Assault"), gs("Stalwart Stance"), gs("Perfected Death Fist"))),
    "LCCB Ryo" : Unit("LCCB Ryo", (gs("Shove"), gs("T.N."), gs("O.O.F."))),
    "Zwei Faust" : Unit("Zwei Faust", (gs("Patrolling"), gs("Client Protection"), gs("Law and Order"))),
    "LCCB Ish" : Unit("LCCB Ish", (gs("Shove"), gs("Quake Rounds"), gs("Suppress"))),
    "NFaust" : Unit("NFaust", (gs("Cackle"), gs("The Gripping"), gs("Execution"))),
    "Slosh Ish" : Unit("Slosh Ish", (gs("It's Heavy...!"), gs("It's Churning...!"), gs("Corrosive Splash"))),
    "7 Sang" : Unit("7 Sang", (gs("Flèche"), gs("Riposte"), gs("Moulinet"))),
    "Dead Meur" : Unit("Dead Meur", (gs("Bat Strike"), gs("Smackdown"), gs("Relentless"))),
    "Molar Sinclair" : Unit("Molar Sinclair", (gs("Fierce Assault"), gs("Steady..."), gs("Gamble"))),
    "NCliff" : Unit("NCliff", (gs("Gawky Nailing"), gs("Puri…fy!"), gs("Infirm Retribution"))),
    "LCCB Rodya" : Unit("LCCB Rodya", (gs("Bludgeon"), gs("Thrust"), gs("Suppress"))),
    "Liu Hong Lu" : Unit("Liu Hong Lu", (gs("Warm Up"), gs("Flowing Flame"), gs("Crimson Blaze Fist"))),
    "Molar Sang" : Unit("Molar Sang", (gs("Stay Calm"), gs("Gamble(Yi Sang)"), gs("Grinding the Molars"))),
    "Cap Ish" : Unit("Cap Ish", (gs("To Me!"), gs("Pursue Them to the End!"), gs("Harpoon of Obsession"))),
    "Liu Gregor" : Unit("Liu Gregor", (gs("Single-point Stab"), gs("Rush Down"), gs("Perfected Palm Strike"))),
    "Butler Faust" : Unit("Butler Faust", (gs("Confiscation"), gs("Interloper Reception"), gs("RA4: Heartseal"))),
    "7Cliff" : Unit("7Cliff", (gs("Intuition"), gs("The Wrap-Up"), gs("Forensics"))),
    "N Don" : Unit("N Don", (gs("Rightful Purge"), gs("Enactment!"), gs("Fanatical Judgement"))),
    "Liu Ryo" : Unit("Liu Ryo", (gs("All-out War"), gs("Fiery Knifehand"), gs("Flame Cleave"))),
    "7 Ryo" : Unit("7 Ryo", (gs("Slash"), gs("Upper Slash"), gs("Swash"))),
    "Rose Meur" : Unit("Rose Meur", (gs("Saddled Tasks"), gs("Forced Break"), gs("Finishing Runup"))),
    "Red Ryo" : Unit("Red Ryo", (gs("Both of You, Shut Up"), gs("S.H. / S.F."), gs("Skullbuster"), gs("Serious Skullbuster"))),
    "Yuro Ryo" : Unit("Yuro Ryo", (gs("Got a Screw Loose?"), gs("Compression Wind-up Spanner"), gs("Percussive Maintenance"))),
    "LCR Faust" : Unit("LCR Faust", (gs("Sole Strike"), gs("Deep Cuts"), gs("Opportunistic Slash"))),
    "Rose Rodya" : Unit("Rose Rodya", (gs("Rev Up"), gs("Vibration Compression"), gs("Let's Rack Up Some Scores"))),
    "Bl Outis" : Unit("Bl Outis", (gs("Draw of the Sword(Outis)"), gs("Acupuncture(Outis)"), gs("Decisive Dive"))),
    "G Gregor" : Unit("G Gregor", (gs("Hack"), gs("Dismember"), gs("Eviscerate"))),
    "Chef Gregor" : Unit("Chef Gregor", (gs("Keep It Fresh"), gs("You Fresh Enough?"), gs("Butcher Viand"))),
    "Devyat Rodya" : Unit("Devyat Rodya", (gs("CT - DK"), gs("CT - GR"), gs("I Trust Ya, Polu!"))),
    "Deici Meur" : Unit("Deici Meur", (gs("Studious Dedication"), gs("Moment of Erudition"), gs("Scorch Knowledge"))),
    "Mariachi Sinclair" : Unit("Mariachi Sinclair", (gs("Baile y Rola"), gs("Danza de Pasión"), gs("Pañata Party"))),
    "Heir Gregor" : Unit("Heir Gregor", (gs("Sabre Slash"), gs("Remise"), gs("Nightmare Hunt"))),
    "Zwei Ish" : Unit("Zwei Ish", (gs("Zwei Knight's Greatsword Form"), gs("Can't Let You Through."), gs("Ward"))),
    "Deici Sang" : Unit("Deici Sang", (gs("Expend Knowledge"), gs("Seal Shut"), gs("Grace of Knowledge"))),
    "Bush Sang" : Unit("Bush Sang", (gs("Sprouting Bud"), gs("Moment's Floral Breeze"), gs("Bloodsteeped Scent"))),
    "N Meur" : Unit("N Meur", (gs("Drive"), gs("You Are Cleansed of Sin"), gs("Annihilate Heretics"))),
    "N Rodya" : Unit("N Rodya", (gs("Devoted Hammering"), gs("Zealous Purge"), gs("Ironclad Retribution"))),
    "Bl Sinclair" : Unit("Bl Sinclair", (gs("Slice then Stab"), gs("Slash Series"), gs("To Claim Their Bones"))),
    "Mid Meur" : Unit("Mid Meur", (gs("We Remember"), gs("Chains of Loyalty"), gs("Recording"))),
    "7 Outis" : Unit("7 Outis", (gs("Predictive Analysis"), gs("Field Command"), gs("Exploit the Gap"))),
    "Oufi Heath" : Unit("Oufi Heath", (gs("Execution Advised"), gs("Final Warning"), gs("Execution Sentencing"))),
    "Zwei Sinclair West" : Unit("Zwei Sinclair West", (gs("Suppressing."), gs("Combat Preparation"), gs("Fence"))),
    "Cinq Meur" : Unit("Cinq Meur", (gs("Allez"), gs("Fente"), gs("Salut"))),
    "T Rodya" : Unit("T Rodya", (gs("Prepare to Collect"), gs("T Corp. Martial Suppression"), gs("Execute Collections"))),
    "T Don" : Unit("T Don", (gs("Let Us Prepare to Collect"), gs("T Corp. Accelerated Amputator"), gs("I Command Thee, Halt!"))),
    "Butterfly Sang" : Unit("Butterfly Sang", (gs("Celebration for the Departed"), gs("Solemn Lament for the Living"), gs("Goodbye Now, A Sorrow In You"))),
    "Yuro Lu" : Unit("Yuro Lu", (gs("Deduction Start"), gs("Morph Cane Technique"), gs("You're the Culprit!"))),
    "Fang Lu" : Unit("Fang Lu", (gs("Slam"), gs("Bonecrusher"), gs("A Cheerful Hunt's End"))),
    "Barber Outis" : Unit("Barber Outis", (gs("Sewing"), gs("Scission"), gs("I'll Make You a New Dress!"))),
    "Priest Gregor" : Unit("Priest Gregor", (gs("Sacrifice for the Family"), gs("Suffocating Guilt"), gs("The Unforgivable Sin"))),
    "Dulcinea Rodya" : Unit("Dulcinea Rodya", ((gs("Begone…")), (gs("In Finely Ground Mistfall")), (gs("The Festival Will End")), (gs("A-DQHA - The Finale")), (gs("DQHA 15: Parasol"))))
    }