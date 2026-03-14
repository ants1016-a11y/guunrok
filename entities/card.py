from enum import Enum


class CardType(Enum):
    ATTACK = "공격"
    DEFENSE = "방어"
    SKILL = "기술"
    DEBUFF = "약화"


class Card:
    def __init__(
        self,
        name,
        card_type,
        base_cost,
        description,
        base_value,
        effect_func,
        mastery_max=5,
    ):
        self.name = name
        self.type = card_type
        self.base_cost = base_cost
        self.description = description
        self.base_value = base_value
        self.effect_func = effect_func

        self.mastery = 1  # 현재 단계 (성)
        self.mastery_max = mastery_max

    def get_upgrade_cost(self):
        """[신설] 다음 단계로 깨달음을 얻기 위해 필요한 XP: $100 \times mastery^{2}$"""
        return 100 * (self.mastery**2)

    def upgrade(self):
        """[신설] 단계를 높이고 위력을 영구히 증폭시킵니다."""
        if self.mastery < self.mastery_max:
            self.mastery += 1
            return True
        return False

    def get_current_value(self):
        """[교정] 숙련도(성)가 높을수록 위력이 20%씩 강해집니다."""
        multiplier = 1 + (self.mastery - 1) * 0.2
        return int(self.base_value * multiplier)
