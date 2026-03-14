import random
from entities.card import Card, CardType
from content.registry import register_card


# --- [고급 무공 효과 함수] ---


def effect_yongho_gwon(player, enemy, card):
    """용호권: 두 번 연속 타격 (각 base_value의 60%)"""
    hit = int((card.base_value + getattr(player, "attack_power_bonus", 0)) * 0.6)
    total = 0
    for _ in range(2):
        total += enemy.take_damage(hit)
    return f"🐉 {card.name}: 용호 연격! 합계 {total}의 피해를 입혔습니다."


def effect_cheol_sa_jang(player, enemy, card):
    """철사장: 방어 + 반격 (방어도 쌓고 적 방어도 직접 깎음)"""
    def_gain = card.base_value
    player.add_defense(def_gain)
    strip = max(0, int(card.base_value * 0.5))
    enemy.defense = max(0, enemy.defense - strip)
    return f"🛡️ {card.name}: 호신강기 +{def_gain}, 적 강기 {strip} 분쇄."


def effect_naega_ilso(player, enemy, card):
    """내가일소: 내공으로 기혈 회복"""
    heal = card.base_value
    before = player.hp
    player.hp = min(player.max_hp, player.hp + heal)
    actual = player.hp - before
    return f"💚 {card.name}: 기혈 {actual}을 회복했습니다."


def effect_jeomhyeol_ta(player, enemy, card):
    """점혈타: 적에게 내공 봉쇄 디버프 (atk 감소 + 다음 합 방어 차단)"""
    atk_debuff = card.base_value
    enemy.atk = max(1, enemy.atk - atk_debuff)
    enemy.defense = 0  # 자세 흐트러트림
    return f"☠️ {card.name}: 급소를 찔러 적의 공격력 -{atk_debuff}, 방어 자세를 무너뜨렸습니다."


def effect_biyeon_bo(player, enemy, card):
    """비연보: 경공 발동 — 내공 회복 + 방어도 획득"""
    energy_gain = 2
    def_gain = card.base_value
    player.energy = min(player.max_energy, player.energy + energy_gain)
    player.add_defense(def_gain)
    return f"🌊 {card.name}: 신형을 흘려 내공 +{energy_gain}, 호신강기 +{def_gain}."


# --- [고급 초식 등록] ---

def init_advanced_cards():
    register_card(
        "용호권",
        Card(
            "용호권",
            CardType.ATTACK,
            3,
            "연속 이격 (각 60% × 2회)",
            20,
            effect_func=effect_yongho_gwon,
        ),
    )
    register_card(
        "철사장",
        Card(
            "철사장",
            CardType.DEFENSE,
            3,
            "방어 + 적 강기 분쇄",
            14,
            effect_func=effect_cheol_sa_jang,
        ),
    )
    register_card(
        "내가일소",
        Card(
            "내가일소",
            CardType.SKILL,
            2,
            "기혈 회복",
            15,
            effect_func=effect_naega_ilso,
        ),
    )
    register_card(
        "점혈타",
        Card(
            "점혈타",
            CardType.DEBUFF,
            2,
            "적 공격력 감소 + 방어 자세 파괴",
            6,
            effect_func=effect_jeomhyeol_ta,
        ),
    )
    register_card(
        "비연보",
        Card(
            "비연보",
            CardType.SKILL,
            1,
            "내공 회복 + 방어도 획득",
            6,
            effect_func=effect_biyeon_bo,
        ),
    )


init_advanced_cards()
