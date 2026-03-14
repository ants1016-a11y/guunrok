# entities/player.py
from infra.config import *


class Player:
    def __init__(self, name="무인"):
        self.name = name
        self.hp = BASE_HP
        self.max_hp = BASE_HP
        self.defense = 0
        self.energy = BASE_ENERGY
        self.max_energy = BASE_ENERGY
        self.energy_regen = ENERGY_REGEN  # 버그 해결
        self.food_buff = None
        self.hand = []

    def get_effective_defense(self):
        """음식 버프(+5)가 포함된 실제 방어력을 반환합니다."""
        bonus = self.food_buff.get("val", 0) if self.food_buff else 0
        return self.defense + bonus

    def take_damage(self, amount: int):  # NameError 해결
        eff_def = self.get_effective_defense()
        actual_dmg = max(1, amount - eff_def)
        self.hp -= actual_dmg
        return actual_dmg
