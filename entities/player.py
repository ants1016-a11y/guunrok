import copy
import random
from infra.config import BASE_ATK, BASELINE_ATK


class Player:
    def __init__(self, name="무인"):
        self.name = name
        self.stats = {
            "근골": 10,
            "심법": 10,
            "외공": 10,
            "경공": 10,
            "자질": 10,
            "행운": 10,
        }
        self.base_max_hp = 100
        self.base_max_energy = 5
        self.energy_regen = 3
        self.gold = 0
        self.xp = 0
        # [신규] 누적 경험치 및 깨달음 단계 추가
        self.total_xp = 0  # 평생 획득한 총 XP
        self.enlightenment_idx = 0  # 현재 몇 번째 깨달음 단계인지 (0부터 시작)
        self.win_streak = 0

        # [신규] 객잔 버프 및 상태 관리 변수
        self.inn_buff = (
            None  # 식사 효과 저장: {"type": "atk/hp/def", "val": 0, "name": ""}
        )
        self.daily_trained = False  # 객잔 방문 시 1회 수련 제한 확인용

        self.temp_max_energy_bonus = 0  # [추가] 전투 중 쌓인 최대 내공 보너스
        self.recalculate_stats()
        self.hp = self.max_hp
        self.energy = self.max_energy
        self.defense = 0

        self.deck = []
        self.hand = []
        self.discard_pile = []
        self.draw_pile = []

    def recalculate_stats(self):
        """모든 수치를 현재 스탯에 맞춰 동기화합니다."""
        # 1. 기혈: 근골 중심
        self.max_hp = self.base_max_hp + ((self.stats["근골"] - 10) * 10)

        # 2. 내공: 심법 비선형 스케일
        v = self.stats["심법"]
        if v <= 15:
            bonus = v - 10
        elif v <= 22:
            bonus = 5 + (v - 15) // 2
        else:
            bonus = 5 + 3 + (v - 22) // 3

        enlighten_bonus = getattr(self, "temp_max_energy_bonus", 0)
        self.max_energy = self.base_max_energy + bonus + enlighten_bonus

        # 3. 공격력: 외공 중심, 근골 보조
        self.attack_power = int(BASE_ATK + self.stats["외공"] * 1.0 + self.stats["근골"] * 0.1)
        self.attack_power_bonus = max(0, self.attack_power - BASELINE_ATK)

        # 4. 방어 시작치: 근골 중심, 외공 보조
        self.base_defense = int(self.stats["근골"] * 0.6 + self.stats["외공"] * 0.2)

        # 5. 내공 회복량 (합 시작 시 적용)
        self.current_regen = self.energy_regen + (self.stats["심법"] // 5)

        # 6. 회피율: 경공 기반 (최대 25%)
        self.evasion = min(0.25, 0.05 + self.stats["경공"] * 0.007)

        # 7. 도주 확률: 경공 기반 (최대 60%)
        self.flee_chance = min(60.0, 10.0 + self.stats["경공"] * 1.2)

        # 8. 합 종료 회복
        self.clash_hp_regen = min(3, self.stats["근골"] // 10)
        self.clash_en_regen = min(2, self.stats["심법"] // 12)

    def initialize_deck(self, registry):
        self.deck = []
        base_cards = ["복호장", "육합권", "포천삼", "삼재공", "유운지"]
        for card_id in base_cards:
            if card_id in registry:
                self.deck.append(copy.deepcopy(registry[card_id]))
        random.shuffle(self.deck)
        self.hand = self.deck[:5]

    def draw_cards(self, count):
        for _ in range(count):
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                self.draw_pile = list(self.discard_pile)
                self.discard_pile = []
                random.shuffle(self.draw_pile)
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop())

    def start_battle(self, registry):
        """[핵심 수선] 전투 시작 시 객잔에서 먹은 음식의 '약빨(Buff)'을 적용합니다."""
        self.temp_max_energy_bonus = 0  # [추가] 보너스 초기화
        self.recalculate_stats()  # 초기화된 값으로 다시 계산

        # 1. 객잔 버프 효과 적용 (1회성)
        if self.inn_buff:
            b_type = self.inn_buff.get("type")
            val = self.inn_buff.get("val", 0)

            if b_type == "energy":  # 술: 내공 폭발
                self.energy += val
                # (참고: max_energy를 넘겨서 시작할 수 있게 함)
            elif b_type == "hp_max":  # 음식: 맷집 강화
                self.max_hp += val
                self.hp += val  # 늘어난 통만큼 현재 체력도 채워줌

        self.defense = 0
        self.draw_pile = list(self.deck)
        import random

        random.shuffle(self.draw_pile)
        self.hand = []
        self.discard_pile = []
        self.draw_cards(5)

    def add_defense(self, amount):
        self.defense += amount
        return amount

    def take_damage(self, dmg):
        # 경공 회피 판정
        if random.random() < getattr(self, "evasion", 0.0):
            return 0
        actual = max(0, dmg - self.defense)
        self.defense = max(0, self.defense - dmg)
        self.hp = max(0, self.hp - actual)
        return actual

    def apply_clash_regen(self):
        """합 종료 시 근골 기혈 회복 + 심법 내공 추가 보너스 (배틀 첫 합 제외)."""
        hp_regen = getattr(self, "clash_hp_regen", 0)
        if hp_regen > 0:
            self.hp = min(self.max_hp, self.hp + hp_regen)
        en_bonus = getattr(self, "clash_en_regen", 0)
        if en_bonus > 0:
            self.energy += en_bonus  # max_energy 초과 허용 (심법 보너스)

    def start_turn_regen(self):
        """[수선] 턴 시작 시 '차(Tea)'를 마셨다면 정신을 집중해 방어도를 얻습니다."""
        regen = self.energy_regen + (self.stats["심법"] // 5)
        self.energy = min(self.max_energy, self.energy + regen)

        # 차(Tea) 버프: 매 턴 방어도 자동 획득
        if self.inn_buff and self.inn_buff.get("type") == "def_turn":
            bonus_def = self.inn_buff.get("val", 0)
            self.defense += bonus_def

    def get_next_enlightenment_threshold(self):
        """[신규] 가속 성장 공식을 이용해 다음 깨달음까지 필요한 총 경험치를 계산합니다."""
        base = 500  # 첫 번째 깨달음 기준점
        difficulty = 200  # 단계별 증가 가중치
        n = self.enlightenment_idx

        # 공식: Base * (n + 1) + Difficulty * (n * (n + 1) / 2)
        threshold = int(base * (n + 1) + difficulty * (n * (n + 1) / 2))
        return threshold

    # --- [저장 기능 추가] 객체 직렬화/역직렬화 ---
    def to_dict(self):
        """플레이어 데이터를 저장 가능한 딕셔너리 형태로 변환"""
        return {
            "name": self.name,
            "stats": self.stats,
            "hp": self.hp,
            "gold": self.gold,
            "xp": self.xp,
            "total_xp": self.total_xp,
            "enlightenment_idx": self.enlightenment_idx,
            "win_streak": self.win_streak,
            "inn_buff": self.inn_buff,
            "daily_trained": self.daily_trained,
            # 덱 저장 시 카드 이름과 숙련도만 저장
            "deck": [{"name": c.name, "mastery": c.mastery} for c in self.deck],
        }

    @classmethod
    def from_dict(cls, data, registry):
        """저장된 딕셔너리에서 플레이어 객체 복원"""
        p = cls(data["name"])
        p.stats = data["stats"]
        p.hp = data["hp"]
        p.gold = data["gold"]
        p.xp = data["xp"]
        p.total_xp = data.get("total_xp", 0)
        p.enlightenment_idx = data.get("enlightenment_idx", 0)
        p.win_streak = data["win_streak"]
        p.inn_buff = data["inn_buff"]
        p.daily_trained = data.get("daily_trained", False)

        # 덱 복원 로직
        p.deck = []
        for c_data in data["deck"]:
            card_name = c_data["name"]
            if card_name in registry:
                # 카드 생성 및 숙련도 복구
                new_card = copy.deepcopy(registry[card_name])
                new_card.mastery = c_data["mastery"]
                p.deck.append(new_card)

        p.recalculate_stats()
        return p
