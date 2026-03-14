import random
from collections import deque
from entities.enemy import Enemy
from content.registry import register_enemy


class HyulgyoJaGaek(Enemy):
    """혈교 자객 — 암기와 독을 쓰는 빠른 자객. 강공과 약화를 자주 구사한다."""

    def __init__(self, level=1):
        super().__init__(name="혈교 자객", hp=55, atk=13, level=level)
        self._poison_stacks = 0

    def refresh_intents(self):
        self.intent_queue.clear()
        pool = ["공격", "강공", "약화", "공격", "독침"]
        random.shuffle(pool)
        for i in range(5):
            self.intent_queue.append(pool[i % len(pool)])

    def execute_single_intent(self, intent, player):
        dmg_dealt = 0
        def_gained = 0

        if intent == "독침":
            drain = 3
            player.energy = max(0, player.energy - drain)
            dmg = int(self.atk * 0.6)
            dmg_dealt = player.take_damage(dmg)
            msg = f"독침이 혈도를 파고든다! 기혈 -{dmg_dealt}, 내공 -{drain}이 흩어진다."
        else:
            return super().execute_single_intent(intent, player)

        return dmg_dealt, def_gained, msg


class HyulgyoGosu(Enemy):
    """혈교 고수 — 혈공과 절식을 번갈아 쓰는 중간 보스."""

    MOVESET = ["혈공", "혈공", "공격", "방어", "절식"]

    def __init__(self, level=1):
        super().__init__(name="혈교 고수", hp=90, atk=16, level=level)

    def refresh_intents(self):
        self.intent_queue.clear()
        pool = list(self.MOVESET)
        random.shuffle(pool)
        for i in range(5):
            self.intent_queue.append(pool[i % len(pool)])

    def execute_single_intent(self, intent, player):
        dmg_dealt = 0
        def_gained = 0

        if intent == "혈공":
            dmg = int(self.atk * 1.4)
            dmg_dealt = player.take_damage(dmg)
            msg = f"[혈공] 붉은 기운이 터져나와 {dmg_dealt}의 피해를 준다!"
        elif intent == "절식":
            def_val = self.atk + 15
            self.defense += def_val
            def_gained = def_val
            msg = f"[절식] 숨을 고르며 호신강기를 {def_val} 끌어올린다."
        else:
            return super().execute_single_intent(intent, player)

        return dmg_dealt, def_gained, msg


class HyulgyoJangro(Enemy):
    """혈교 장로 — 챕터 3 보스. 혈마공과 불멸진을 구사한다."""

    MOVESET = [
        "혈마강타", "혈마강타",
        "불멸진",
        "혈천만상",
        "공격", "방어",
        "흡혈",
    ]

    def __init__(self):
        super().__init__(name="혈교 장로 혈마도", hp=500, atk=24, level=15)
        self.is_immortal = False

    def refresh_intents(self):
        self.intent_queue.clear()
        pool = list(self.MOVESET)
        random.shuffle(pool)
        for i in range(5):
            self.intent_queue.append(pool[i % len(pool)])

    def take_damage(self, amount):
        if self.is_immortal:
            amount = max(0, amount - 20)
        actual = super().take_damage(amount)
        return actual

    def execute_single_intent(self, intent, player):
        dmg_dealt = 0
        def_gained = 0

        if intent == "혈마강타":
            dmg = self.atk + 10
            dmg_dealt = player.take_damage(dmg)
            msg = f"[혈마강타] 혈기로 뭉친 주먹이 {dmg_dealt}의 피해를 입힌다!"
        elif intent == "불멸진":
            self.is_immortal = True
            def_val = 40
            self.defense += def_val
            def_gained = def_val
            msg = "[불멸진] 혈교 비전이 펼쳐진다! 피해가 20 감소하고 강기 +40."
        elif intent == "혈천만상":
            dmg = self.atk * 2
            dmg_dealt = player.take_damage(dmg)
            drain = 4
            player.energy = max(0, player.energy - drain)
            msg = f"[혈천만상] 하늘을 뒤덮는 혈기! {dmg_dealt}의 피해, 내공 -{drain}."
        elif intent == "흡혈":
            dmg = int(self.atk * 0.8)
            dmg_dealt = player.take_damage(dmg)
            heal = dmg_dealt // 2
            self.hp = min(self.max_hp, self.hp + heal)
            msg = f"[흡혈] 기혈을 빨아들여 {dmg_dealt} 피해 주고 자신은 {heal} 회복!"
        else:
            return super().execute_single_intent(intent, player)

        return dmg_dealt, def_gained, msg


register_enemy("hyulgyo_jaGaek", HyulgyoJaGaek)
register_enemy("hyulgyo_gosu", HyulgyoGosu)
register_enemy("hyulgyo_jangro", HyulgyoJangro)
