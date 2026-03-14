class Actor:
    """플레이어와 적의 공통 기반 클래스"""

    def __init__(self, name, hp, atk):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = 0

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        actual = max(0, amount - self.defense)
        self.defense = max(0, self.defense - amount)
        self.hp = max(0, self.hp - actual)
        return actual

    def add_defense(self, amount):
        self.defense += amount
        return amount
