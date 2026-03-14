"""
ui/renderer.py
전역 색상 상수와 재사용 가능한 렌더링 유틸리티 함수를 관리합니다.
"""

# --- 색상 팔레트 ---
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_GRAY = (100, 100, 100)
COLOR_DARK_GRAY = (30, 30, 30)
COLOR_RED = (200, 50, 50)
COLOR_GREEN = (50, 200, 50)
COLOR_BLUE = (50, 50, 200)

# 연출용 섬광 색상
FLASH_RED = (255, 100, 100)
FLASH_BLUE = (100, 100, 255)
FLASH_GREEN = (100, 255, 100)

# 카드 타입별 색상
CARD_TYPE_COLORS = {
    "공격": (200, 60, 60),
    "방어": (60, 100, 200),
    "기술": (60, 180, 100),
    "약화": (160, 80, 200),
}


def draw_text_centered(surf, font, text, color, y, screen_width):
    """텍스트를 화면 중앙에 렌더링합니다."""
    rendered = font.render(text, True, color)
    surf.blit(rendered, (screen_width // 2 - rendered.get_width() // 2, y))
    return rendered.get_height()


def draw_button(surf, rect, bg_color, border_color, font, text, text_color,
                border_radius=8, border_width=1):
    """표준 버튼 하나를 그립니다. 버튼 Rect를 반환합니다."""
    import pygame
    pygame.draw.rect(surf, bg_color, rect, border_radius=border_radius)
    if border_width > 0:
        pygame.draw.rect(surf, border_color, rect, border_width, border_radius=border_radius)
    label = font.render(text, True, text_color)
    surf.blit(label, (
        rect.centerx - label.get_width() // 2,
        rect.centery - label.get_height() // 2,
    ))
    return rect


def draw_card_type_bar(surf, rect, card_type_str, bar_width=8):
    """카드 좌측에 타입별 컬러 바를 그립니다."""
    import pygame
    color = CARD_TYPE_COLORS.get(card_type_str, (120, 120, 120))
    bar = pygame.Rect(rect.x, rect.y, bar_width, rect.height)
    pygame.draw.rect(surf, color, bar, border_radius=4)
    return color
