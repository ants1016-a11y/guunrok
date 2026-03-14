# infra/config.py
from enum import Enum

# 1. 화면 및 성능 설정
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 2. 강호의 색상 (무협 UI 전용)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GOLD = (218, 165, 32)
COLOR_RED = (180, 0, 0)
COLOR_GREEN = (0, 150, 0)
COLOR_BLUE = (100, 150, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_DARK_GREEN = (0, 100, 0)


# 3. 게임 페이로드 상태 (Phase) 정의
class Phase(Enum):
    WORLD = "강호 대지"
    PLAYER_TURN = "아방 합"
    ENEMY_TURN = "적방 합"
    VICTORY_PANEL = "비무 승리"
    GAMEOVER = "주화입마"
    INN = "객잔"
    TRAINING = "연무장"
    DECK = "비급고 정비"
    ERROR = "기혈 뒤틀림"


# 효과 함수 정의 (별도 파일이나 config 하단에 배치)
def basic_attack_effect(p, e, c):
    dmg = e.take_damage(c.base_value)
    return f"기본 초식으로 {dmg}의 피해를 입혔습니다."


def basic_defense_effect(p, e, c):
    p.add_defense(c.base_value)
    return f"기본 방어로 {c.base_value}의 기운을 갈무리했습니다."


def meditation_effect(p, e, c):
    # 즉시 내공을 2 회복합니다. (운기조식)
    p.energy = min(p.max_energy, p.energy + 2)
    return "운기조식을 통해 내공 2를 즉시 회복했습니다."


# 4. 전투 밸런스 상수
MAX_CLASHES_PER_TURN = 5

# 스탯 기준치 (외공=10, 근골=10 기준)
BASE_ATK = 5          # 공격력 기반값: ATK = BASE_ATK + 외공*1.0 + 근골*0.1
BASELINE_ATK = 16     # 기초 스탯(10/10)일 때 ATK = 5 + 10 + 1 = 16

ENLIGHTEN_BASE_XP = 500
ENLIGHTEN_DIFFICULTY_FACTOR = 200

SCREEN_SHAKE_POWER = 10  # 화면 흔들림 강도
FLASH_COLOR = (255, 255, 255)  # 치명타 섬광 색상 (백색)
FLASH_RED = (255, 50, 50)  # 공격 치명타
FLASH_BLUE = (50, 50, 255)  # 방어 치명타
FLASH_GREEN = (50, 255, 50)  # 보조 치명타
CRIT_MULTIPLIER = 1.5  # 치명타 피해 배율

GAMEOVER = "죽음"  # [교정] 주화입마 -> 죽음


MAX_CLASHES_PER_TURN = 5  # 적의 의도가 항상 5개가 되도록 보장하는 기준
