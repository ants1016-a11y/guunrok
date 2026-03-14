"""
world/faction_data.py
세력별 적 풀(Tier 매핑) + 노드 정보 기반 적 생성 함수
"""
import random
from world.map_data import FactionType, Tier


# ──────────────────────────────────────────────
# 세력 × Tier → (enemy_registry_key, stat_overrides)
# stat_overrides가 빈 dict면 클래스 기본값 사용 (보스 등)
# ──────────────────────────────────────────────
FACTION_POOL = {
    FactionType.NOKRIM: {
        Tier.MINION:  [("nokrim_minion",  {"name": "산채 졸개",    "hp": 40,  "atk": 7,  "level": 1})],
        Tier.CAPTAIN: [("nokrim_captain", {"name": "녹림 행동대장","hp": 65,  "atk": 10, "level": 3})],
        Tier.ELDER:   [("nokrim_elder",   {"name": "녹림 고수",    "hp": 110, "atk": 14, "level": 6})],
        Tier.MASTER:  [("nokrim_master",  {"name": "녹림 거두",    "hp": 160, "atk": 18, "level": 8})],
        Tier.BOSS:    [("boss_macheon",   {})],  # MaCheonGwang 고정값
    },
    FactionType.SAPHA: {
        Tier.MINION:  [("hyulgyo_jaGaek", {})],
        Tier.CAPTAIN: [("hyulgyo_gosu",   {})],
        Tier.ELDER:   [("hyulgyo_gosu",   {})],
        Tier.BOSS:    [("hyulgyo_jangro", {})],
    },
    FactionType.SEWAE: {
        Tier.MINION:  [("sewae_minion",   {"name": "세외 탐색자", "hp": 45,  "atk": 8,  "level": 2})],
        Tier.CAPTAIN: [("sewae_captain",  {"name": "세외 고수",  "hp": 75,  "atk": 12, "level": 5})],
        Tier.ELDER:   [("sewae_captain",  {"name": "세외 수호자","hp": 120, "atk": 16, "level": 7})],
        Tier.BOSS:    [("sewae_captain",  {"name": "세외 우두머리","hp": 200,"atk": 20, "level": 10})],
    },
    FactionType.MERCENARY: {
        Tier.MINION:  [("merc_minion",    {"name": "용병",       "hp": 35,  "atk": 6,  "level": 1})],
        Tier.CAPTAIN: [("merc_captain",   {"name": "용병 대장",  "hp": 60,  "atk": 9,  "level": 3})],
        Tier.ELDER:   [("merc_captain",   {"name": "일류 용병",  "hp": 100, "atk": 13, "level": 5})],
        Tier.BOSS:    [("merc_captain",   {"name": "전설의 용병","hp": 180, "atk": 17, "level": 8})],
    },
}


def build_enemy_for_node(node_data, enemy_registry):
    """
    NodeData의 faction + tier를 보고 적 인스턴스를 반환합니다.
    registry에 있는 보스/특수 적은 그대로 사용,
    없으면 기본 Enemy로 폴백합니다.
    """
    pool = FACTION_POOL.get(node_data.faction)
    if pool is None:
        return _fallback_enemy(node_data)

    tier_pool = pool.get(node_data.tier)
    if not tier_pool:
        # 해당 티어가 없으면 MINION으로 폴백
        tier_pool = pool.get(Tier.MINION, [])
    if not tier_pool:
        return _fallback_enemy(node_data)

    key, overrides = random.choice(tier_pool)
    enemy_cls = enemy_registry.get(key)

    if enemy_cls is not None and not overrides:
        # 보스/특수 적: 클래스 기본값 그대로
        return enemy_cls()

    if enemy_cls is not None and overrides:
        # 서브클래스 __init__를 통해 생성 후 스탯 오버라이드
        # (__new__ + Enemy.__init__ 우회 방식을 쓰면 서브클래스 고유 속성이 누락됨)
        obj = enemy_cls(level=overrides.get("level", 1))
        if "name"  in overrides: obj.name    = overrides["name"]
        if "hp"    in overrides:
            obj.max_hp = overrides["hp"]
            obj.hp     = overrides["hp"]
        if "atk"   in overrides: obj.atk     = overrides["atk"]
        return obj

    # registry 미등록: 기본 Enemy 직접 생성
    from entities.enemy import Enemy
    return Enemy(
        name=overrides.get("name", "무명의 적"),
        hp=overrides.get("hp", 30 + node_data.risk_level * 10),
        atk=overrides.get("atk", 5 + node_data.risk_level * 2),
        level=overrides.get("level", max(1, node_data.risk_level * 2)),
    )


def _fallback_enemy(node_data):
    from entities.enemy import Enemy
    return Enemy(
        name="길을 막는 자",
        hp=30 + node_data.risk_level * 8,
        atk=5 + node_data.risk_level * 2,
        level=max(1, node_data.risk_level * 2),
    )
