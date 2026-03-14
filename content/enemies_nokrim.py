import random
from entities.enemy import Enemy
from content.registry import register_enemy


class MaCheonGwang(Enemy):
    def __init__(self):
        super().__init__(name="녹림왕 마천광", hp=320, atk=20, level=10)
        self.is_overloaded = False  # 근육 과부하 상태 (HP 40% 이하)
        self.is_immovable = False  # 천악 부동체 활성화 여부
        self._cycle = 0  # 패턴 사이클 카운터
        # refresh_intents는 prepare_enemy_intents()가 호출함 (중복 호출 방지)

    # ──────────────────────────────────────────────────────────────────────────
    # 패턴 기반 의도 큐
    # 사이클 1: 수비 → 강타 → 빈틈(회복) → 폭발 → 필살기 예고
    # 사이클 2+: 수비 → 내공드레인 → 빈틈(회복) → 강타×2 → 필살기
    # ──────────────────────────────────────────────────────────────────────────
    def refresh_intents(self):
        self.intent_queue.clear()
        if self._cycle == 0:
            # 첫 사이클 ─ 고정 패턴(패턴 파악 유도)
            pattern = [
                "천악 부동체",  # 合1: 방어 쌓기 → 공격 효율↓ (빈틈 아님)
                "살웅 괴력권",  # 合2: 강타
                "운기 조식",  # 合3: 回復 = 빈틈! 이때 집중 공격
                "황산 대참",  # 合4: 강타
                "녹림 파천참",  # 合5: 필살기 예고 — 방어 준비 필수
            ]
        else:
            # 이후 사이클 ─ 같은 무공 풀을 랜덤 순서로(획일화 방지)
            pattern = [
                "천악 부동체",
                "패왕의 포효",
                "운기 조식",
                "살웅 괴력권",
                "녹림 파천참",
            ]
            random.shuffle(pattern)
        self.intent_queue.extend(pattern)
        self._cycle += 1

    # ──────────────────────────────────────────────────────────────────────────
    # 피해 처리: 천악부동체 + 근육 과부하
    # ──────────────────────────────────────────────────────────────────────────
    def take_damage(self, amount):
        if self.is_immovable:
            amount = max(0, amount - 12)  # 천악부동체: 피해 12 경감

        actual_damage = super().take_damage(amount)

        # 근육 과부하: HP 40% 이하에서 발동 — 공격 2배, 방어 불가
        if self.hp <= self.max_hp * 0.4 and not self.is_overloaded:
            self.is_overloaded = True
            self.atk = int(self.atk * 1.8)
            self.defense = 0
            self.is_immovable = False  # 과부하 시 부동체 해제

        return actual_damage

    # ──────────────────────────────────────────────────────────────────────────
    # 의도 실행
    # ──────────────────────────────────────────────────────────────────────────
    def execute_single_intent(self, intent, player):
        dmg_dealt = 0
        def_gained = 0
        msg = ""

        # 과부하 상태: 방어 기동 불가
        if self.is_overloaded:
            self.defense = 0

        if intent == "천악 부동체":
            self.is_immovable = True
            if not self.is_overloaded:
                def_val = 30 + self.level * 2
                self.defense += def_val
                def_gained = def_val
                msg = (
                    f"마천광이 [천악 부동체]를 취합니다. "
                    f"강기 {def_val}을 두르고 피해를 {12} 경감합니다!"
                )
            else:
                msg = (
                    "마천광이 부동체를 취하려 했으나, 과부하된 근육이 비명을 지릅니다!"
                )

        elif intent == "살웅 괴력권":
            dmg = self.atk + 8
            dmg_dealt = player.take_damage(dmg)
            msg = f"마천광의 [살웅 괴력권]! 곰의 목을 비틀던 괴력이 {dmg_dealt}의 피해를 입힙니다!"

        elif intent == "황산 대참":
            dmg = int(self.atk * 1.6)
            dmg_dealt = player.take_damage(dmg)
            msg = f"거대한 도가 대기를 가릅니다! [황산 대참]으로 {dmg_dealt}의 피해!"

        elif intent == "패왕의 포효":
            drain = 3
            player.energy = max(0, player.energy - drain)
            msg = (
                f"마천광이 전장을 울리는 포효를 내지릅니다! 내공이 {drain} 흩어집니다."
            )

        elif intent == "녹림 파천참":
            dmg = self.atk * 3
            dmg_dealt = player.take_damage(dmg)
            msg = f"전설의 비기 [녹림 파천참]! 하늘을 가르는 섬광이 {dmg_dealt}의 피해를 입혔습니다!"

        elif intent == "운기 조식":
            heal_amount = 30
            self.hp = min(self.max_hp, self.hp + heal_amount)
            # 부동체 일시 해제 — 이 합의 빈틈
            self.is_immovable = False
            msg = (
                f"마천광이 숨을 고르며 [운기 조식]에 들어갑니다. (기혈 +{heal_amount})"
                "\n  ▶ 부동체가 풀린 빈틈! 집중 공격의 기회입니다."
            )

        elif intent == "기본 공격":
            dmg = self.atk + random.randint(-2, 4)
            dmg_dealt = player.take_damage(dmg)
            msg = f"마천광이 묵직한 권각술로 {dmg_dealt}의 피해를 입힙니다."

        elif intent == "기본 방어":
            if not self.is_overloaded:
                def_val = self.atk + 8
                self.defense += def_val
                def_gained = def_val
                msg = f"마천광이 공격을 흘려내며 방어도 {def_val}을 얻습니다."
            else:
                msg = "마천광이 방어하려 했으나 과부하로 자세가 무너집니다!"

        else:
            return super().execute_single_intent(intent, player)

        return dmg_dealt, def_gained, msg


# 레지스트리 등록
register_enemy("boss_macheon", MaCheonGwang)
