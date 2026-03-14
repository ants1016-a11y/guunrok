import random
from entities.card import Card, CardType
from content.registry import register_card

# --- [정예 무공 효과 함수] ---


def effect_samjae_gong(player, enemy, card):
    breakthrough_val = 1 + (card.mastery // 3)
    player.temp_max_energy_bonus += breakthrough_val
    player.recalculate_stats()
    player.energy = min(player.max_energy, player.energy + breakthrough_val)
    return f"✨ 삼재공 돌파! 내공의 그릇이 {breakthrough_val}만큼 커졌습니다."


def effect_yukhap_gwon(player, enemy, card):
    dmg = card.base_value + getattr(player, "attack_power_bonus", 0)
    actual = enemy.take_damage(dmg)
    return f"⚔️ {card.name}: {actual}의 피해를 입혔습니다."


def effect_pocheon_sam(player, enemy, card):
    base = card.base_value
    defense = random.randint(base, base + 4)
    player.add_defense(defense)
    return f"🛡️ {card.name}: 호신강기를 {defense}만큼 굳혔습니다."


def effect_bokho_gwon(player, enemy, card):
    dmg = card.base_value + getattr(player, "attack_power_bonus", 0)
    actual = enemy.take_damage(dmg)
    return f"🐅 {card.name}: 중후한 장력이 {actual}의 피해를 적중시켰습니다!"


def effect_yuun_ji(player, enemy, card):
    debuff_val = 5
    enemy.atk = max(1, enemy.atk - debuff_val)
    return f"☁️ {card.name}: 적의 기세를 {debuff_val}만큼 꺾어 공격력을 약화시켰습니다."


# --- [UI 버튼 전용 기본 초식 효과 함수] ---
# 이들은 덱에 포함되지 않으므로, 카드 이름 앞에 [기초] 등을 붙여 구분할 수 있습니다.


def effect_basic_attack(player, enemy, card):
    dmg = 5 + getattr(player, "attack_power_bonus", 0)
    actual = enemy.take_damage(dmg)
    return f"⚔️ 기본 공격: {actual}의 피해를 입혔습니다."


def effect_basic_defense(player, enemy, card):
    defense = 5
    player.add_defense(defense)
    return f"🛡️ 기본 방어: 호신강기를 {defense}만큼 굳혔습니다."


def effect_meditation(player, enemy, card):
    recovery = 2
    player.energy = min(player.max_energy, player.energy + recovery)
    return f"🧘 운기조식: 내공을 {recovery}만큼 회복하여 기세를 가다듬었습니다."


# --- [초식 등록] ---


def init_basic_cards():
    """
    [수선] 기본 3종은 UI 버튼 운용을 위해 등록은 유지하되,
    Player.initialize_deck의 명단에서는 제외되어 카드로 드로우되지 않게 합니다.
    """
    # 0. UI 전용 기초 초식 (덱에는 포함되지 않음)
    register_card(
        "기본 공격",
        Card(
            "기본 공격",
            CardType.ATTACK,
            0,
            "기초적인 타격",
            5,
            effect_func=effect_basic_attack,
        ),
    )
    register_card(
        "기본 방어",
        Card(
            "기본 방어",
            CardType.DEFENSE,
            0,
            "기초적인 방어",
            5,
            effect_func=effect_basic_defense,
        ),
    )
    register_card(
        "운기조식",
        Card(
            "운기조식",
            CardType.SKILL,
            0,
            "내공 2 회복",
            0,
            effect_func=effect_meditation,
        ),
    )

    # 1. 정예 5대 초식 (실제 덱 구성 품목)
    register_card(
        "삼재공",
        Card(
            "삼재공",
            CardType.SKILL,
            1,
            "내공 그릇 확장",
            1,
            effect_func=effect_samjae_gong,
        ),
    )
    register_card(
        "육합권",
        Card(
            "육합권",
            CardType.ATTACK,
            2,
            "8~12의 무작위 피해",
            12,
            effect_func=effect_yukhap_gwon,
        ),
    )
    register_card(
        "포천삼",
        Card(
            "포천삼",
            CardType.DEFENSE,
            2,
            "8~12의 호신강기",
            8,
            effect_func=effect_pocheon_sam,
        ),
    )
    register_card(
        "복호장",
        Card(
            "복호장",
            CardType.ATTACK,
            4,
            "18~25의 파괴적 피해",
            18,
            effect_func=effect_bokho_gwon,
        ),
    )
    register_card(
        "유운지",
        Card(
            "유운지",
            CardType.SKILL,
            3,
            "적 공격력 5 감소",
            5,
            effect_func=effect_yuun_ji,
        ),
    )


init_basic_cards()
