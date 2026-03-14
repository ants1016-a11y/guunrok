"""
world/map_data.py
월드맵 데이터 구조 정의: 노드 타입, 세력, 난이도 Tier, NodeData
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Tuple


class NodeType(Enum):
    MOUNTAIN_PATH = "산길"       # 전투 ↑
    OFFICIAL_ROAD = "관도"       # 이벤트 위주, 전투 ↓
    SMALL_TOWN    = "소도시"     # 상점/소문
    BIG_CITY      = "대도시"     # 상점+이벤트
    SECT_GATE     = "문파"       # 강화/수련
    INN           = "객잔"       # 회복/버프
    TOURNAMENT    = "비무대"     # 고위험 고보상


class FactionType(Enum):
    NOKRIM     = "녹림"
    SAPHA      = "사파"
    SEWAE      = "세외"
    MERCENARY  = "용병"
    NEUTRAL    = "중립"


class Tier(Enum):
    MINION  = 1   # 졸개급
    CAPTAIN = 2   # 대장급
    ELDER   = 3   # 장로급
    MASTER  = 4   # 후기지수급
    BOSS    = 5   # 보스


# 노드 타입별 표시 색상 (RGB)
NODE_TYPE_COLORS = {
    NodeType.MOUNTAIN_PATH: (110, 70,  40),
    NodeType.OFFICIAL_ROAD: (70,  100, 70),
    NodeType.SMALL_TOWN:    (50,  70,  140),
    NodeType.BIG_CITY:      (70,  50,  150),
    NodeType.SECT_GATE:     (150, 40,  40),
    NodeType.INN:           (40,  120, 80),
    NodeType.TOURNAMENT:    (150, 130, 20),
}

# 노드 타입별 이모지 힌트 (라벨용)
NODE_TYPE_ICONS = {
    NodeType.MOUNTAIN_PATH: "⚔",
    NodeType.OFFICIAL_ROAD: "🛤",
    NodeType.SMALL_TOWN:    "🏘",
    NodeType.BIG_CITY:      "🏯",
    NodeType.SECT_GATE:     "⛩",
    NodeType.INN:           "🍵",
    NodeType.TOURNAMENT:    "🥊",
}


@dataclass
class NodeData:
    id: int
    node_type: NodeType
    pos: Tuple[int, int]                       # pygame 화면 좌표
    connections: List[int] = field(default_factory=list)
    risk_level: int = 1                        # 0~3: 분기 난이도
    faction: FactionType = FactionType.NEUTRAL
    tier: Tier = Tier.MINION
    locked_by_reincarnation: bool = False      # 회귀 해금 훅 (1차엔 항상 False)
    visited: bool = False
    is_boss: bool = False
    label: str = ""
    region: str = ""                           # "north" / "south" / ...
