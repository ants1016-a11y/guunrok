"""
world/node_generator.py
북쪽(녹림) 루트 노드 그래프 생성
"""
from world.map_data import NodeData, NodeType, FactionType, Tier


def generate_north_route(screen_w: int = 1280, screen_h: int = 720) -> list:
    """
    녹림 루트 노드 그래프를 생성합니다.
    구조: 청운성(출발) → 분기 전투/휴식 → 마천광(보스)
    반환: NodeData 리스트 (connections으로 그래프 연결 표현)
    """
    N  = FactionType.NOKRIM
    NT = FactionType.NEUTRAL
    MP = NodeType.MOUNTAIN_PATH
    OR = NodeType.OFFICIAL_ROAD
    INN = NodeType.INN
    BC = NodeType.BIG_CITY
    SG = NodeType.SECT_GATE
    T  = Tier

    # 6열 × 3행 레이아웃
    xs = [100, 290, 480, 670, 860, 1100]
    yT = 140   # 상단 행
    yM = 360   # 중간 행
    yB = 560   # 하단 행

    nodes = [
        # ── Col 0: 출발 ──
        NodeData(
            id=0, node_type=BC, pos=(xs[0], yM),
            connections=[1, 2],
            risk_level=0, faction=NT, tier=T.MINION,
            label="청운성", region="north",
        ),

        # ── Col 1: 첫 분기 ──
        NodeData(
            id=1, node_type=MP, pos=(xs[1], 220),
            connections=[3, 4],
            risk_level=1, faction=N, tier=T.MINION,
            label="북산길", region="north",
        ),
        NodeData(
            id=2, node_type=OR, pos=(xs[1], 500),
            connections=[4, 5],
            risk_level=1, faction=N, tier=T.MINION,
            label="관도", region="north",
        ),

        # ── Col 2: 두 번째 분기 ──
        NodeData(
            id=3, node_type=INN, pos=(xs[2], yT),
            connections=[6],
            risk_level=0, faction=NT, tier=T.MINION,
            label="주막", region="north",
        ),
        NodeData(
            id=4, node_type=MP, pos=(xs[2], yM),
            connections=[6, 7],
            risk_level=2, faction=N, tier=T.CAPTAIN,
            label="산채 입구", region="north",
        ),
        NodeData(
            id=5, node_type=MP, pos=(xs[2], yB),
            connections=[7],
            risk_level=2, faction=N, tier=T.CAPTAIN,
            label="협곡", region="north",
        ),

        # ── Col 3: 세 번째 분기 ──
        NodeData(
            id=6, node_type=SG, pos=(xs[3], 240),
            connections=[8],
            risk_level=0, faction=NT, tier=T.MINION,
            label="무관", region="north",
        ),
        NodeData(
            id=7, node_type=MP, pos=(xs[3], 480),
            connections=[8],
            risk_level=3, faction=N, tier=T.ELDER,
            label="녹림 거점", region="north",
        ),

        # ── Col 4: 합류점 ──
        NodeData(
            id=8, node_type=MP, pos=(xs[4], yM),
            connections=[9],
            risk_level=3, faction=N, tier=T.ELDER,
            label="산채 심부", region="north",
        ),

        # ── Col 5: 보스 ──
        NodeData(
            id=9, node_type=MP, pos=(xs[5], yM),
            connections=[],
            risk_level=5, faction=N, tier=T.BOSS,
            is_boss=True, label="마천광의 산채", region="north",
        ),
    ]

    return nodes
