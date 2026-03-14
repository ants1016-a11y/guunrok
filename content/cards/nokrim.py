import random
from entities.card import Card, CardType
from content.registry import register_card


# ─────────────────────────────────────────────────────────────────────────────
# 마천광 의도 표시용 참고 카드 (noop – 플레이어가 사용하지 않음)
# ─────────────────────────────────────────────────────────────────────────────

def _noop(player, enemy, card):
    return ""


register_card("salung_gwon",      Card("살웅 괴력권",  CardType.ATTACK,  3, "곰의 머리를 부수는 괴력.",     25, effect_func=_noop))
register_card("hwangsan_daecham", Card("황산 대참",    CardType.ATTACK,  4, "산을 가르는 횡베기.",           32, effect_func=_noop))
register_card("cheonak_body",     Card("천악 부동체",  CardType.DEFENSE, 2, "태산 같은 기세로 타격을 받아냄.", 15, effect_func=_noop))
register_card("paewang_roar",     Card("패왕의 포효",  CardType.SKILL,   3, "전장을 울리는 외침.",            0, effect_func=_noop))
register_card("nokrim_pacheon",   Card("녹림 파천참",  CardType.ATTACK,  5, "하늘을 가르는 녹림왕의 비기.",   55, effect_func=_noop))


# ─────────────────────────────────────────────────────────────────────────────
# 보스 처치 후 획득 가능한 플레이어 전용 비급 (3종)
# ─────────────────────────────────────────────────────────────────────────────

def effect_nokrim_pado(player, enemy, card):
    """녹림패도법: 방어 파쇄 후 강타 — 천악부동체 대응."""
    shatter = min(getattr(enemy, "defense", 0), 15)
    if hasattr(enemy, "defense"):
        enemy.defense = max(0, enemy.defense - 15)
    dmg = card.base_value + getattr(player, "attack_power_bonus", 0)
    actual = enemy.take_damage(dmg)
    if shatter > 0:
        return f"⚔️ {card.name}: 방어 {shatter} 파쇄 후 {actual}의 피해!"
    return f"⚔️ {card.name}: {actual}의 피해를 입혔습니다."


def effect_cheongeun_chu(player, enemy, card):
    """천근추: 자신의 기본값 + 적 공격력의 절반만큼 방어 획득."""
    def_val = card.base_value + getattr(enemy, "atk", 0) // 2
    player.add_defense(def_val)
    return f"🪨 {card.name}: 산처럼 버텨 호신강기 {def_val}을(를) 쌓았습니다."


def effect_sanak_bung(player, enemy, card):
    """산악붕: 2타 연속 타격 — 방어를 두 번 깎아낸다."""
    hit = (card.base_value + getattr(player, "attack_power_bonus", 0)) // 2
    a1 = enemy.take_damage(hit)
    a2 = enemy.take_damage(hit)
    return f"💥 {card.name}: 2타 연격! 합계 {a1 + a2}의 피해!"


register_card(
    "nokrim_pado",
    Card(
        "녹림패도법",
        CardType.ATTACK,
        3,
        "방어 15 파쇄 후 강타. 천악부동체를 뚫는다.",
        20,
        effect_func=effect_nokrim_pado,
    ),
)

register_card(
    "cheongeun_chu",
    Card(
        "천근추",
        CardType.DEFENSE,
        2,
        "기본 방어 + 적 공격력/2 의 강기를 쌓는다.",
        12,
        effect_func=effect_cheongeun_chu,
    ),
)

register_card(
    "sanak_bung",
    Card(
        "산악붕",
        CardType.ATTACK,
        3,
        "2타 연격. 방어를 두 번 깎아 빠르게 관통한다.",
        18,
        effect_func=effect_sanak_bung,
    ),
)

# 보스 전용 드랍 풀 (이 ID만 보스 보상에 등장)
BOSS_NOKRIM_DROP_POOL = ["nokrim_pado", "cheongeun_chu", "sanak_bung"]
