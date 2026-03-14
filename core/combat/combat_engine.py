# core/combat/combat_engine.py
class CombatEngine:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

    def resolve_turn(self, player_card):
        """플레이어의 초식과 적의 예독된 초식이 격돌합니다."""
        if not self.enemy.intent_queue:
            return "적의 기력이 다했습니다."

        # 적의 5수 중 첫 번째 수를 꺼냄 (오수 예독 시스템)
        enemy_intent = self.enemy.intent_queue.popleft()

        # 여기서 플레이어 카드 효과와 적의 의도를 계산하여 데미지 판정
        # (이 로직은 나중에 상세히 구현하겠습니다)
