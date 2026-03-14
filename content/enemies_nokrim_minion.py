"""
content/enemies_nokrim_minion.py
녹림 산적 졸개 — 잡기술(돌팔매/주먹질) + 무공 1수 구조.
"""

import random
from entities.enemy import Enemy
from content.registry import register_enemy

# ── 데이터 분리: 무공 후보 ──────────────────────────────────────────────────────
MINION_SPECIAL_POOL = ["난도질", "멱살잡이"]

# ── 5합 패턴 템플릿 (SPECIAL 토큰을 생성 시 무공으로 치환) ───────────────────────
# 제약: SPECIAL은 각 패턴에 정확히 1회만 등장
MINION_TEMPLATES = [
    ["돌팔매", "주먹질", "주먹질", "SPECIAL", "주먹질"],  # 패턴 A
    ["주먹질", "SPECIAL", "주먹질", "주먹질", "주먹질"],  # 패턴 B
    ["돌팔매", "주먹질", "SPECIAL", "주먹질", "돌팔매"],  # 패턴 C
]


class NokrimMinion(Enemy):
    """
    녹림 산적 졸개.
    생성 시 무공 1수와 5합 패턴이 확정됩니다.
    외부에서 name/hp/atk를 오버라이드해도 패턴 구조는 그대로 유지됩니다.
    """

    def __init__(self, level: int = 1):
        super().__init__(name="산채 졸개", hp=40, atk=7, level=level)
        # 생성 시 무공 1개 확정 ─ 이후 변경 없음
        self.special_move: str = random.choice(MINION_SPECIAL_POOL)
        # 패턴 확정 (SPECIAL 토큰 → 실제 무공명으로 치환)
        template = random.choice(MINION_TEMPLATES)
        self._pattern = [
            self.special_move if tok == "SPECIAL" else tok for tok in template
        ]
        self._hap_count = 0  # refresh_intents 호출 횟수

    # ── 의도 갱신 ───────────────────────────────────────────────────────────────
    def refresh_intents(self):
        """1합: 고정 패턴(패턴 파악 유도), 2합 이후: 같은 무공 풀을 랜덤 순서로."""
        self.intent_queue.clear()
        if self._hap_count == 0:
            # 첫 합은 고정 순서 — 적의 패턴을 파악할 기회
            self.intent_queue.extend(self._pattern)
        else:
            # 이후 합은 동일 무공 풀을 섞어서 — 획일화 방지
            shuffled = list(self._pattern)
            random.shuffle(shuffled)
            self.intent_queue.extend(shuffled)
        self._hap_count += 1

    # ── 의도 실행 ───────────────────────────────────────────────────────────────
    def execute_single_intent(self, intent: str, player):
        dmg_dealt = 0
        def_gained = 0

        if intent == "돌팔매":
            dmg = max(1, self.atk - 3) + random.randint(0, 2)
            dmg_dealt = player.take_damage(dmg)
            msg = f"산적이 돌을 집어 던진다! ({dmg_dealt}의 피해)"

        elif intent == "주먹질":
            dmg = self.atk + random.randint(-1, 2)
            dmg_dealt = player.take_damage(dmg)
            msg = f"거친 주먹이 턱을 노린다! ({dmg_dealt}의 피해)"

        elif intent == "난도질":
            # 초식 1수 — 주먹질보다 강하지만 절기는 아님
            dmg = self.atk + 4
            dmg_dealt = player.take_damage(dmg)
            msg = f"어설픈 도날이 허공을 찢는다! ({dmg_dealt}의 피해)"

        elif intent == "멱살잡이":
            # 기세 방해 — 내공 1 소진 + 약한 타격
            drain = 1
            player.energy = max(0, player.energy - drain)
            dmg = max(1, self.atk // 2)
            dmg_dealt = player.take_damage(dmg)
            msg = (
                f"멱살을 틀어쥐고 균형을 무너뜨린다! "
                f"(내공 -{drain}, 피해 {dmg_dealt})"
            )

        else:
            return super().execute_single_intent(intent, player)

        return dmg_dealt, def_gained, msg


# ── 레지스트리 등록 ────────────────────────────────────────────────────────────
register_enemy("nokrim_minion", NokrimMinion)
