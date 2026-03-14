# content/registry.py

CARD_REGISTRY = {}
ENEMY_REGISTRY = {}


def register_card(card_id, card_obj):
    CARD_REGISTRY[card_id] = card_obj


def register_enemy(enemy_id, enemy_class):
    ENEMY_REGISTRY[enemy_id] = enemy_class


def get_card(card_id):
    return CARD_REGISTRY.get(card_id)
