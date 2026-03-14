from collections import deque
import random

# 기본 제원 상수
BASE_HP = 40
BASE_ATK = 7


class Enemy:
    def __init__(self, name, hp=BASE_HP, atk=BASE_ATK, level=1):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.level = level
        self.defense = 0
        self.intent_queue = deque()

    def take_damage(self, amount):
        """방어도를 고려하여 기혈 피해를 입습니다."""
        actual_damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        # 구버전 규칙: 받은 피해만큼 적의 방어도도 소모됩니다.
        self.defense = max(0, self.defense - amount)
        return actual_damage

    def is_alive(self):
        """생존 여부를 확인합니다."""
        return self.hp > 0

    def execute_single_intent(self, intent, player):
        """
        [신규] BattleManager가 한 합씩 계산할 때 호출하는 적의 단일 의도 실행기.
        (피해량, 방어증가량, 서사 메시지)를 반환합니다.
        """
        import random

        dmg_dealt = 0
        def_gained = 0

        if intent == "공격":
            dmg = self.atk + random.randint(-1, 2)
            dmg_dealt = player.take_damage(dmg)
            msg = f"혈풍 같은 일격이 파고든다! (피해 {dmg_dealt})"

        elif intent == "강공":
            dmg = int(self.atk * 1.5)
            dmg_dealt = player.take_damage(dmg)
            msg = f"패왕의 기세가 눌러온다…! (중상 {dmg_dealt})"

        elif intent == "방어":
            def_val = self.atk + random.randint(3, 7)
            self.defense += def_val
            def_gained = def_val
            msg = f"철벽의 호신강기가 둘러진다. (방어 +{def_val})"

        elif intent == "약화":
            drain = 2
            player.energy = max(0, player.energy - drain)
            msg = f"탁한 기운이 경맥을 어지럽힌다. 내공이 {drain} 흩어진다. (약화)"

        else:
            msg = f"적이 「{intent}」의 기운을 갈무리한다."

        return dmg_dealt, def_gained, msg
