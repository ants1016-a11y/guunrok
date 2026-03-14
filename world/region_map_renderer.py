"""
world/region_map_renderer.py
REGION_MAP 페이즈용 노드 그래프 렌더러
"""
import pygame
from world.map_data import NodeType, NODE_TYPE_COLORS, NODE_TYPE_ICONS

NODE_RADIUS = 28
BOSS_RADIUS = 36


def render_region_map(
    surf: pygame.Surface,
    nodes: list,
    current_node_id: int,
    visiting_node_id: int,
    font,
    font_small,
) -> dict:
    """
    노드 그래프를 surf에 그리고, 클릭 가능한 노드의 {node_id: Rect}를 반환합니다.

    Args:
        current_node_id: 플레이어가 현재 있는 노드(방문 완료)
        visiting_node_id: 현재 진행 중(전투/휴식 중)인 노드 (-1이면 없음)
    """
    node_map = {n.id: n for n in nodes}

    # 접근 가능한 노드: 방문 완료된 노드의 자식 중 미방문
    reachable_ids = set()
    for n in nodes:
        if n.visited:
            for c_id in n.connections:
                child = node_map.get(c_id)
                if child and not child.visited:
                    reachable_ids.add(c_id)

    # ── 연결선 먼저 그리기 ──
    for n in nodes:
        for c_id in n.connections:
            child = node_map.get(c_id)
            if not child:
                continue
            if n.visited and child.visited:
                line_color = (70, 70, 70)
            elif n.visited:
                line_color = (160, 140, 60)
            else:
                line_color = (40, 40, 50)
            pygame.draw.line(surf, line_color, n.pos, child.pos, 2)

    # ── 노드 그리기 ──
    clickable = {}

    for n in nodes:
        cx, cy = n.pos
        r = BOSS_RADIUS if n.is_boss else NODE_RADIUS

        is_reachable = n.id in reachable_ids
        is_visited = n.visited
        is_current = (n.id == current_node_id)
        is_visiting = (n.id == visiting_node_id)

        base_color = NODE_TYPE_COLORS.get(n.node_type, (80, 80, 80))

        if is_visiting:
            # 현재 진행 중인 노드: 금빛
            color = (180, 160, 40)
            border = (255, 220, 80)
            border_w = 4
        elif is_visited:
            color = (45, 45, 45)
            border = (85, 85, 85)
            border_w = 2
        elif is_current and not is_visited:
            # 현재 위치(방문은 완료됐지만 is_current만 표시)
            color = base_color
            border = (255, 220, 50)
            border_w = 4
        elif is_reachable:
            color = base_color
            border = (220, 220, 220)
            border_w = 3
        else:
            color = (35, 35, 42)
            border = (58, 58, 68)
            border_w = 1

        pygame.draw.circle(surf, color, (cx, cy), r)
        pygame.draw.circle(surf, border, (cx, cy), r, border_w)

        # 아이콘 텍스트
        icon = NODE_TYPE_ICONS.get(n.node_type, "?")
        icon_color = (255, 255, 255) if not is_visited else (90, 90, 90)
        icon_surf = font_small.render(icon, True, icon_color)
        surf.blit(icon_surf, (cx - icon_surf.get_width() // 2, cy - icon_surf.get_height() // 2))

        # 라벨 (접근 가능하거나 방문한 노드만 표시)
        show_label = is_reachable or is_current or is_visited or is_visiting
        if show_label:
            label_color = (230, 210, 150) if is_reachable else (140, 140, 140)
            label_surf = font_small.render(n.label, True, label_color)
            surf.blit(label_surf, (cx - label_surf.get_width() // 2, cy + r + 6))

        # 보스 경고 표시
        if n.is_boss and not is_visited:
            warn = font_small.render("!", True, (255, 70, 70))
            surf.blit(warn, (cx + r - 4, cy - r - 2))

        # 접근 가능한 노드만 클릭 rect 등록
        if is_reachable:
            rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            clickable[n.id] = rect

    return clickable
