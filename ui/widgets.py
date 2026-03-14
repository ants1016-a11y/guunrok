# ui/widgets.py
import pygame
import math  # [추가] 수학적 연출(sin)을 위해 이 파일에도 반드시 필요합니다!


def draw_card_art_icon(screen, name: str, type_str: str, cx: int, cy: int, r: int, accent):
    """
    무협 스타일 원형 아이콘.
    크림 배경 원 + 먹물 선화로 각 무공의 특성을 표현합니다.
    """
    CREAM  = (238, 225, 200)
    INK    = (35, 22, 10)
    RING   = (100, 72, 44)

    # ── 배경 원 ──
    pygame.draw.circle(screen, CREAM, (cx, cy), r)
    pygame.draw.circle(screen, RING,  (cx, cy), r, 2)

    s = r - 5   # 내부 그림 반경

    def ang(deg):
        return math.radians(deg)

    def pt(ox, oy, dist, deg):
        return (cx + ox + int(dist * math.cos(ang(deg))),
                cy + oy + int(dist * math.sin(ang(deg))))

    # ── 카드별 아이콘 ──

    if name == "복호장":
        # 호랑이 장법 — 활짝 편 손바닥 + 호선(虎線) 3줄기
        # 손바닥: 세로 타원 (손목↑ 손끝↓ 방향)
        palm_rect = pygame.Rect(cx - s * 2 // 5, cy - s // 2, s * 4 // 5, s)
        pygame.draw.ellipse(screen, INK, palm_rect, 2)
        # 호랑이 줄무늬 — 손바닥을 가로지르는 3선
        for dy in [-s // 5, 0, s // 5]:
            pygame.draw.line(screen, INK,
                             (palm_rect.left + 4, cy + dy),
                             (palm_rect.right - 4, cy + dy), 2)
        # 손끝 충격파
        for dx in [-s // 3, 0, s // 3]:
            pygame.draw.line(screen, INK,
                             (cx + dx, palm_rect.bottom - 2),
                             (cx + dx, palm_rect.bottom + s // 4), 1)

    elif name == "육합권":
        # 주먹 – 가로 사각 손등 + 손가락 마디
        fist_r = pygame.Rect(cx - s // 2, cy - s // 4, s, s // 2)
        pygame.draw.rect(screen, INK, fist_r, 2, border_radius=3)
        # 마디 3선
        for kx in [cx - s // 6, cx, cx + s // 6]:
            pygame.draw.line(screen, INK, (kx, fist_r.top), (kx, fist_r.top - s // 4), 2)
        # 엄지
        pygame.draw.arc(screen, INK,
                        pygame.Rect(fist_r.right - 4, fist_r.top, s // 3, s // 3),
                        ang(0), ang(120), 2)

    elif name == "포천삼":
        # 방패 (위쪽 평편 + 아래 뾰족)
        pts = [
            (cx - s, cy - s // 3),
            (cx + s, cy - s // 3),
            (cx + s, cy + s // 5),
            (cx,     cy + s),
            (cx - s, cy + s // 5),
        ]
        pygame.draw.polygon(screen, INK, pts, 2)
        # 방패 십자
        pygame.draw.line(screen, INK, (cx, cy - s // 3 + 3), (cx, cy + s - 6), 1)
        pygame.draw.line(screen, INK,
                         (cx - s // 2, cy + s // 8), (cx + s // 2, cy + s // 8), 1)

    elif name == "삼재공":
        # 삼재(三才) — 천(天)·지(地)·인(人) 세 방향 기격
        # 세 방향(위 / 좌하 / 우하)으로 굵은 기운 줄기가 뻗어나감
        for deg in [270, 30, 150]:
            p_inner = pt(0, 0, s // 4, deg)
            p_outer = pt(0, 0, s * 0.88, deg)
            pygame.draw.line(screen, INK, p_inner, p_outer, 3)
            # 끝 화살촉 (작은 V)
            for d_off in [-25, 25]:
                tip = pt(0, 0, s * 0.65, deg + d_off)
                pygame.draw.line(screen, INK, tip, p_outer, 2)
        # 중심 기점(氣點)
        pygame.draw.circle(screen, INK, (cx, cy), s // 5, 2)

    elif name == "유운지":
        # 아래를 향한 손가락 + 기(氣) 파동
        for i, dx in enumerate([-5, 0, 5]):
            pygame.draw.line(screen, INK, (cx + dx, cy - s // 2),
                             (cx + dx, cy + s // 6), 2)
        pygame.draw.arc(screen, INK,
                        pygame.Rect(cx - s // 2, cy + s // 6, s, s // 3),
                        ang(0), ang(180), 2)
        # 약화 물결선
        for wave_y in [cy + s // 2]:
            for wx in range(cx - s // 2, cx + s // 2, 6):
                pygame.draw.arc(screen, INK,
                                pygame.Rect(wx, wave_y, 6, 4), ang(0), ang(180), 1)

    elif name == "녹림패도법":
        # 대각 도검 + 파쇄선
        pygame.draw.line(screen, INK, (cx - s + 2, cy + s - 2),
                         (cx + s - 2, cy - s + 2), 3)
        pygame.draw.polygon(screen, INK,
                            [(cx + s - 2, cy - s + 2),
                             (cx + s - 8, cy - s + 6),
                             (cx + s - 4, cy - s + 10)], 0)
        # 충격 방사선
        for deg in [45, 90, 135]:
            pygame.draw.line(screen, INK,
                             pt(0, 0, s // 2, deg), pt(0, 0, s * 0.85, deg), 1)

    elif name == "천근추":
        # 무거운 추 – 상단 막대 + 구체
        pygame.draw.line(screen, INK, (cx, cy - s), (cx, cy - s // 3), 3)
        pygame.draw.circle(screen, INK, (cx, cy + s // 5), s // 2, 3)
        # 중력선
        for dx in [-s // 3, 0, s // 3]:
            pygame.draw.line(screen, INK,
                             (cx + dx, cy + s // 5 + s // 2 + 2),
                             (cx + dx, cy + s // 5 + s // 2 + 6), 2)

    elif name == "산악붕":
        # 두 주먹 연격 – 왼쪽/오른쪽 내려치기
        for sign, off_y in [(-1, -3), (1, 3)]:
            bx = cx + sign * (s // 2)
            by = cy + off_y
            pygame.draw.rect(screen, INK,
                             pygame.Rect(bx - s // 4, by - s // 4, s // 2, s // 3), 2)
            pygame.draw.line(screen, INK, (bx, by - s // 4 - 1),
                             (bx, by - s // 4 - s // 3), 2)

    # ── 졸개 잡기술 + 무공 ──────────────────────────────────────────────────────

    elif name == "돌팔매":
        # 포물선 궤적 + 날아가는 돌
        steps = 9
        for i in range(steps - 1):
            t0 = i / (steps - 1)
            t1 = (i + 1) / (steps - 1)
            x0 = cx - s + 2 + int(2 * (s - 2) * t0)
            y0 = cy + int(s * 0.7 * (4 * t0 * (1 - t0)) - s * 0.35)
            x1 = cx - s + 2 + int(2 * (s - 2) * t1)
            y1 = cy + int(s * 0.7 * (4 * t1 * (1 - t1)) - s * 0.35)
            pygame.draw.line(screen, INK, (x0, y0), (x1, y1), 2)
        # 날아가는 돌 (호 끝점에 불규칙 다각형)
        ex = cx + s - 4
        ey = cy - s // 3
        stone_pts = [(ex - 5, ey - 3), (ex + 3, ey - 5), (ex + 6, ey),
                     (ex + 2, ey + 5), (ex - 4, ey + 3)]
        pygame.draw.polygon(screen, INK, stone_pts, 2)

    elif name == "주먹질":
        # 전방 돌진 주먹 — 직사각 + 팔뚝 + 앞쪽 충격선
        fist = pygame.Rect(cx - s // 8, cy - s // 3, s // 2, s * 2 // 3)
        pygame.draw.rect(screen, INK, fist, 2, border_radius=4)
        # 팔뚝 (아래쪽)
        pygame.draw.line(screen, INK,
                         (fist.centerx, fist.bottom),
                         (fist.centerx, fist.bottom + s // 3), 4)
        # 앞쪽 충격 방사선 3개
        for dy in [-s // 4, 0, s // 4]:
            pygame.draw.line(screen, INK,
                             (fist.right, fist.centery + dy // 2),
                             (fist.right + s // 3, fist.centery + dy), 2)

    elif name == "멱살잡이":
        # 멱살 움켜쥐기 — 안쪽으로 구부러진 두 손 + 잡힌 옷깃
        # 잡힌 옷깃 (중앙 사각)
        collar = pygame.Rect(cx - s // 4, cy - s // 5, s // 2, s * 2 // 5)
        pygame.draw.rect(screen, INK, collar, 2, border_radius=3)
        # 왼손 손가락 (안쪽으로 구부러짐)
        for i, dy in enumerate([-s // 4, 0, s // 4]):
            pygame.draw.arc(screen, INK,
                            pygame.Rect(cx - s + 2, cy + dy - s // 8,
                                        s * 3 // 4, s // 4),
                            ang(0), ang(160), 2)
        # 오른손 손가락 (대칭)
        for i, dy in enumerate([-s // 4, 0, s // 4]):
            pygame.draw.arc(screen, INK,
                            pygame.Rect(cx + s // 4, cy + dy - s // 8,
                                        s * 3 // 4, s // 4),
                            ang(20), ang(180), 2)

    elif name == "난도질":
        # 어설픈 난자 — 3개의 불규칙 참격선
        slashes = [
            ((cx - s + 3, cy - s // 4), (cx + s // 2, cy + s // 3)),
            ((cx - s // 3, cy - s + 3), (cx + s // 3, cy + s - 3)),
            ((cx - s // 2, cy + s // 5), (cx + s - 3, cy - s // 3)),
        ]
        for p1, p2 in slashes:
            pygame.draw.line(screen, INK, p1, p2, 2)
        # 칼날 끝 (불규칙 꺾임)
        lx1, ly1 = slashes[0][0]
        pygame.draw.line(screen, INK, (lx1, ly1), (lx1 + s // 5, ly1 - s // 5), 2)

    # ── 보스 무공 (의도 아이콘용) ──

    elif name in ("살웅 괴력권", "기본 공격"):
        # 곰 발 / 큰 주먹
        pygame.draw.circle(screen, INK, (cx, cy + 2), s // 2, 2)
        for i, (dx, dy) in enumerate([(-6, -s // 2 - 3), (0, -s // 2 - 5), (6, -s // 2 - 3)]):
            pygame.draw.circle(screen, INK, (cx + dx, cy + dy), 4, 2)

    elif name in ("황산 대참",):
        # 대형 X 참격
        pygame.draw.line(screen, INK, (cx - s + 2, cy - s + 2), (cx + s - 2, cy + s - 2), 3)
        pygame.draw.line(screen, INK, (cx + s - 2, cy - s + 2), (cx - s + 2, cy + s - 2), 3)
        pygame.draw.circle(screen, INK, (cx, cy), 4)

    elif name in ("천악 부동체", "기본 방어"):
        # 산(山) 실루엣 – 삼각봉우리
        pts = [(cx - s, cy + s - 2), (cx, cy - s + 2), (cx + s, cy + s - 2)]
        pygame.draw.polygon(screen, INK, pts, 2)
        pygame.draw.line(screen, INK, (cx - s // 2, cy + s - 2),
                         (cx - s // 2, cy + s // 4), 1)

    elif name in ("패왕의 포효",):
        # 소리 파동 – 동심 호(弧) 3개
        for i in range(1, 4):
            pygame.draw.arc(screen, INK,
                            pygame.Rect(cx - s * i // 3, cy - s * i // 3,
                                        s * i // 3 * 2, s * i // 3 * 2),
                            ang(-60), ang(60), 2)
        # 입(점)
        pygame.draw.circle(screen, INK, (cx - s // 2, cy), 3)

    elif name in ("녹림 파천참",):
        # 번개 / 상향 참격
        pts = [
            (cx - 3, cy + s - 2),
            (cx + 4, cy),
            (cx - 2, cy),
            (cx + 5, cy - s + 2),
        ]
        pygame.draw.lines(screen, INK, False, pts, 3)

    elif name in ("운기 조식",):
        # 좌선(坐禪) – 명상하는 인물
        pygame.draw.circle(screen, INK, (cx, cy - s // 2), s // 4, 2)   # 머리
        pygame.draw.arc(screen, INK,
                        pygame.Rect(cx - s // 2, cy - s // 5, s, s // 2),
                        ang(0), ang(180), 2)                              # 몸통 반원
        pygame.draw.line(screen, INK, (cx - s // 2, cy + s // 4),
                         (cx + s // 2, cy + s // 4), 2)                  # 가부좌 선

    else:
        # 기본 폴백: 타입별 기호
        if type_str == "공격":
            pygame.draw.line(screen, INK, (cx - s + 2, cy + s - 2),
                             (cx + s - 2, cy - s + 2), 3)
            pygame.draw.polygon(screen, INK,
                                [(cx + s - 2, cy - s + 2),
                                 (cx + s - 7, cy - s + 5),
                                 (cx + s - 4, cy - s + 9)], 0)
        elif type_str == "방어":
            pts = [(cx, cy - s), (cx + s, cy - s // 3),
                   (cx + s // 2, cy + s), (cx - s // 2, cy + s), (cx - s, cy - s // 3)]
            pygame.draw.polygon(screen, INK, pts, 2)
        else:
            for i in range(3):
                pygame.draw.circle(screen, INK, (cx, cy), s // 3 + i * (s // 3), 1)


def draw_stat_bar(
    screen,
    x,
    y,
    w,
    h,
    current,
    maximum,
    color,
    label,
    font,
    visual_current=None,
    shield=0,
):
    """
    [극상 수선] 기혈의 잔상 효과와 중첩된 호신강기(맥동 광막)를 렌더링합니다.
    """
    # 1. 배경 (가장 아래 레이어)
    pygame.draw.rect(screen, (30, 30, 30), (x, y, w, h), border_radius=5)

    # 2. 잔상 렌더링 (하얀색 바)
    # 실제 기혈이 변한 뒤 서서히 줄어들며 타격의 깊이를 보여줍니다.
    if visual_current is not None and visual_current > current:
        v_ratio = max(0, min(1, visual_current / maximum)) if maximum > 0 else 0
        pygame.draw.rect(
            screen, (220, 220, 220), (x, y, int(w * v_ratio), h), border_radius=5
        )

    # 3. 실제 기혈 게이지
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    pygame.draw.rect(screen, color, (x, y, int(w * ratio), h), border_radius=5)

    # 4. [핵심] 호신강기(Shield) 겹쳐 그리기
    # 기혈바 위를 덮는 푸른 광막 효과입니다.
    if shield > 0:
        s_ratio = max(0, min(1, shield / maximum)) if maximum > 0 else 0
        s_width = int(w * s_ratio)

        # 반투명 서피스 생성
        shield_surf = pygame.Surface((s_width, h), pygame.SRCALPHA)

        # [신규] 호신강기 맥동(Pulse): 은은하게 빛이 납니다.
        # 여기서 math.sin을 사용하므로 파일 상단에 import math가 필수입니다!
        pulse_alpha = 140 + int(math.sin(pygame.time.get_ticks() * 0.01) * 20)
        shield_surf.fill((100, 200, 255, pulse_alpha))

        screen.blit(shield_surf, (x, y))

        # 방어 수치 텍스트 (강할 罡)
        s_txt = font.render(f"罡 {shield}", True, (150, 230, 255))
        screen.blit(s_txt, (x + w + 10, y))

    # 5. 테두리 출력
    # 호신강기 존재 시 푸른색, 없을 시 흰색 테두리
    border_col = (100, 200, 255) if shield > 0 else (255, 255, 255)
    pygame.draw.rect(screen, border_col, (x, y, w, h), 1, border_radius=5)

    # 6. 라벨 및 정보 출력
    txt_label = font.render(f"{label} {current}/{maximum}", True, (255, 255, 255))
    screen.blit(txt_label, (x, y - 22))


def draw_card_advanced(screen, x, y, card, font):
    """[개편] MTG/유희왕 감성 + 심플 카드 프레임(자동 이미지 매칭 포함)"""
    import os
    import pygame

    # --- 함수 내부 캐시(모듈 전역 수정 없이도 캐시됨) ---
    if not hasattr(draw_card_advanced, "_cache"):
        draw_card_advanced._cache = {}  # (path, size) -> Surface or None

    def _slug(name: str) -> str:
        # 기존 규칙 유지(영문/숫자만) — 단, 이건 후보 중 하나로만 사용
        s = name.strip().lower()
        out = []
        for ch in s:
            if ch.isalnum():
                out.append(ch)
            elif ch in [" ", "-", "_"]:
                out.append("_")
        slug = "".join(out)
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_") or "unknown"

    def _clean_filename_keep_korean(name: str) -> str:
        # ✅ 한글/영문/숫자는 살리고, 파일명에 위험한 문자만 정리
        bad = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        out = name.strip()
        for ch in bad:
            out = out.replace(ch, "_")
        # 공백은 언더바로 통일(파일명 흔들림 방지)
        out = out.replace(" ", "_")
        while "__" in out:
            out = out.replace("__", "_")
        return out.strip("_") or "unknown"

    def _try_load(path, size):
        key = (path, size)
        if key in draw_card_advanced._cache:
            return draw_card_advanced._cache[key]
        if not os.path.exists(path):
            draw_card_advanced._cache[key] = None
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            draw_card_advanced._cache[key] = img
            return img
        except Exception:
            draw_card_advanced._cache[key] = None
            return None

    # --- Layout constants ---
    w, h = 140, 190
    rect = pygame.Rect(x, y, w, h)

    # 타입별 포인트 컬러(프레임/리본/젬 테두리)
    if card.type.value == "공격":
        accent = (200, 80, 80)
        type_label = "공격"
    elif card.type.value == "방어":
        accent = (80, 200, 120)
        type_label = "방어"
    else:
        accent = (120, 140, 220)
        type_label = "기세"

    # 베이스(중립) + 프레임
    base_bg = (28, 28, 32)  # 다크 차콜
    inner_bg = (45, 45, 52)
    pygame.draw.rect(screen, base_bg, rect, border_radius=10)
    pygame.draw.rect(screen, accent, rect, 3, border_radius=10)

    inner = rect.inflate(-8, -8)
    pygame.draw.rect(screen, inner_bg, inner, border_radius=8)
    pygame.draw.rect(screen, (230, 230, 230), inner, 1, border_radius=8)

    # 상단 이름 바(헤더)
    header = pygame.Rect(inner.x, inner.y, inner.w, 30)
    pygame.draw.rect(screen, (20, 20, 22), header, border_radius=8)
    pygame.draw.line(
        screen,
        accent,
        (header.x + 8, header.bottom - 1),
        (header.right - 8, header.bottom - 1),
        2,
    )

    # 좌상단 비용 젬(원)
    gem_r = 12
    gem_center = (header.x + 16, header.y + 15)
    pygame.draw.circle(screen, (18, 18, 20), gem_center, gem_r + 2)
    pygame.draw.circle(screen, accent, gem_center, gem_r + 1, 2)
    pygame.draw.circle(screen, (60, 60, 70), gem_center, gem_r)

    cost_surf = font.render(str(card.base_cost), True, (245, 245, 245))
    screen.blit(
        cost_surf,
        (
            gem_center[0] - cost_surf.get_width() // 2,
            gem_center[1] - cost_surf.get_height() // 2,
        ),
    )

    # 카드명(너무 길면 줄이기)
    name = card.name
    if len(name) > 7:
        name = name[:7] + "…"
    name_txt = font.render(name, True, (245, 245, 245))
    screen.blit(name_txt, (header.x + 34, header.y + 6))

    # 타입 리본
    ribbon = pygame.Rect(inner.x, header.bottom + 4, inner.w, 16)
    pygame.draw.rect(screen, (18, 18, 20), ribbon, border_radius=6)
    pygame.draw.rect(screen, accent, ribbon, 1, border_radius=6)
    type_txt = font.render(f"{type_label}  ·  {card.mastery}성", True, (220, 220, 220))
    screen.blit(type_txt, (ribbon.x + 6, ribbon.y - 1))

    # 일러스트 프레임 영역
    art_rect = pygame.Rect(inner.x + 6, ribbon.bottom + 4, inner.w - 12, 68)
    pygame.draw.rect(screen, (12, 12, 14), art_rect, border_radius=6)
    pygame.draw.rect(screen, (230, 230, 230), art_rect, 1, border_radius=6)

    # --- 위력/방어 표시 로직 (기존 유지) ---
    multiplier = 1 + (card.mastery - 1) * 0.2
    if "복호" in card.name:
        val_display = f"{int(18 * multiplier)}~{int(25 * multiplier)}"
    elif card.name in ["육합권", "포천삼"]:
        val_display = f"{int(8 * multiplier)}~{int(12 * multiplier)}"
    else:
        val_display = str(card.get_current_value())
    label = "방어" if card.type.value == "방어" else "위력"

    # ---------------------------------------------------------
    # ✅ 카드 일러스트 자동 매칭 (강화)
    # - 한글 파일명 우선
    # - id/slug 등 후보를 여러 개 시도
    # ---------------------------------------------------------
    candidates = []

    # 1) 표시명 그대로(한글 포함) / 정리한 버전
    candidates.append(_clean_filename_keep_korean(card.name))
    if _clean_filename_keep_korean(card.name) != card.name:
        candidates.append(card.name)  # 혹시 공백 그대로 저장한 경우

    # 2) 기존 slug(영문화)
    candidates.append(_slug(card.name))

    # 3) card.id / key가 있으면 추가 (프로젝트 구조에 따라 존재할 수도)
    for attr in ["id", "key", "card_id", "cid"]:
        v = getattr(card, attr, None)
        if isinstance(v, str) and v.strip():
            candidates.append(_clean_filename_keep_korean(v))
            candidates.append(_slug(v))

    # 중복 제거(순서 유지)
    seen = set()
    uniq = []
    for c in candidates:
        c = (c or "").strip()
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)
        uniq.append(c)

    # 경로 후보 만들기
    img = None
    for fname in uniq:
        rel = os.path.join("assets", "cards", f"{fname}.png")
        p1 = os.path.abspath(rel)
        p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel))
        p3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", rel))

        img = (
            _try_load(p1, size=(art_rect.w, art_rect.h))
            or _try_load(p2, size=(art_rect.w, art_rect.h))
            or _try_load(p3, size=(art_rect.w, art_rect.h))
        )
        if img:
            break

    if img:
        screen.blit(img, art_rect.topleft)
        gloss = pygame.Surface((art_rect.w, art_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(
            gloss,
            (255, 255, 255, 14),
            (0, 0, art_rect.w, art_rect.h // 2),
            border_radius=6,
        )
        screen.blit(gloss, art_rect.topleft)
    else:
        # 이미지가 없을 때: 카드별 무협 원형 아이콘
        cx, cy = art_rect.center
        r = min(art_rect.w, art_rect.h) // 2 - 2
        draw_card_art_icon(screen, card.name, type_label, cx, cy, r, accent)

    # 텍스트 박스(효과/설명 영역)
    text_box = pygame.Rect(inner.x + 6, art_rect.bottom + 6, inner.w - 12, 48)
    pygame.draw.rect(screen, (18, 18, 20), text_box, border_radius=6)
    pygame.draw.rect(screen, (230, 230, 230), text_box, 1, border_radius=6)

    info1 = f"{label} {val_display}"
    info2 = f"내공 {card.base_cost}"

    info1_s = font.render(info1, True, (245, 245, 245))
    info2_s = font.render(info2, True, (210, 210, 210))
    screen.blit(info1_s, (text_box.x + 6, text_box.y + 6))
    screen.blit(info2_s, (text_box.x + 6, text_box.y + 26))

    # 하단 숙련도 바(기존 유지)
    bar_bg = pygame.Rect(inner.x + 8, inner.bottom - 12, inner.w - 16, 6)
    pygame.draw.rect(screen, (10, 10, 12), bar_bg, border_radius=3)
    exp_ratio = getattr(card, "mastery_exp", 0) / getattr(card, "mastery_max", 100)
    exp_w = int(bar_bg.w * max(0.0, min(1.0, exp_ratio)))
    pygame.draw.rect(
        screen, accent, (bar_bg.x, bar_bg.y, exp_w, bar_bg.h), border_radius=3
    )


def draw_enemy_intent_box(screen, x, y, intent_queue, font):
    """[복구] 적의 다음 초식을 미리 읽어 표시합니다."""
    if intent_queue:
        # 무협의 느낌을 살린 붉은색 예독 텍스트
        intent_txt = font.render(
            f"□ 차기 합: {intent_queue[0]} 예상", True, (200, 50, 50)
        )
        screen.blit(intent_txt, (x, y))


def draw_battle_log(screen, x, y, logs, font):
    """비무의 흐름을 텍스트로 출력합니다."""
    # 최근 10개의 로그만 표시
    for i, msg in enumerate(logs[-10:]):
        log_txt = font.render(msg, True, (230, 230, 230))
        screen.blit(log_txt, (x, y + i * 22))
