import copy
import math
import os
import random
import sys
import traceback
from enum import Enum, auto

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame

from content.registry import CARD_REGISTRY
from core.combat.battle_manager import BattleManager
from core.game_stage import get_chapter, is_chapter_transition
from entities.enemy import Enemy
from entities.player import Player
from infra.config import *  # noqa: F403
from infra.loader import load_content
from infra.storage import (
    get_existing_users,
    load_game_data,
    save_game_data,
)
from ui.widgets import (
    draw_card_advanced,
    draw_card_art_icon,
    draw_stat_bar,
)

# [기초 설정값 선언] 사관(Ruff)의 결벽증을 해결하기 위해 배치를 조정했습니다.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
SCREEN_SHAKE_POWER = 5

# [색상 법전 선언] 누락되었던 섬광(FLASH)의 기운을 추가했습니다.
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_GRAY = (100, 100, 100)
COLOR_DARK_GRAY = (30, 30, 30)
COLOR_RED = (200, 50, 50)
COLOR_GREEN = (50, 200, 50)
COLOR_BLUE = (50, 50, 200)

# [연출용 색상] 비무 중 발생하는 섬광의 색상입니다.
FLASH_RED = (255, 100, 100)
FLASH_BLUE = (100, 100, 255)
FLASH_GREEN = (100, 255, 100)


# [무림 페이즈 선언]
class Phase(Enum):
    WORLD = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    TRAINING = auto()
    VICTORY_PANEL = auto()
    GAMEOVER = auto()
    INN = auto()
    VICTORY = auto()
    VICTORY_FINISH = auto()  # [신규] 전투 마무리 연출 페이즈
    DECK = auto()  # [신규] 비급고 정비 페이즈
    CARD_REWARD = auto()  # [신규] 전투 후 비급 획득 선택 페이즈
    REGION_MAP = auto()  # [신규] 노드 루트 맵 탐색 페이즈


# [수정] 예법에 맞춰 Phase_Ext를 PhaseExt로 개명했습니다.
class PhaseExt:
    LOGIN = "LOGIN"


class GuunrokGame:
    def __init__(self):
        """[수선] 페이즈 명칭을 PhaseExt로 통일하여 사관의 지적을 해결했습니다."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("구운록 v2 - 대천세상")

        self.current_clash_idx = -1
        self.player_slots = []
        self.card_rects = []
        self.clock = pygame.time.Clock()
        self.setup_font()
        load_content("content")
        self.flash_color = COLOR_WHITE

        # [수정] 스포트라이트 연출을 위한 반투명 검은색 막 생성
        self.dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 180))

        self.player = None
        self.clash_particles = []

        # [신규] 부드러운 기혈 감소 애니메이션을 위한 가상 기혈 변수 초기화
        self.player_visual_hp = 0
        self.enemy_visual_hp = 0

        self.temp_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.flash_surf.fill((255, 255, 255))
        self.screen_shake = 0
        self.flash_alpha = 0

        self.battle_log = []

        self.clash_anim = {
            "active": False,
            "clash_idx": 0,
            "stage": "WAIT",
            "char_idx": 0,
            "timer": 0,
            "full_text": "",
            "sub_lines": [],
        }

        # [수정] Phase_Ext를 PhaseExt로 변경
        self.phase = PhaseExt.LOGIN
        self.input_id = ""

        self.chapter, self.encounter = 1, 1
        self.ui_buttons_active = {}
        self.ui_buttons_next = {}
        self.clashes_count = 0
        self.btn_end_turn_rect = pygame.Rect(1000, 710, 140, 50)
        self.last_battle_rewards = None
        self.run_history = []
        self.death_novel = []
        self.victory_overlay = False
        self.card_reward_choices = []  # 비급 보상 후보 (초기화)

        # ── [신규] 월드맵 노드 런 상태 ──
        self.current_node_graph = None  # list[NodeData] or None
        self.current_node_id = -1  # 현재 위치 노드 id
        self._visiting_node_id = -1  # 진행 중(전투/휴식 중)인 노드 id
        self.victory_overlay_msg = ""
        os.makedirs("debug/snapshots", exist_ok=True)

        # ------------------------------------------------------------------
        # [신규] 에셋(이미지) 자동 매칭/로딩을 위한 최소 캐시 시스템
        #   - 파일명 규칙만 맞추면 자동으로 뜸
        #   - 없으면 None 반환 → 기존 UI로 안전하게 폴백
        # ------------------------------------------------------------------
        self.asset_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets"
        )
        self._img_cache = {}  # (rel_path, size, alpha) -> Surface or None

        # 자주 쓰는 기본 경로(규칙)
        self.asset_bg_dir = os.path.join(self.asset_root, "bg")
        self.asset_portrait_enemy_dir = os.path.join(
            self.asset_root, "portraits", "enemy"
        )
        self.asset_portrait_player_dir = os.path.join(
            self.asset_root, "portraits", "player"
        )

    def setup_font(self):
        """[수선] 폰트 로딩 중 발생하는 오류를 예법(Exception 명시)에 맞춰 처리합니다."""
        for f in ["applesdgothicneo", "malgungothic", "nanumgothic", "arial"]:
            try:
                self.font = pygame.font.SysFont(f, 18)
                self.font_small = pygame.font.SysFont(f, 14)
                self.font_name = pygame.font.SysFont(f, 26, bold=True)
                self.font_novel = pygame.font.SysFont(f, 20, italic=True)
                if self.font.render("한글", True, (0, 0, 0)).get_width() > 0:
                    break
            except Exception:  # [수정] bare except를 Exception으로 구체화했습니다.
                continue

    # --- [신규] 저장 및 불러오기 기능 ---
    def save_current_game(self):
        if not self.player:
            return
        data = {
            "player": self.player.to_dict(),
            "chapter": self.chapter,
            "encounter": self.encounter,
            "run_history": self.run_history,
        }
        if save_game_data(self.player.name, data):
            self.add_history("게임 기록을 저장함.")
            # 저장 성공 알림 (간단히 로그로 대체)

    def load_game_by_id(self, user_id):
        data = load_game_data(user_id)
        if data:
            self.player = Player.from_dict(data["player"], CARD_REGISTRY)
            self.chapter = data["chapter"]
            self.encounter = data["encounter"]
            self.run_history = data.get("run_history", [])
            self.phase = Phase.WORLD
            print(f"{user_id} 로드 완료!")
        else:
            # 파일이 없으면 새로 시작
            self.player = Player(user_id)
            self.player.initialize_deck(CARD_REGISTRY)
            self.chapter, self.encounter = 1, 1
            self.run_history = []
            self.phase = Phase.WORLD
            print(f"신규 유저 {user_id} 생성!")

    # ── [신규] 월드맵 노드 런 메서드 ──

    def _enter_region(self, region: str):
        """월드맵 노드 그래프를 생성하고 REGION_MAP 페이즈로 진입합니다."""
        from world.node_generator import generate_north_route

        if region == "north":
            self.current_node_graph = generate_north_route(SCREEN_WIDTH, SCREEN_HEIGHT)
            # 시작 노드(청운성) 자동 방문 처리
            self.current_node_graph[0].visited = True
            self.current_node_id = 0
            self._visiting_node_id = -1
        self.phase = Phase.REGION_MAP

    def _back_to_region_map(self):
        """현재 방문 중이던 노드를 완료로 표시하고 REGION_MAP으로 복귀합니다."""
        if self._visiting_node_id >= 0 and self.current_node_graph:
            node = next(
                (n for n in self.current_node_graph if n.id == self._visiting_node_id),
                None,
            )
            if node:
                node.visited = True
            self.current_node_id = self._visiting_node_id
            self._visiting_node_id = -1
        self.phase = Phase.REGION_MAP

    def _after_battle_continue(self):
        """전투 후 '강호 유랑' 버튼. 카드 보상이 있으면 먼저 표시, 그 다음 노드/조우로 이동."""
        self.victory_overlay = False
        # 준비된 카드 보상이 있으면 먼저 CARD_REWARD 화면으로
        # 보스 처치인데 보상이 아직 준비 안 됐다면 지금 준비
        if (
            not self.card_reward_choices
            and self.last_battle_rewards
            and self.last_battle_rewards.get("is_boss")
        ):
            self._prepare_boss_card_reward()
        if self.card_reward_choices:
            self.phase = Phase.CARD_REWARD
            return
        if self.current_node_graph:
            self._back_to_region_map()
        else:
            self.encounter += 1
            self.start_kangho_chuldo()

    def _visit_node(self, node_id: int):
        """노드를 방문합니다. 노드 타입에 따라 전투/휴식/수련으로 전환합니다."""
        if not self.current_node_graph:
            return
        node = next((n for n in self.current_node_graph if n.id == node_id), None)
        if not node or node.visited:
            return

        self._visiting_node_id = node_id

        from world.map_data import NodeType as NT_

        combat_types = {NT_.MOUNTAIN_PATH, NT_.OFFICIAL_ROAD, NT_.TOURNAMENT}

        if node.node_type in combat_types:
            from content.registry import ENEMY_REGISTRY
            from world.faction_data import build_enemy_for_node

            self.enemy = build_enemy_for_node(node, ENEMY_REGISTRY)
            self.battle_mgr = BattleManager(self.player, self.enemy, self)
            self.player.start_battle(CARD_REGISTRY)
            self.new_hap()
            self.phase = Phase.PLAYER_TURN
            intro_log = [
                {
                    "text": f"⚔️ {self.enemy.name}이(가) 길을 막아섭니다!",
                    "color": (255, 255, 255),
                }
            ]
            if node.is_boss:
                intro_log.insert(
                    0,
                    {
                        "text": "💀 보스 조우! 녹림왕이 나타났다!",
                        "color": (255, 80, 80),
                    },
                )
            self.battle_log = intro_log
            self.add_history(f"[{node.label}] {self.enemy.name}와(과) 조우함.")

        elif node.node_type == NT_.INN:
            self.phase = Phase.INN

        elif node.node_type == NT_.SECT_GATE:
            self.phase = Phase.TRAINING

        else:
            # BIG_CITY, SMALL_TOWN 등 즉시 완료
            node.visited = True
            self.current_node_id = node_id
            self._visiting_node_id = -1
            self.phase = Phase.REGION_MAP

    def render_region_map_to(self, surf):
        """REGION_MAP 페이즈 렌더링: 노드 그래프 표시 및 클릭 처리."""
        from world.region_map_renderer import render_region_map

        surf.fill((15, 20, 30))

        # 타이틀
        title = self.font_name.render("녹림 루트 ─ 북쪽 강호", True, (200, 180, 100))
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 18))

        # 플레이어 상태 (우상단)
        info = self.font_small.render(
            f"HP: {self.player.hp}/{self.player.max_hp}  금자: {self.player.gold}  XP: {self.player.xp}",
            True,
            (200, 200, 200),
        )
        surf.blit(info, (SCREEN_WIDTH - info.get_width() - 20, 18))

        # 노드 그래프 렌더링 (clickable rects 반환)
        clickable = render_region_map(
            surf,
            self.current_node_graph,
            self.current_node_id,
            self._visiting_node_id,
            self.font,
            self.font_small,
        )

        # 클릭 가능한 노드 → ui_buttons에 등록
        for node_id, rect in clickable.items():
            self.ui_buttons_next[f"node_{node_id}"] = {
                "rect": rect,
                "enabled": True,
                "on_click": lambda nid=node_id: self._visit_node(nid),
            }

        # 안내 텍스트
        hint = self.font_small.render(
            "빛나는 노드를 선택하여 진행하세요", True, (140, 140, 120)
        )
        surf.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 90))

        # 강호 대지로 귀환 버튼
        r_back = pygame.Rect(SCREEN_WIDTH - 210, SCREEN_HEIGHT - 65, 190, 48)
        self.ui_buttons_next["region_back_world"] = {
            "rect": r_back,
            "enabled": True,
            "on_click": lambda: [
                setattr(self, "current_node_graph", None),
                setattr(self, "current_node_id", -1),
                setattr(self, "_visiting_node_id", -1),
                setattr(self, "phase", Phase.WORLD),
            ],
        }
        pygame.draw.rect(surf, (55, 55, 55), r_back, border_radius=8)
        pygame.draw.rect(surf, (110, 110, 110), r_back, 1, border_radius=8)
        bt = self.font.render("강호 대지로", True, (200, 200, 200))
        surf.blit(
            bt,
            (
                r_back.centerx - bt.get_width() // 2,
                r_back.centery - bt.get_height() // 2,
            ),
        )

    # --- [신규] 로그인 화면 렌더링 ---
    def render_login_to(self, surf):
        surf.fill(COLOR_BLACK)
        title = self.font_name.render("구운록(九雲錄): 대천세상", True, COLOR_GOLD)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        prompt = self.font.render(
            "강호에 남길 이름을 입력하시오 (Enter):", True, COLOR_WHITE
        )
        surf.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 200))

        # 입력창 그리기
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 250, 300, 50)
        pygame.draw.rect(surf, (50, 50, 50), input_rect)
        pygame.draw.rect(surf, COLOR_GOLD, input_rect, 2)

        id_surf = self.font_name.render(self.input_id, True, COLOR_WHITE)
        surf.blit(id_surf, (input_rect.x + 10, input_rect.y + 10))

        # 기존 유저 목록 표시
        existing_users = get_existing_users()
        if existing_users:
            surf.blit(
                self.font_small.render(
                    "이어하기 가능한 무인들:", True, (150, 150, 150)
                ),
                (SCREEN_WIDTH // 2 - 150, 330),
            )
            for i, user in enumerate(existing_users):
                u_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 360 + i * 40, 300, 35)
                self.ui_buttons_next[f"login_{user}"] = {
                    "rect": u_btn_rect,
                    "enabled": True,
                    "on_click": lambda u=user: self.load_game_by_id(u),
                }
                pygame.draw.rect(surf, (30, 30, 60), u_btn_rect, border_radius=5)
                surf.blit(
                    self.font.render(user, True, COLOR_WHITE),
                    (u_btn_rect.x + 10, u_btn_rect.y + 8),
                )

    def add_history(self, msg):
        self.run_history.append(msg)

    def generate_death_novel(self):
        intro = f"강호의 어느 이름 모를 산길, {self.player.name}이라 불리던 한 무인이 첫 발을 내디뎠다."
        training_count = sum(1 for h in self.run_history if "연무장" in h)
        stats_msg = (
            f"그는 {training_count}번의 수련을 통해 {self.player.stats['근골']}의 근골과 {self.player.stats['심법']}의 심법을 얻었으나, "
            if training_count > 0
            else "그는 기틀을 닦기도 전에 가혹한 강호의 풍파를 정면으로 마주했다."
        )
        battle_summary = f"출도 이후 총 {self.encounter}번의 조우를 거치며 {self.chapter}장의 경지까지 도달했으나, "
        outro = f"마지막 순간, {self.enemy.name}의 공세를 이기지 못하고 고요히 눈을 감았다. 그가 남긴 투지는 먼지처럼 흩어졌으나, 그의 이름은 강호의 전설로 기억되리라."
        return [intro, stats_msg, battle_summary, outro]

    def start_kangho_chuldo(self):
        """챕터별 적 소환. 챕터1(1-5): 산적, 챕터2(6-20): 녹림, 챕터3(21+): 혈교"""
        level = self.encounter
        if self.encounter <= 5:
            # 챕터 1: 산적 구간
            if self.encounter == 5:
                self.enemy = Enemy("산적 부두목", hp=45, atk=7, level=level)
            elif self.encounter == 3:
                self.enemy = Enemy("산적 행동대장", hp=30, atk=5, level=level)
            else:
                self.enemy = Enemy("산적", hp=20, atk=4, level=level)
        elif self.encounter <= 20:
            # 챕터 2: 녹림 구간
            if self.encounter % 5 == 0:
                from content.enemies_nokrim import MaCheonGwang

                self.enemy = MaCheonGwang()
            elif self.encounter % 3 == 0:
                self.enemy = Enemy("녹림 행동대장", hp=60, atk=10, level=level + 1)
            else:
                self.enemy = Enemy("산채 졸개", hp=40, atk=7, level=level)
        else:
            # 챕터 3: 혈교 구간
            from content.enemies import HyulgyoGosu, HyulgyoJaGaek, HyulgyoJangro

            if self.encounter % 5 == 0:
                self.enemy = HyulgyoJangro()
            elif self.encounter % 3 == 0:
                self.enemy = HyulgyoGosu(level=level + 2)
            else:
                self.enemy = HyulgyoJaGaek(level=level)

        self.battle_mgr = BattleManager(self.player, self.enemy, self)
        self.player.start_battle(CARD_REGISTRY)
        self.new_hap()
        self.phase = Phase.PLAYER_TURN
        ch_info = get_chapter(self.encounter)
        intro_log = []
        if is_chapter_transition(self.encounter):
            intro_log.append({"text": f"📖 {ch_info['name']}", "color": COLOR_GOLD})
            intro_log.append({"text": ch_info["desc"], "color": (200, 200, 160)})
        intro_log.append(
            {
                "text": f"⚔️ {self.enemy.name}이(가) 길을 막아섭니다!",
                "color": COLOR_WHITE,
            }
        )
        self.battle_log = intro_log
        self.add_history(f"{self.enemy.name}와(과) 조우함.")

    def calculate_crit(self, card_type):
        crit_chance = max(
            1, 5 + (self.player.stats["행운"] * 0.8) - (self.enemy.level * 2)
        )
        if random.randint(1, 100) <= crit_chance:
            self.flash_alpha = 50
            if card_type == "공격":
                self.screen_shake, self.flash_color = 15, FLASH_RED
            elif card_type == "방어":
                self.flash_color = FLASH_BLUE
            else:
                self.flash_color = FLASH_GREEN
            return True
        return False

    def new_hap(self):
        """합 시작: 내공 풀충전 + 심법 추가 보너스, 방어는 근골/외공 기반 시작치."""
        self.player.discard_pile.extend(self.player.hand)
        self.player.hand = []

        self.player.recalculate_stats()
        self.player.energy = self.player.max_energy
        self.player.defense = self.player.base_defense  # 근골*0.6 + 외공*0.2
        self.player.draw_cards(5)
        self.player_slots, self.clashes_count = [], 0
        self.phase = Phase.PLAYER_TURN
        self.battle_mgr.prepare_enemy_intents()

    def attempt_escape(self):
        """경공을 이용한 도주 시도. 성공률 = min(60%, 10% + 경공*1.2%)"""
        escape_chance = int(self.player.flee_chance)
        if random.randint(1, 100) <= escape_chance:
            self.battle_log.append(
                {
                    "text": "💨 경공을 펼쳐 적의 포위를 빠져나왔다!",
                    "color": (150, 220, 150),
                }
            )
            self.player.win_streak = 0
            self.add_history(f"{self.enemy.name}에게서 도주 성공.")
            self.phase = Phase.WORLD
        else:
            self.battle_log.append(
                {
                    "text": f"💨 도주를 시도했으나 {self.enemy.name}에게 잡혔다!",
                    "color": (220, 100, 100),
                }
            )
            penalty_dmg = int(self.enemy.atk * 0.5)
            actual = self.player.take_damage(penalty_dmg)
            self.battle_log.append(
                {"text": f"뒤통수에 일격! 기혈 -{actual}", "color": (255, 80, 80)}
            )
            if self.player.hp <= 0:
                self.phase = Phase.GAMEOVER
                self.death_novel = self.generate_death_novel()

    def upgrade_stat(self, stat_name):
        """[정련] 중복 계산을 지우고, 통합 계산 함수를 호출하여 모든 수치를 동기화합니다."""
        if self.player.xp >= 50:
            self.player.xp -= 50
            self.player.stats[stat_name] += 1
            self.player.recalculate_stats()
            self.player.energy = self.player.max_energy
            self.add_history(f"연무장에서 {stat_name}을(를) 연마함.")

    def handle_input(self, event):
        """[수선] 격돌 연출 중 클릭 시 즉시 결과를 산출하는 로직을 추가했습니다."""

        # [신규 추가] 연출 중 마우스 클릭 시 즉시 종료 시퀀스 실행
        if self.clash_anim["active"] and event.type == pygame.MOUSEBUTTONDOWN:
            self.finish_clash_immediately()
            return

        # [예시] handle_input 함수 내부에 추가하면 좋은 로직
        if self.clash_anim["active"] and event.type == pygame.MOUSEBUTTONDOWN:
            # 현재 타이핑 중인 단계를 강제로 완료 상태로 점프!
            if self.clash_anim["stage"] in ["HEADER_TYPING", "RESULT_TYPING"]:
                # (로직 생략: 타이머를 조작하거나 char_idx를 끝까지 밀어버림)
                pass

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for bid in sorted(self.ui_buttons_active.keys(), reverse=True):
                btn = self.ui_buttons_active[bid]
                if btn["rect"].collidepoint(mx, my) and btn["enabled"]:
                    btn["on_click"]()
                    return

            if self.phase == Phase.PLAYER_TURN:
                if hasattr(self, "slot_rects"):
                    for i, rect in enumerate(self.slot_rects):
                        if rect.collidepoint(mx, my) and i < len(self.player_slots):
                            removed_card = self.player_slots.pop(i)
                            if removed_card.name not in [
                                "기본 공격",
                                "기본 방어",
                                "운기조식",
                            ]:
                                self.player.hand.append(removed_card)
                            return
                if hasattr(self, "card_rects"):
                    for i, rect in enumerate(self.card_rects):
                        if rect.collidepoint(mx, my):
                            self.add_card_to_slot(i)
                            return

    def finish_clash_immediately(self):
        """[신규] 남은 모든 격돌을 즉시 계산하고 결과를 로그에 새깁니다."""
        anim = self.clash_anim
        start_idx = anim["clash_idx"]

        # 1. 현재 남은 합부터 마지막 5합까지 루프로 즉시 처리
        for idx in range(start_idx, 5):
            if self.enemy.hp <= 0:  # 적이 이미 쓰러졌다면 중단
                break

            player_card = (
                self.player_slots[idx] if idx < len(self.player_slots) else None
            )
            enemy_intent = self.enemy.intent_queue[idx]

            # 에너지 소모 처리 (아직 소모되지 않은 합들만)
            # 현재 진행 중이던 합이 HEADER_INIT 이전이었다면 에너지 소모
            if idx > start_idx and player_card:
                self.player.energy -= player_card.base_cost
            elif idx == start_idx and anim["stage"] == "HEADER_INIT" and player_card:
                self.player.energy -= player_card.base_cost

            # 실제 대미지 및 효과 계산 실행 (BattleManager 호출)
            results = self.battle_mgr.resolve_single_clash(player_card, enemy_intent)

            # [신규] 즉시 처리 중 적이 쓰러졌다면 마지막 일격 기록
            if self.enemy.hp <= 0:
                self.last_kill_info = {
                    "card": (player_card.name if player_card else "무방비"),
                    "enemy_intent": enemy_intent,
                    "idx": idx,
                }

            # 로그에 결과 텍스트들 즉시 기록
            p_name = player_card.name if player_card else "무방비"
            header_text = f"▶ 제 {idx+1}합: {p_name} vs {enemy_intent}"
            self.battle_log.append({"text": header_text, "color": COLOR_WHITE})

            for line_text, line_color in results:
                self.battle_log.append({"text": line_text, "color": line_color})

        # 2. 모든 파티클 및 텍스트 효과 제거 및 연출 종료
        if hasattr(self, "clash_particles"):
            self.clash_particles.clear()
        if hasattr(self, "floating_texts"):
            self.floating_texts.clear()
        self.end_clash_sequence()

    def start_sequential_clash(self):
        """[수정] 'for' 루프를 제거했습니다. 이제 시스템이 멈추지 않고 연출 모드로 진입합니다."""
        if not self.player_slots:
            return

        self.phase = Phase.ENEMY_TURN
        # [변경] 연출에 필요한 정보를 저장하고 '활성화' 상태로 바꿉니다.
        self.clash_anim.update(
            {
                "active": True,
                "clash_idx": 0,
                "stage": "HEADER_INIT",
                "char_idx": 0,
                "timer": pygame.time.get_ticks(),
            }
        )
        self.current_clash_idx = 0

    def update_clash_animation(self):
        """[극상 수선] 로그(서사) 출력 후, 실제 HP/방어 변화가 적용되도록 타이밍을 제어합니다."""
        now = pygame.time.get_ticks()
        anim = self.clash_anim
        idx = anim["clash_idx"]

        # ⚠️ 여기서는 enemy.hp로 종료 판단하지 않는다.
        # (피해를 지연 적용할 수 있으므로, pending_state를 적용한 뒤에 죽음이 반영됨)
        if idx >= 5:
            self.end_clash_sequence()
            return

        if anim["stage"] == "HEADER_INIT":
            player_card = (
                self.player_slots[idx] if idx < len(self.player_slots) else None
            )
            p_name = player_card.name if player_card else "무방비"
            anim["full_text"] = (
                f"▶ 제 {idx+1}합: {p_name} vs {self.enemy.intent_queue[idx]}"
            )
            anim["clash_offset"] = 0
            self.battle_log.append({"text": "", "color": (255, 255, 255)})
            if player_card:
                self.player.energy -= player_card.base_cost
            anim["stage"], anim["char_idx"] = "HEADER_TYPING", 0

            # [신규] 이번 합 지연 적용 플래그 초기화
            anim.pop("pending_state", None)
            anim.pop("pre_state", None)
            anim["damage_applied"] = False
            anim["hits_spawned"] = False

        elif anim["stage"] == "HEADER_TYPING":
            if now - anim["timer"] > 20:
                if anim["char_idx"] < len(anim["full_text"]):
                    self.battle_log[-1]["text"] += anim["full_text"][anim["char_idx"]]
                    anim["char_idx"] += 1
                    anim["timer"] = now
                else:
                    anim["stage"], anim["timer"] = "WAIT_BEFORE_RESOLVE", now

        elif anim["stage"] == "WAIT_BEFORE_RESOLVE":
            anim["clash_offset"] = -15  # 기 모으기(Wind-up)
            if now - anim["timer"] > 400:
                player_card = (
                    self.player_slots[idx] if idx < len(self.player_slots) else None
                )
                enemy_intent = self.enemy.intent_queue[idx]

                # [핵심] 판정 전 상태 스냅샷(되돌리기용)
                pre_state = {
                    "p_hp": self.player.hp,
                    "p_def": self.player.defense,
                    "p_energy": self.player.energy,
                    "p_max_energy": self.player.max_energy,
                    "p_temp_bonus": self.player.temp_max_energy_bonus,
                    "e_hp": self.enemy.hp,
                    "e_def": self.enemy.defense,
                    "e_atk": self.enemy.atk,
                }

                # [수선] 파편 연출용 방어 수치 기록
                self.old_enemy_def = self.enemy.defense
                self.old_player_def = self.player.defense

                # 1) 먼저 판정을 '실제로' 돌려서 (로그/서사) sub_data를 만든다.
                anim["sub_data"] = self.battle_mgr.resolve_single_clash(
                    player_card, enemy_intent
                )

                # 2) 판정이 끝난 "결과 상태"를 저장한다.
                post_state = {
                    "p_hp": self.player.hp,
                    "p_def": self.player.defense,
                    "p_energy": self.player.energy,
                    "p_max_energy": self.player.max_energy,
                    "p_temp_bonus": self.player.temp_max_energy_bonus,
                    "e_hp": self.enemy.hp,
                    "e_def": self.enemy.defense,
                    "e_atk": self.enemy.atk,
                }

                # 3) 지금 당장은 결과 상태를 적용하지 않고, 원래 상태로 되돌린다.
                #    => 로그(서사)가 먼저 나오고, HP바는 그 후에 닳게 된다.
                self.player.hp = pre_state["p_hp"]
                self.player.defense = pre_state["p_def"]
                self.player.energy = pre_state["p_energy"]
                self.player.max_energy = pre_state["p_max_energy"]
                self.player.temp_max_energy_bonus = pre_state["p_temp_bonus"]
                self.enemy.hp = pre_state["e_hp"]
                self.enemy.defense = pre_state["e_def"]
                self.enemy.atk = pre_state["e_atk"]

                # 4) 나중에 적용할 pending_state로 저장
                anim["pending_state"] = post_state
                anim["pre_state"] = pre_state
                anim["damage_applied"] = False
                anim["hits_spawned"] = False

                # [신규] 이번 합에서 적이 죽는다면, 죽음 정보는 pending_state 기준으로 기록
                if post_state["e_hp"] <= 0:
                    self.last_kill_info = {
                        "card": (player_card.name if player_card else "무방비"),
                        "enemy_intent": enemy_intent,
                        "idx": idx,
                    }

                anim["current_line_idx"], anim["stage"] = 0, "RESULT_TYPING_INIT"

        elif anim["stage"] == "RESULT_TYPING_INIT":
            line_text, line_color = anim["sub_data"][anim["current_line_idx"]]
            import re

            dmg_match = re.search(r"(\d+)의", line_text)

            if dmg_match:
                is_enemy_hit = "적에게" in line_text

                # 타격 연출
                anim["clash_offset"] = 30 if is_enemy_hit else -30
                self.screen_shake = 25 if "치명" in line_text else 12

                # 무공 타입 추출
                p_card = (
                    self.player_slots[idx] if idx < len(self.player_slots) else None
                )
                m_type = "기본"
                if p_card:
                    if "검" in p_card.name:
                        m_type = "검"
                    elif "도" in p_card.name:
                        m_type = "도"
                    elif "권" in p_card.name or "장" in p_card.name:
                        m_type = "권"
                    elif "각" in p_card.name:
                        m_type = "각"

                # 파티클
                if not hasattr(self, "clash_particles"):
                    self.clash_particles = []

                slot_cx = (self.screen.get_width() - 540) // 2 + idx * 110 + 50
                impact_pos = [slot_cx, 140 if is_enemy_hit else 280]

                # ⚠️ 호신강기 파괴 판정은 실제 상태가 아직 적용 전일 수 있으므로
                # pending_state 기준으로 본다.
                pending = anim.get("pending_state")
                if pending and is_enemy_hit:
                    if pending["e_def"] <= 0 and self.old_enemy_def > 0:
                        self.spawn_shatter_particles(impact_pos, (100, 200, 255))

                self.spawn_martial_particles(impact_pos, m_type)

            # 말풍선 수치 — 첫 번째 결과 라인에서 무조건 1회 생성
            if not anim.get("hits_spawned", False):
                self._spawn_hit_indicators(idx, anim)
                anim["hits_spawned"] = True

            self.battle_log.append({"text": "", "color": line_color})
            anim["stage"], anim["char_idx"] = "RESULT_TYPING", 0

        elif anim["stage"] == "RESULT_TYPING":
            if anim.get("clash_offset", 0) > 0:
                anim["clash_offset"] -= 3
            elif anim.get("clash_offset", 0) < 0:
                anim["clash_offset"] += 3

            target_line_text = anim["sub_data"][anim["current_line_idx"]][0]

            if now - anim["timer"] > 8:
                if anim["char_idx"] < len(target_line_text):
                    self.battle_log[-1]["text"] += target_line_text[anim["char_idx"]]
                    anim["char_idx"] += 1
                    anim["timer"] = now
                else:
                    # ✅ [핵심] "피해/파쇄" 문장이 다 찍힌 뒤에 실제 HP/방어를 적용한다.
                    #    (선언/응수 문장은 제외하고, 전투 결과 문장(🗡️/🩸/🛡️ 등)에서 1회 적용)
                    if not anim.get("damage_applied", False) and anim.get(
                        "pending_state"
                    ):
                        is_result_line = (
                            target_line_text.startswith("🗡️")
                            or target_line_text.startswith("🩸")
                            or target_line_text.startswith("🛡️")
                        )
                        is_not_breath_line = not target_line_text.startswith(
                            "…숨을 삼킨다"
                        )
                        if is_result_line and is_not_breath_line:
                            pending = anim["pending_state"]
                            self.player.hp = pending["p_hp"]
                            self.player.defense = pending["p_def"]
                            self.player.energy = pending["p_energy"]
                            self.player.max_energy = pending["p_max_energy"]
                            self.player.temp_max_energy_bonus = pending["p_temp_bonus"]
                            self.enemy.hp = pending["e_hp"]
                            self.enemy.defense = pending["e_def"]
                            self.enemy.atk = pending["e_atk"]
                            anim["damage_applied"] = True

                    anim["current_line_idx"] += 1
                    if anim["current_line_idx"] < len(anim["sub_data"]):
                        anim["stage"], anim["timer"] = "RESULT_TYPING_INIT", now + 100
                    else:
                        anim["stage"], anim["timer"] = "WAIT_AFTER_ROUND", now

        elif anim["stage"] == "WAIT_AFTER_ROUND":
            anim["clash_offset"] = 0

            # 혹시 결과 문장이 하나도 없어서 damage_applied가 안 되었으면,
            # 이 타이밍에라도 pending_state를 적용해 둔다(안전장치).
            if anim.get("pending_state") and not anim.get("damage_applied", False):
                pending = anim["pending_state"]
                self.player.hp = pending["p_hp"]
                self.player.defense = pending["p_def"]
                self.player.energy = pending["p_energy"]
                self.player.max_energy = pending["p_max_energy"]
                self.player.temp_max_energy_bonus = pending["p_temp_bonus"]
                self.enemy.hp = pending["e_hp"]
                self.enemy.defense = pending["e_def"]
                self.enemy.atk = pending["e_atk"]
                anim["damage_applied"] = True

            if now - anim["timer"] > 1000:
                # 적이 여기서 죽었으면, 다음 합으로 넘기지 말고 바로 시퀀스 종료
                if self.enemy.hp <= 0:
                    self.end_clash_sequence()
                    return

                anim["clash_idx"] += 1
                self.current_clash_idx = anim["clash_idx"]
                anim["stage"] = "HEADER_INIT"

    def end_clash_sequence(self):
        """[신규] 연출 종료 후 뒷정리를 담당합니다."""
        self.clash_anim["active"] = False
        self.current_clash_idx = -1

        # ✅ 전투가 끝났으면 기본적으로 입력/오버레이 상태를 초기화
        # (적이 살아있으면 다음 턴으로 넘어가야 하므로 victory_overlay는 꺼져 있어야 함)
        if getattr(self, "victory_overlay", False) and (
            not hasattr(self, "enemy") or self.enemy.hp > 0
        ):
            self.victory_overlay = False
            self.victory_overlay_msg = ""

        # 슬롯에 올린 카드 정리
        for s_card in self.player_slots:
            if s_card.name not in ["기본 공격", "기본 방어", "운기조식"]:
                self.player.discard_pile.append(s_card)
        self.player_slots.clear()

        # 사망 처리
        if self.player.hp <= 0:
            self.player.hp = 0
            self.phase = Phase.GAMEOVER
            self.death_novel = self.generate_death_novel()
            return

        # ✅ 적이 죽었으면: (네가 만든) 승리 오버레이로 진입
        if self.enemy and self.enemy.hp <= 0:
            self.process_victory(set_phase=False)

            kill_info = getattr(self, "last_kill_info", None) or {}
            kill_card = kill_info.get("card", "무명의 초식")

            self.battle_log.append(
                {
                    "text": f"☠️ 「{kill_card}」의 여운 속에 {self.enemy.name}이(가) 무릎을 꿇고 쓰러진다.",
                    "color": (220, 220, 220),
                }
            )

            if self.last_battle_rewards:
                r = self.last_battle_rewards
                gold_txt = r.get("gold", 0)
                self.victory_overlay_msg = f"전리품: 공력(XP) +{r['xp']} | 금자 +{gold_txt} ({r['streak']}연승)"
                self.battle_log.append(
                    {"text": f"🏮 {self.victory_overlay_msg}", "color": (200, 200, 200)}
                )

            self.victory_overlay = True
            # 화면 전환 없이 전투 화면에서 버튼만 띄우는 구조라 phase는 큰 의미 없음(하지만 고정해둠)
            self.phase = Phase.ENEMY_TURN
            return

        # ✅ 적이 살아있으면: 무조건 다음 합(턴) 준비로 넘어간다
        self.victory_overlay = False
        self.victory_overlay_msg = ""
        self.new_hap()
        self.player.apply_clash_regen()  # 합 종료 회복은 new_hap 이후 (배틀 첫 합 제외)

    def prepare_victory_finish(self):
        """[신규] 적이 쓰러진 순간의 여운(마지막 일격/유언/보상)을 준비하고 마무리 화면으로 이동."""
        # 보상 계산은 기존 로직 재활용
        self.process_victory(set_phase=False)

        # 마지막 일격 정보(없으면 기본값)
        info = getattr(self, "last_kill_info", None) or {
            "card": "무명의 초식",
            "idx": 4,
        }
        kill_card = info.get("card", "무명의 초식")

        # 적 유언(간단 템플릿)
        name = self.enemy.name if self.enemy else "적"
        death_lines = [
            f"{name}: '크… 이 한 수… 대단하군…'",
            f"{name}: '강호는… 넓다… 다음엔… 지지 않겠다…'",
            f"{name}: '내가… 여기서… 끝이라니…'",
            f"{name}: '그 초식… 기억해두겠다…'",
        ]
        self.victory_story_lines = [
            f"마지막으로 너는 「{kill_card}」를 틀어쥐고, 숨통을 끊었다.",
            random.choice(death_lines),
        ]

        # 마무리 페이즈로
        self.phase = Phase.VICTORY_FINISH

    def draw_battle_base_ui_to(self, surf):
        """[수선] 기혈 잔상(Visual HP)과 호신강기(Defense)를 바에 반영합니다."""
        self.player.recalculate_stats()

        def _slug(name: str) -> str:
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

        def _load_img(rel_path, size=None, alpha=True):
            key = (rel_path, size, alpha)
            if key in self._img_cache:
                return self._img_cache[key]
            full_path = os.path.join(self.asset_root, rel_path)
            if not os.path.exists(full_path):
                self._img_cache[key] = None
                return None
            try:
                img = pygame.image.load(full_path)
                img = img.convert_alpha() if alpha else img.convert()
                if size:
                    img = pygame.transform.smoothscale(img, size)
                self._img_cache[key] = img
                return img
            except Exception:
                self._img_cache[key] = None
                return None

        hdr = f"PHASE={self.phase} chapter={self.chapter} encounter={self.encounter}"
        surf.blit(self.font.render(hdr, True, COLOR_WHITE), (20, 15))

        # --------------------------
        # [신규] 플레이어 초상화
        # --------------------------
        if self.player:
            p_slug = _slug(self.player.name)
            p_img = _load_img(
                os.path.join("portraits", "player", f"{p_slug}.png"),
                size=(96, 96),
                alpha=True,
            )
            if p_img:
                p_rect = pygame.Rect(0, 0, 96, 96)
                p_rect.topleft = (20, 60)
                surf.blit(p_img, p_rect.topleft)
                pygame.draw.rect(surf, (255, 255, 255), p_rect, 2, border_radius=8)

        surf.blit(self.font_name.render(self.player.name, True, COLOR_WHITE), (130, 75))

        draw_stat_bar(
            surf,
            20,
            120,
            260,
            20,
            self.player.hp,
            self.player.max_hp,
            COLOR_GREEN,
            "기혈",
            self.font,
            visual_current=self.player_visual_hp,
            shield=self.player.defense,
        )

        energy_txt = f"내공: {self.player.energy}/{self.player.max_energy}"
        surf.blit(self.font.render(energy_txt, True, COLOR_GOLD), (20, 148))

        surf.blit(
            self.font.render(
                f"공격력: {self.player.attack_power}", True, (255, 100, 100)
            ),
            (20, 175),
        )
        surf.blit(
            self.font.render(f"강기: {self.player.defense}", True, (100, 150, 255)),
            (20, 200),
        )

        if hasattr(self, "enemy") and self.enemy:
            # --------------------------
            # [신규] 적 초상화
            # --------------------------
            e_slug = _slug(self.enemy.name)
            e_img = _load_img(
                os.path.join("portraits", "enemy", f"{e_slug}.png"),
                size=(96, 96),
                alpha=True,
            )
            if e_img:
                e_rect = pygame.Rect(0, 0, 96, 96)
                e_rect.topleft = (1170, 60)
                surf.blit(e_img, e_rect.topleft)
                pygame.draw.rect(surf, (255, 255, 255), e_rect, 2, border_radius=8)

            surf.blit(
                self.font_name.render(self.enemy.name, True, COLOR_WHITE), (950, 75)
            )

            draw_stat_bar(
                surf,
                950,
                120,
                215,
                20,
                self.enemy.hp,
                self.enemy.max_hp,
                COLOR_RED,
                "적 기혈",
                self.font,
                visual_current=self.enemy_visual_hp,
                shield=self.enemy.defense,
            )

            from ui.widgets import draw_enemy_intent_box

            draw_enemy_intent_box(surf, 950, 40, self.enemy.intent_queue, self.font)

    def render_battle_screen_to(self, surf):
        """[생략 금지] 적 의도 슬롯을 비급 카드 형태로 렌더링하도록 수선된 전문입니다."""
        victory_mode = getattr(self, "victory_overlay", False)

        # ---------------------------------------------------------
        # [신규] 전투 배경 자동 로드/표시 (없으면 그냥 넘어감)
        # 규칙: assets/bg/battle.png
        # ---------------------------------------------------------
        def _load_img(rel_path, size=None, alpha=True):
            key = (rel_path, size, alpha)
            if key in self._img_cache:
                return self._img_cache[key]

            full_path = os.path.join(self.asset_root, rel_path)
            if not os.path.exists(full_path):
                self._img_cache[key] = None
                return None

            try:
                img = pygame.image.load(full_path)
                img = img.convert_alpha() if alpha else img.convert()
                if size:
                    img = pygame.transform.smoothscale(img, size)
                self._img_cache[key] = img
                return img
            except Exception:
                self._img_cache[key] = None
                return None

        bg = _load_img(
            os.path.join("bg", "battle.png"),
            size=(surf.get_width(), surf.get_height()),
            alpha=False,
        )
        if bg:
            surf.blit(bg, (0, 0))
            # 배경 위에 반투명 어두운 오버레이를 씌워 가독성 확보
            overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 155))
            surf.blit(overlay, (0, 0))

        # 1. 기초 UI 및 기혈바 출력
        self.draw_battle_base_ui_to(surf)

        is_animating = self.clash_anim.get("active", False)

        # 연출 중이 아닐 때만 기술 패널(기본 공격/방어 등)을 그립니다.
        if not is_animating and not victory_mode:
            self.render_basic_technique_panel(surf)

        # 에너지 및 슬롯 계산
        slot_w, slot_h, start_x = 100, 130, (surf.get_width() - 540) // 2
        self.slot_rects = []

        temp_energy = self.player.energy
        for card in self.player_slots:
            temp_energy -= card.base_cost
            if "운기조식" in card.name:
                temp_energy = min(self.player.max_energy, temp_energy + 2)
        self.current_rem_energy = temp_energy

        # [연출] 애니메이션 중 스포트라이트와 HP바 강조
        if is_animating:
            surf.blit(self.dim_surf, (0, 0))
            self.draw_battle_base_ui_to(surf)

        # 2. 슬롯 렌더링 (격돌 오프셋 및 기세 스케일링 적용)
        for i in range(5):
            x = start_x + i * 110
            is_active = i == self.current_clash_idx

            # 연출 중에는 활성 슬롯만 하이라이트
            if is_animating and not is_active:
                continue

            # 격돌 시 중앙으로 모이는 오프셋
            offset_y = self.clash_anim.get("clash_offset", 0) if is_active else 0

            # [기세] 격돌 중인 슬롯은 12px 확장
            bonus = 12 if (is_animating and is_active) else 0
            current_w = slot_w + bonus
            current_h = slot_h + bonus
            draw_x = x - (bonus // 2)

            border_color = COLOR_GOLD if is_active else (40, 40, 40)
            border_width = (
                6 if (is_animating and is_active) else (4 if is_active else 1)
            )

            # 적 슬롯 — 아이콘을 먼저 그리고 테두리를 위에 덮어 테두리가 보이게 함
            i_rect = pygame.Rect(draw_x, 140 + offset_y, current_w, current_h)
            self.draw_intent_icon_to(
                surf,
                (
                    self.enemy.intent_queue[i]
                    if i < len(self.enemy.intent_queue)
                    else "???"
                ),
                i_rect.center,
            )
            pygame.draw.rect(surf, border_color, i_rect, border_width, border_radius=5)

            # 플레이어 슬롯
            p_rect = pygame.Rect(draw_x, 280 - offset_y, current_w, current_h)
            self.slot_rects.append(p_rect)

            if i < len(self.player_slots):
                self.draw_mini_card(
                    surf, self.player_slots[i], p_rect, i < self.current_clash_idx
                )
            else:
                pygame.draw.rect(surf, (20, 20, 20), p_rect, border_radius=5)
                pygame.draw.rect(
                    surf, border_color, p_rect, border_width, border_radius=5
                )

        # 3. 파티클
        if hasattr(self, "clash_particles"):
            for p in self.clash_particles[:]:
                p["pos"][0] += p["vel"][0]
                p["pos"][1] += p["vel"][1]
                p["life"] -= 1

                if p["life"] <= 0:
                    self.clash_particles.remove(p)
                    continue

                alpha = max(0, min(255, p["life"] * 8))
                color = [max(0, c * (alpha / 255)) for c in p["color"]]
                px, py = p["pos"]
                m_type = p.get("m_type", "기본")

                if m_type == "검":
                    pygame.draw.line(surf, color, (px - 4, py + 4), (px + 4, py - 4), 2)
                elif m_type == "도":
                    pygame.draw.line(surf, color, (px - 6, py - 6), (px + 6, py + 6), 5)
                elif m_type == "권":
                    pygame.draw.circle(
                        surf, color, (int(px), int(py)), random.randint(3, 7)
                    )
                    pygame.draw.circle(surf, COLOR_WHITE, (int(px), int(py)), 2)
                else:
                    pygame.draw.circle(
                        surf, color, (int(px), int(py)), max(1, p["life"] // 8)
                    )

        # 4. 플로팅 텍스트
        FADE_FRAMES = 28
        if hasattr(self, "floating_texts"):
            for ft in self.floating_texts[:]:
                # delay 중이면 대기
                if ft.get("delay", 0) > 0:
                    ft["delay"] -= 1
                    continue

                # pop-in 연출: 처음 8프레임은 위로 살짝 튀어오름
                ft["pos"][1] += ft["vel"][1]
                ft["vel"][1] = ft["vel"][1] * 0.72  # 빠르게 감속 → 정지

                alpha = int(255 * min(1.0, ft["life"] / FADE_FRAMES))

                cx, cy = int(ft["pos"][0]), int(ft["pos"][1])
                p_font = self.font_name
                txt_color = ft.get("text_color", (240, 240, 240))

                if ft.get("style") == "card":
                    accent = ft["color"]
                    txt_surf = p_font.render(ft["text"], True, txt_color)
                    pad_x, pad_y = 14, 7
                    bw = txt_surf.get_width() + pad_x * 2 + 6  # +6 for accent bar
                    bh = txt_surf.get_height() + pad_y * 2

                    tmp = pygame.Surface((bw + 2, bh + 2), pygame.SRCALPHA)
                    tmp.fill((0, 0, 0, 0))

                    # 그림자
                    pygame.draw.rect(
                        tmp, (0, 0, 0, min(160, alpha)), (3, 3, bw, bh), border_radius=7
                    )
                    # 본체 (어두운 반투명 배경)
                    pygame.draw.rect(
                        tmp,
                        (14, 17, 28, min(230, alpha)),
                        (1, 1, bw, bh),
                        border_radius=7,
                    )
                    # 컬러 테두리 (1px)
                    border_a = min(alpha, 200)
                    pygame.draw.rect(
                        tmp, accent + (border_a,), (1, 1, bw, bh), 1, border_radius=7
                    )
                    # 좌측 악센트 바
                    bar_rect = pygame.Rect(1, 1, 5, bh)
                    pygame.draw.rect(
                        tmp,
                        accent + (min(alpha, 220),),
                        bar_rect,
                        border_top_left_radius=7,
                        border_bottom_left_radius=7,
                    )
                    # 텍스트
                    txt_a = p_font.render(ft["text"], True, txt_color + (alpha,))
                    tmp.blit(txt_a, (1 + 6 + pad_x, 1 + pad_y))

                    surf.blit(tmp, (cx - bw // 2, cy - bh // 2))
                else:
                    faded = tuple(int(c * alpha / 255) for c in txt_color)
                    plain = p_font.render(ft["text"], True, faded)
                    surf.blit(
                        plain,
                        (cx - plain.get_width() // 2, cy - plain.get_height() // 2),
                    )

                ft["life"] -= 1
                if ft["life"] <= 0:
                    self.floating_texts.remove(ft)

        # 5. 로그 출력
        log_y_start = 430
        for i, log_entry in enumerate(self.battle_log[-10:]):
            color = (
                log_entry.get("color", COLOR_WHITE)
                if isinstance(log_entry, dict)
                else (240, 240, 240)
            )
            text = (
                log_entry.get("text", "") if isinstance(log_entry, dict) else log_entry
            )
            surf.blit(
                self.font_small.render(text.split("\n")[0], True, color),
                (start_x, log_y_start + i * 28),
            )

        # 6. 에너지/UI  (슬롯 아래 중앙에 배치 — 슬롯 끝 y≈410 바로 아래)
        energy_rect = pygame.Rect(start_x + 210, 415, 160, 36)
        pygame.draw.rect(surf, (30, 30, 50), energy_rect, border_radius=10)
        surf.blit(
            self.font.render(
                f"잔여 氣: {self.current_rem_energy}",
                True,
                COLOR_GOLD if self.current_rem_energy >= 0 else COLOR_RED,
            ),
            (energy_rect.x + 15, energy_rect.y + 18),
        )

        if not is_animating and not victory_mode:
            if self.phase == Phase.PLAYER_TURN:
                ready = len(self.player_slots) > 0 and self.current_rem_energy >= 0
                btn_rect = pygame.Rect(1040, 630, 160, 55)
                self.ui_buttons_next["start_clash"] = {
                    "rect": btn_rect,
                    "enabled": ready,
                    "on_click": self.start_sequential_clash,
                }
                pygame.draw.rect(
                    surf,
                    COLOR_GOLD if ready else COLOR_GRAY,
                    btn_rect,
                    border_radius=10,
                )
                txt = self.font.render(
                    (
                        "초식 전개"
                        if ready
                        else (
                            "내공 부족" if self.current_rem_energy < 0 else "초식 대기"
                        )
                    ),
                    True,
                    COLOR_WHITE,
                )
                surf.blit(
                    txt,
                    (
                        btn_rect.centerx - txt.get_width() // 2,
                        btn_rect.centery - txt.get_height() // 2,
                    ),
                )

                # 도주 버튼 (경공 기반 성공률)
                escape_chance = int(self.player.flee_chance)
                escape_rect = pygame.Rect(1040, 692, 160, 36)
                self.ui_buttons_next["escape"] = {
                    "rect": escape_rect,
                    "enabled": True,
                    "on_click": self.attempt_escape,
                }
                pygame.draw.rect(surf, (80, 50, 20), escape_rect, border_radius=8)
                pygame.draw.rect(surf, (140, 90, 40), escape_rect, 1, border_radius=8)
                esc_txt = self.font_small.render(
                    f"도주({escape_chance}%)", True, (200, 180, 140)
                )
                surf.blit(
                    esc_txt,
                    (
                        escape_rect.centerx - esc_txt.get_width() // 2,
                        escape_rect.centery - esc_txt.get_height() // 2,
                    ),
                )

            self.render_player_hand_to(surf)

        # --- 승리 오버레이 ---
        if victory_mode:
            surf.blit(self.dim_surf, (0, 0))
            self.draw_battle_base_ui_to(surf)

            msg = getattr(self, "victory_overlay_msg", "")
            if msg:
                t = self.font.render(msg, True, COLOR_GOLD)
                surf.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 470))

            r_yulang = pygame.Rect(SCREEN_WIDTH // 2 - 260, 520, 240, 60)
            self.ui_buttons_next["yulang"] = {
                "rect": r_yulang,
                "enabled": True,
                "on_click": self._after_battle_continue,
            }
            pygame.draw.rect(surf, (34, 139, 34), r_yulang, border_radius=10)
            surf.blit(
                self.font.render("강호 유랑", True, COLOR_WHITE),
                (r_yulang.x + 70, r_yulang.y + 20),
            )

            r_back = pygame.Rect(SCREEN_WIDTH // 2 + 20, 520, 240, 60)
            self.ui_buttons_next["back_world"] = {
                "rect": r_back,
                "enabled": True,
                "on_click": lambda: [
                    setattr(self, "victory_overlay", False),
                    setattr(self, "phase", Phase.WORLD),
                ],
            }
            pygame.draw.rect(surf, COLOR_GRAY, r_back, border_radius=10)
            surf.blit(
                self.font.render("강호 대지로", True, COLOR_WHITE),
                (r_back.x + 60, r_back.y + 20),
            )

    def _spawn_hit_indicators(self, idx, anim):
        """카드 충돌 지점에 피해·방어·기혈 변화 수치를 겹치지 않게 순서대로 표시합니다.
        순서: ① 총 대미지 → ② 강기 흡수 → ③ 실제 HP 피해
        위치는 고정 슬롯 Y로 배치해 겹침 없음. 1.5초 유지 후 페이드아웃.
        """
        if not hasattr(self, "floating_texts"):
            self.floating_texts = []

        pre = anim.get("pre_state", {})
        post = anim.get("pending_state", {})
        if not pre or not post:
            return

        slot_cx = (self.screen.get_width() - 540) // 2 + idx * 110 + 50
        # 적 카드 위 → 위쪽 방향으로 스택 (y값이 작을수록 위)
        # 플레이어 카드 아래 → 아래쪽 방향으로 스택
        E_BASE = 130  # 적 측 가장 아래 버블 Y
        P_BASE = 360  # 플레이어 측 가장 위 버블 Y
        STEP = 38  # 버블 간 수직 간격
        LIFE = 95  # ≈1.6초 @ 60fps

        def card_bubble(text, color, x, anchor_y, delay, pop_dir=-1):
            """pop_dir: -1=위로 팝, +1=아래로 팝"""
            return {
                "text": text,
                "pos": [float(x), float(anchor_y + pop_dir * 10)],
                "vel": [0.0, float(pop_dir * -3.5)],  # 튀어오름 후 감속 정지
                "color": color,
                "text_color": (235, 240, 248),
                "style": "card",
                "life": LIFE,
                "delay": delay,
            }

        # ── 적 측 (플레이어가 공격) — E_BASE에서 위로 쌓임
        e_def_lost = pre["e_def"] - post["e_def"]
        e_hp_lost = pre["e_hp"] - post["e_hp"]
        e_raw = e_def_lost + e_hp_lost

        e_row = 0
        if e_raw > 0:
            self.floating_texts.append(
                card_bubble(
                    f"공격  {e_raw}",
                    (255, 140, 30),
                    slot_cx,
                    E_BASE - e_row * STEP,
                    delay=0,
                )
            )
            e_row += 1
        if e_def_lost > 0:
            self.floating_texts.append(
                card_bubble(
                    f"강기  -{e_def_lost}",
                    (70, 185, 255),
                    slot_cx,
                    E_BASE - e_row * STEP,
                    delay=10,
                )
            )
            e_row += 1
        if e_hp_lost > 0:
            self.floating_texts.append(
                card_bubble(
                    f"피해  -{e_hp_lost}",
                    (255, 215, 30),
                    slot_cx,
                    E_BASE - e_row * STEP,
                    delay=20,
                )
            )

        # ── 플레이어 측 (적이 공격) — P_BASE에서 아래로 쌓임
        p_def_lost = pre["p_def"] - post["p_def"]
        p_hp_lost = pre["p_hp"] - post["p_hp"]
        p_raw = p_def_lost + p_hp_lost

        p_row = 0
        if p_raw > 0:
            self.floating_texts.append(
                card_bubble(
                    f"공격  {p_raw}",
                    (255, 140, 30),
                    slot_cx,
                    P_BASE + p_row * STEP,
                    delay=0,
                    pop_dir=1,
                )
            )
            p_row += 1
        if p_def_lost > 0:
            self.floating_texts.append(
                card_bubble(
                    f"강기  -{p_def_lost}",
                    (70, 120, 255),
                    slot_cx,
                    P_BASE + p_row * STEP,
                    delay=10,
                    pop_dir=1,
                )
            )
            p_row += 1
        if p_hp_lost > 0:
            self.floating_texts.append(
                card_bubble(
                    f"피해  -{p_hp_lost}",
                    (235, 60, 60),
                    slot_cx,
                    P_BASE + p_row * STEP,
                    delay=20,
                    pop_dir=1,
                )
            )

        # ── 플레이어 방어 획득 (방어 카드)
        p_def_gain = post["p_def"] - pre["p_def"]
        if p_def_gain > 0:
            self.floating_texts.append(
                card_bubble(
                    f"강기  +{p_def_gain}",
                    (60, 130, 255),
                    slot_cx,
                    P_BASE,
                    delay=0,
                    pop_dir=1,
                )
            )

        # ── 기혈 회복
        p_heal = post["p_hp"] - pre["p_hp"]
        if p_heal > 0:
            self.floating_texts.append(
                card_bubble(
                    f"기혈  +{p_heal}",
                    (50, 200, 100),
                    slot_cx,
                    P_BASE + STEP,
                    delay=0,
                    pop_dir=1,
                )
            )

        # ── 내공 변화
        p_energy_lost = pre["p_energy"] - post["p_energy"]
        if p_energy_lost > 0:
            self.floating_texts.append(
                card_bubble(
                    f"내공  -{p_energy_lost}",
                    (185, 85, 240),
                    slot_cx,
                    P_BASE + STEP * 2,
                    delay=0,
                    pop_dir=1,
                )
            )
        p_energy_gain = post["p_energy"] - pre["p_energy"]
        if p_energy_gain > 0:
            self.floating_texts.append(
                card_bubble(
                    f"내공  +{p_energy_gain}",
                    (155, 220, 55),
                    slot_cx,
                    P_BASE + STEP * 2,
                    delay=0,
                    pop_dir=1,
                )
            )

    def spawn_martial_particles(self, pos, m_type):
        """[수선] 무공 종류에 따라 색상뿐만 아니라 '형태(Type)' 정보도 함께 저장합니다."""
        colors = {
            "검": (200, 255, 255),  # 예리한 청백색
            "도": (255, 150, 50),  # 묵직한 오렌지
            "권": (255, 255, 150),  # 충격의 황색
            "각": (150, 255, 150),  # 바람의 녹색
            "기본": (255, 255, 255),
        }
        color = colors.get(m_type, (255, 255, 255))

        for _ in range(15):
            self.clash_particles.append(
                {
                    "pos": list(pos),
                    "vel": [random.uniform(-6, 6), random.uniform(-6, 6)],
                    "color": color,
                    "life": random.randint(15, 30),
                    "m_type": m_type,  # 형태 구분을 위해 추가
                }
            )

    def draw_clash_particles(self, surf):
        """[신규] 저장된 기운들을 화면에 형상화합니다. 위치 갱신과 드로잉을 동시에 처리합니다."""
        # 역순으로 순회하여 삭제 시 인덱스 오류 방지
        for p in self.clash_particles[:]:
            # 1. 위치 갱신: pos = pos + vel
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 1

            if p["life"] <= 0:
                self.clash_particles.remove(p)
                continue

            # 2. 수명에 따른 투명도 계산 (색상을 어둡게 만들어 페이드 아웃 효과)
            alpha = max(0, min(255, p["life"] * 8))
            current_color = [max(0, c * (alpha / 255)) for c in p["color"]]

            # 3. 무공 종류별 형상화 (주인님의 아이디어 적용)
            px, py = p["pos"]
            if p["m_type"] == "검":
                # 예리한 사선 (/)
                pygame.draw.line(
                    surf, current_color, (px - 4, py + 4), (px + 4, py - 4), 2
                )
            elif p["m_type"] == "도":
                # 굵고 묵직한 반대 사선 (\)
                pygame.draw.line(
                    surf, current_color, (px - 6, py - 6), (px + 6, py + 6), 5
                )
            elif p["m_type"] == "권":
                # 주먹 모양을 형상화한 이중 원형 (충격파)
                pygame.draw.circle(
                    surf, current_color, (int(px), int(py)), random.randint(3, 6)
                )
                pygame.draw.circle(
                    surf, COLOR_WHITE, (int(px), int(py)), 2
                )  # 중심점 반짝임
            elif p["m_type"] == "각":
                # 바람을 가르는 십자 모양 (+)
                pygame.draw.line(surf, current_color, (px - 5, py), (px + 5, py), 2)
                pygame.draw.line(surf, current_color, (px, py - 5), (px, py + 5), 2)
            else:
                # 기본: 작은 점
                pygame.draw.circle(surf, current_color, (int(px), int(py)), 2)

    def spawn_shatter_particles(self, pos, color):
        """호신강기가 깨질 때 유리 파편 효과를 생성합니다."""
        for _ in range(25):
            self.clash_particles.append(
                {
                    "pos": list(pos),
                    "vel": [random.uniform(-7, 7), random.uniform(-7, 7)],
                    "color": color,
                    "life": random.randint(30, 60),
                }
            )

    def add_card_to_slot(self, card_idx):
        if card_idx < len(self.player.hand):
            card = self.player.hand[card_idx]
            if card.base_cost <= self.current_rem_energy and len(self.player_slots) < 5:
                self.player_slots.append(self.player.hand.pop(card_idx))

    def add_basic_card_to_slot(self, card_name):
        """[수선] 함수 내부에 있던 중복 import 문들을 제거하여 사관의 지적을 해결했습니다."""
        # [수정] 내부 import copy와 from content.registry 문을 삭제했습니다.
        # 이 도구들은 이제 파일 최상단에서 관리됩니다.

        template = CARD_REGISTRY.get(card_name)
        if template and len(self.player_slots) < 5:
            if template.base_cost <= self.current_rem_energy:
                self.player_slots.append(copy.deepcopy(template))

    def render_training_to(self, surf):
        """[통합 수선] 신체 단련(설명 추가)과 무공 연마를 한 화면에서 처리합니다."""
        # 1. 상단 제목 및 보유 공력 표시
        surf.blit(
            self.font_name.render("연무장: 신체와 초식을 단련합니다", True, COLOR_GOLD),
            (400, 40),
        )
        surf.blit(
            self.font.render(f"보유 공력(XP): {self.player.xp}", True, COLOR_WHITE),
            (500, 90),
        )

        # 2. [좌측] 기초 스탯 단련 영역 (효과 설명 추가)
        surf.blit(self.font.render("[ 기초 스탯 단련 ]", True, COLOR_GOLD), (150, 140))

        # [신규] 스탯별 상세 효과 설명서
        p = self.player
        stat_desc = {
            "근골": f"기혈 +10 | 방어 시작치 +0.6 | 합 종료 HP +{p.clash_hp_regen}",
            "심법": f"내공/회복 증가 | 합 시작 EN +{p.clash_en_regen} (추가 보너스)",
            "외공": "공격력 +1 (주) | 방어 시작치 +0.2 (보조) | 물리 무공 계수",
            "경공": f"회피율 {min(25, int((0.05 + p.stats['경공']*0.007)*100))}% | 도주 {int(p.flee_chance)}%",
            "자질": "전투 승리 XP +3%/레벨",
            "행운": "치명타 확률 증가",
        }

        for i, (s, v) in enumerate(self.player.stats.items()):
            # [수정] 설명을 넣기 위해 버튼 높이를 키우고(45->60), 간격을 벌림(55->70)
            r = pygame.Rect(100, 180 + i * 70, 350, 60)

            self.ui_buttons_next[f"train_{s}"] = {
                "rect": r,
                "enabled": self.player.xp >= 50,
                "on_click": lambda name=s: self.upgrade_stat(name),
            }

            # 버튼 배경 및 테두리
            pygame.draw.rect(
                surf,
                (40, 40, 60) if self.player.xp >= 50 else (20, 20, 20),
                r,
                border_radius=5,
            )
            pygame.draw.rect(
                surf,
                COLOR_GOLD if self.player.xp >= 50 else COLOR_GRAY,
                r,
                1,
                border_radius=5,
            )

            # [수정] 텍스트 1: 스탯 이름과 현재 수치 (위쪽 배치)
            label = f"{s}: {v}"
            if s == "심법":
                label += f" (내공: {self.player.max_energy})"

            surf.blit(self.font.render(label, True, COLOR_WHITE), (r.x + 15, r.y + 10))

            # [신규] 텍스트 2: 효과 설명 (아래쪽 배치, 작은 회색 글씨)
            desc_text = stat_desc.get(s, "능력치 상승")
            surf.blit(
                self.font_small.render(f"└ {desc_text}", True, (180, 180, 180)),
                (r.x + 15, r.y + 35),
            )

            # [신규] 텍스트 3: 비용 (우측 배치)
            cost_txt = "XP 50"
            surf.blit(
                self.font_small.render(
                    cost_txt, True, COLOR_GOLD if self.player.xp >= 50 else COLOR_GRAY
                ),
                (r.right - 50, r.centery - 7),
            )

        # 3. [우측] 무공 초식 연마 영역 (이전 명상 기능을 이식)
        surf.blit(self.font.render("[ 무공 초식 연마 ]", True, COLOR_GOLD), (700, 140))
        for i, card in enumerate(self.player.deck):
            # 카드가 리스트를 벗어나지 않게 최대 8개까지만 표시
            if i >= 8:
                break

            cost = card.get_upgrade_cost()
            # 위치를 오른쪽으로 조정 (x=650)
            r = pygame.Rect(650, 180 + i * 55, 450, 45)
            can_up = self.player.xp >= cost and card.mastery < card.mastery_max

            self.ui_buttons_next[f"meditate_{card.name}"] = {
                "rect": r,
                "enabled": can_up,
                "on_click": lambda c=card, p=cost: [
                    setattr(self.player, "xp", self.player.xp - p),
                    c.upgrade(),
                ],
            }

            # 버튼 배경 및 테두리
            pygame.draw.rect(
                surf,
                (40, 60, 40) if can_up else (20, 20, 20),
                r,
                border_radius=5,
            )
            pygame.draw.rect(
                surf,
                COLOR_GREEN if can_up else COLOR_GRAY,
                r,
                1,
                border_radius=5,
            )

            # 카드 강화 라벨 표시
            if card.mastery < card.mastery_max:
                label = f"{card.name} ({card.mastery}성) -> 강화 XP: {cost}"
            else:
                label = f"{card.name} [완성: {card.mastery}성]"
            surf.blit(self.font.render(label, True, COLOR_WHITE), (r.x + 20, r.y + 12))

    def render_inn_to(self, surf):
        """[통합 구현] 휴식, 식사(버프), 수련, 소문을 아우르는 종합 객잔 시스템입니다."""
        # 1. 배경 및 기본 정보
        header = self.font_name.render(
            "🏮 객잔 (Drunken Immortal Inn)", True, COLOR_GOLD
        )
        surf.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 40))

        status_txt = (
            f"금자: {self.player.gold} | 기혈: {self.player.hp}/{self.player.max_hp}"
        )
        if self.player.inn_buff:
            status_txt += f" | 식사 효과: {self.player.inn_buff['name']}"

        st_surf = self.font.render(status_txt, True, COLOR_WHITE)
        surf.blit(st_surf, (SCREEN_WIDTH // 2 - st_surf.get_width() // 2, 80))

        # ---------------------------------------------------------
        # [A 구역] 객잔 투숙 (휴식) - 좌측 상단
        # ---------------------------------------------------------
        surf.blit(self.font.render("[ 객잔 투숙 ]", True, COLOR_GOLD), (150, 140))
        rest_menus = [
            {"label": "쪽잠 (50%)", "ratio": 0.5, "cost": 15},
            {"label": "숙면 (100%)", "ratio": 1.0, "cost": 30},
        ]

        for i, menu in enumerate(rest_menus):
            r = pygame.Rect(100, 180 + i * 70, 300, 60)
            cost = menu["cost"]
            can_buy = self.player.gold >= cost and self.player.hp < self.player.max_hp

            # 클로저: 회복 로직
            def make_rest(c=cost, ratio=menu["ratio"], label=menu["label"]):
                def func():
                    self.player.gold -= c
                    heal = int(self.player.max_hp * ratio)
                    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                    msg = f"🛌 {label}을 통해 기혈을 회복했습니다."
                    self.add_history(msg)
                    self.inn_notice = msg  # [추가] 화면 표시용

                return func

            self.ui_buttons_next[f"inn_rest_{i}"] = {
                "rect": r,
                "enabled": can_buy,
                "on_click": make_rest(),
            }

            # 버튼 그리기
            color = (60, 40, 40) if can_buy else (30, 30, 30)
            pygame.draw.rect(surf, color, r, border_radius=8)
            pygame.draw.rect(
                surf, COLOR_GOLD if can_buy else COLOR_GRAY, r, 2, border_radius=8
            )

            txt = f"{menu['label']} - {cost}냥"
            if self.player.hp >= self.player.max_hp:
                txt = "기혈 충만"
            t_surf = self.font.render(txt, True, COLOR_WHITE)
            surf.blit(
                t_surf,
                (
                    r.centerx - t_surf.get_width() // 2,
                    r.centery - t_surf.get_height() // 2,
                ),
            )

        # ---------------------------------------------------------
        # [B 구역] 식사 및 반주 (버프) - 우측 상단
        # ---------------------------------------------------------
        surf.blit(self.font.render("[ 식사 및 반주 ]", True, COLOR_GOLD), (750, 140))
        food_menus = [
            {
                "name": "죽엽청",
                "desc": "내공 +2 (시작 시)",
                "cost": 10,
                "type": "energy",
                "val": 2,
            },
            {
                "name": "장육",
                "desc": "최대 체력 +30",
                "cost": 20,
                "type": "hp_max",
                "val": 30,
            },
            {
                "name": "용정차",
                "desc": "매 턴 방어 +3",
                "cost": 10,
                "type": "def_turn",
                "val": 3,
            },
        ]

        for i, food in enumerate(food_menus):
            r = pygame.Rect(700, 180 + i * 70, 400, 60)
            cost = food["cost"]
            is_full = self.player.inn_buff is not None
            can_eat = self.player.gold >= cost and not is_full

            def make_eat(f=food):
                def func():
                    self.player.gold -= f["cost"]
                    self.player.inn_buff = {
                        "type": f["type"],
                        "val": f["val"],
                        "name": f["name"],
                    }
                    msg = f"🍽️ {f['name']}을(를) 맛있게 먹었습니다."
                    self.add_history(msg)
                    self.inn_notice = msg  # [추가] 화면 표시용

                return func

            self.ui_buttons_next[f"inn_food_{i}"] = {
                "rect": r,
                "enabled": can_eat,
                "on_click": make_eat(),
            }

            # 버튼 그리기
            color = (40, 60, 40) if can_eat else (30, 30, 30)
            pygame.draw.rect(surf, color, r, border_radius=8)
            pygame.draw.rect(
                surf, COLOR_GREEN if can_eat else COLOR_GRAY, r, 2, border_radius=8
            )

            txt = f"{food['name']}({cost}냥): {food['desc']}"
            if is_full:
                txt = f"{food['name']} (배부름)"
            t_surf = self.font.render(txt, True, COLOR_WHITE)
            surf.blit(
                t_surf,
                (
                    r.centerx - t_surf.get_width() // 2,
                    r.centery - t_surf.get_height() // 2,
                ),
            )

        # ---------------------------------------------------------
        # [C 구역] 심득(心得): 깨달음을 얻는 시간 (마일스톤 방식)
        # ---------------------------------------------------------
        r_train = pygame.Rect(400, 450, 480, 70)
        next_goal = self.player.get_next_enlightenment_threshold()
        is_qualified = self.player.total_xp >= next_goal
        can_train = is_qualified and len(self.player.deck) > 0

        def do_train():
            import random

            if self.player.deck:
                target = random.choice(self.player.deck)
                target.mastery += 1
                self.player.enlightenment_idx += 1

                scenarios = [
                    f"🕯️ 촛불 아래서 홀로 {target.name} 초식을 복기하다 깊은 이치를 깨달았습니다.",
                    f"🧘 명상하던 중, {target.name}의 막혔던 혈도가 뚫리는 심득을 얻었습니다.",
                    f"🌕 뒷마당에서 {target.name}을(를) 펼치다 마침내 벽을 넘었습니다.",
                    f"🗡️ 밤바람을 맞으며 {target.name}의 진정한 위력에 눈을 떴습니다.",
                ]
                msg = random.choice(scenarios)
                self.add_history(msg)
                self.inn_notice = (
                    msg  # [핵심 추가] 화면에 무공 이름이 포함된 메시지 저장
                )

        self.ui_buttons_next["inn_train"] = {
            "rect": r_train,
            "enabled": can_train,
            "on_click": do_train,
        }

        # 버튼 디자인 및 텍스트 설정
        if can_train:
            bg_col = (50, 40, 80)
            border_col = (150, 100, 255)
            t_msg = f"✨ 심득(心得): 경지를 돌파하다 (공력 {next_goal} 달성)"
        else:
            bg_col = (30, 30, 30)
            border_col = COLOR_GRAY
            t_msg = f"🔒 다음 깨달음까지 정진하십시오. ({self.player.total_xp} / {next_goal})"

        pygame.draw.rect(surf, bg_col, r_train, border_radius=10)
        pygame.draw.rect(surf, border_col, r_train, 2, border_radius=10)

        ts = self.font.render(t_msg, True, COLOR_WHITE)
        surf.blit(
            ts,
            (
                r_train.centerx - ts.get_width() // 2,
                r_train.centery - ts.get_height() // 2,
            ),
        )

        # ---------------------------------------------------------
        # [E 구역] 알림 메시지 출력 (심득 결과 표시용) - [신규]
        # ---------------------------------------------------------
        if hasattr(self, "inn_notice") and self.inn_notice:
            notice_surf = self.font.render(self.inn_notice, True, COLOR_GOLD)
            surf.blit(
                notice_surf, (SCREEN_WIDTH // 2 - notice_surf.get_width() // 2, 410)
            )

        # ---------------------------------------------------------
        # [D 구역] 강호의 소문 (Flavor Text) - 최하단
        # ---------------------------------------------------------
        import time

        rumors = [
            "점소이: '요즘 흑풍채 녀석들이 관길을 막고 행패라더군요.'",
            "손님1: '죽엽청 한 잔이면 호랑이도 때려잡지!'",
            "손님2: '화산파의 매화검법을 본 적 있소? 정말 화려하다던데.'",
            "주모: '외상은 사절입니다. 무림 맹주가 와도 안 돼요.'",
            "떠돌이: '전설에 따르면 이 근처에 기연이 숨겨져 있다오.'",
            f"점소이: '{self.player.name} 대협, 오늘도 안색이 좋아 보이십니다!'",
        ]
        idx = int(time.time() / 5) % len(rumors)
        rumor_surf = self.font_small.render(f"💬 {rumors[idx]}", True, (200, 200, 200))
        surf.blit(rumor_surf, (SCREEN_WIDTH // 2 - rumor_surf.get_width() // 2, 550))

    def _prepare_card_reward(self):
        """전투 후 비급 보상으로 제시할 카드 3장을 무작위 선정합니다."""
        _ui_only = {"기본 공격", "기본 방어", "운기조식"}
        _boss_only = {"nokrim_pado", "cheongeun_chu", "sanak_bung"}
        # 보스 의도 표시용 noop 카드는 플레이어 보상에 등장하지 않음
        _noop_only = {
            "salung_gwon",
            "hwangsan_daecham",
            "cheonak_body",
            "paewang_roar",
            "nokrim_pacheon",
        }
        _exclude = _ui_only | _boss_only | _noop_only
        deck_names = {c.name for c in self.player.deck}
        reward_pool = [
            cid
            for cid in CARD_REGISTRY
            if cid not in deck_names and cid not in _exclude
        ]
        if len(reward_pool) < 3:
            reward_pool = [cid for cid in CARD_REGISTRY if cid not in _exclude]
        choices = random.sample(reward_pool, min(3, len(reward_pool)))
        self.card_reward_choices = [copy.deepcopy(CARD_REGISTRY[c]) for c in choices]

    def _prepare_boss_card_reward(self):
        """보스 처치 후 확정 비급 보상 — 녹림 비급 3종 모두 제시."""
        from content.cards.nokrim import BOSS_NOKRIM_DROP_POOL

        deck_names = {c.name for c in self.player.deck}
        pool = [
            cid
            for cid in BOSS_NOKRIM_DROP_POOL
            if CARD_REGISTRY.get(cid) and CARD_REGISTRY[cid].name not in deck_names
        ]
        # 이미 3개 다 보유 중이면 일반 풀로 폴백
        if not pool:
            self._prepare_card_reward()
            return
        self.card_reward_choices = [copy.deepcopy(CARD_REGISTRY[c]) for c in pool]

    def render_card_reward_to(self, surf):
        """비급 획득 선택 화면"""
        is_boss_reward = (self.last_battle_rewards or {}).get("is_boss", False)
        surf.fill((10, 5, 20))

        if is_boss_reward:
            title = self.font_name.render(
                "💀 녹림왕의 비전 비급!", True, (255, 160, 60)
            )
            surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
            sub = self.font.render(
                "마천광에게서 빼앗은 녹림 비전을 하나 선택합니다", True, (220, 180, 100)
            )
        else:
            title = self.font_name.render("⚡ 비급을 얻었습니다", True, COLOR_GOLD)
            surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
            sub = self.font.render(
                "하나를 선택하여 덱에 추가합니다 (건너뛰기 가능)", True, (180, 180, 180)
            )
        surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 110))

        # 보상 요약
        if self.last_battle_rewards:
            r = self.last_battle_rewards
            reward_line = self.font_small.render(
                f"이번 전투 보상: 공력 +{r['xp']} | 금자 +{r['gold']}  ({r['streak']}연승)",
                True,
                (220, 180, 80) if is_boss_reward else (160, 220, 160),
            )
            surf.blit(
                reward_line, (SCREEN_WIDTH // 2 - reward_line.get_width() // 2, 148)
            )

        type_colors = {
            "공격": (200, 60, 60),
            "방어": (60, 100, 200),
            "기술": (60, 180, 100),
            "약화": (160, 80, 200),
        }
        choices = getattr(self, "card_reward_choices", [])
        card_w, card_h = 340, 200
        total_w = len(choices) * card_w + (len(choices) - 1) * 30
        start_x = SCREEN_WIDTH // 2 - total_w // 2

        for i, card in enumerate(choices):
            rx = start_x + i * (card_w + 30)
            ry = 200
            r = pygame.Rect(rx, ry, card_w, card_h)

            type_str = card.type.value
            bar_col = type_colors.get(type_str, (120, 120, 120))
            pygame.draw.rect(surf, (25, 15, 40), r, border_radius=10)
            pygame.draw.rect(surf, bar_col, r, 2, border_radius=10)
            pygame.draw.rect(
                surf, bar_col, pygame.Rect(rx, ry, 10, card_h), border_radius=5
            )

            name_s = self.font.render(card.name, True, COLOR_WHITE)
            surf.blit(name_s, (rx + 20, ry + 15))

            type_s = self.font_small.render(
                f"[{type_str}]  내공 비용: {card.base_cost}", True, bar_col
            )
            surf.blit(type_s, (rx + 20, ry + 55))

            desc_s = self.font_small.render(card.description, True, (180, 180, 180))
            surf.blit(desc_s, (rx + 20, ry + 85))

            val_s = self.font_small.render(
                f"기본 위력: {card.base_value}", True, (200, 200, 120)
            )
            surf.blit(val_s, (rx + 20, ry + 115))

            pick_btn = pygame.Rect(rx + 20, ry + 148, card_w - 40, 40)
            self.ui_buttons_next[f"pick_card_{i}"] = {
                "rect": pick_btn,
                "enabled": True,
                "on_click": lambda c=card: self._pick_card_reward(c),
            }
            pygame.draw.rect(surf, (50, 35, 80), pick_btn, border_radius=6)
            pygame.draw.rect(surf, (150, 100, 220), pick_btn, 1, border_radius=6)
            pick_s = self.font_small.render("이 비급을 취한다", True, COLOR_WHITE)
            surf.blit(
                pick_s,
                (
                    pick_btn.centerx - pick_s.get_width() // 2,
                    pick_btn.centery - pick_s.get_height() // 2,
                ),
            )

        # 건너뛰기 버튼
        skip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 440, 240, 50)

        def _skip_reward():
            self.card_reward_choices = []
            if self.current_node_graph:
                self._back_to_region_map()
            else:
                self.phase = Phase.VICTORY_PANEL

        self.ui_buttons_next["skip_reward"] = {
            "rect": skip_rect,
            "enabled": True,
            "on_click": _skip_reward,
        }
        pygame.draw.rect(surf, (40, 40, 40), skip_rect, border_radius=8)
        pygame.draw.rect(surf, COLOR_GRAY, skip_rect, 1, border_radius=8)
        skip_s = self.font.render("건너뛰기", True, COLOR_GRAY)
        surf.blit(
            skip_s,
            (
                skip_rect.centerx - skip_s.get_width() // 2,
                skip_rect.centery - skip_s.get_height() // 2,
            ),
        )

    def _pick_card_reward(self, card):
        """선택한 카드를 덱에 추가하고 승리 패널 또는 REGION_MAP으로 이동"""
        self.player.deck.append(card)
        self.add_history(f"비급 획득: {card.name}")
        self.card_reward_choices = []  # 소비 완료
        if self.current_node_graph:
            self._back_to_region_map()
        else:
            self.phase = Phase.VICTORY_PANEL

    def render_deck_to(self, surf):
        """[신규] 비급고 정비 화면 - 보유 비급(카드) 열람 및 연마"""
        surf.fill((15, 10, 25))

        surf.blit(
            self.font_name.render("비급고 정비", True, (180, 140, 255)), (500, 40)
        )
        surf.blit(
            self.font.render(f"보유 공력(XP): {self.player.xp}", True, COLOR_GOLD),
            (500, 90),
        )

        type_colors = {
            "공격": (200, 60, 60),
            "방어": (60, 100, 200),
            "기술": (60, 180, 100),
            "약화": (160, 80, 200),
        }

        cols = 2
        card_w, card_h = 520, 100
        pad_x, pad_y = 60, 140
        gap_x, gap_y = 560, 110

        for i, card in enumerate(self.player.deck):
            col = i % cols
            row = i // cols
            rx = pad_x + col * gap_x
            ry = pad_y + row * gap_y

            r = pygame.Rect(rx, ry, card_w, card_h)
            cost = card.get_upgrade_cost()
            can_up = self.player.xp >= cost and card.mastery < card.mastery_max
            maxed = card.mastery >= card.mastery_max

            bg_color = (30, 20, 50) if not maxed else (20, 40, 20)
            border_color = (
                (120, 80, 200) if can_up else ((80, 150, 80) if maxed else (60, 60, 80))
            )

            pygame.draw.rect(surf, bg_color, r, border_radius=8)
            pygame.draw.rect(surf, border_color, r, 2, border_radius=8)

            # 카드 타입 컬러 바
            type_str = card.type.value
            bar_color = type_colors.get(type_str, (120, 120, 120))
            pygame.draw.rect(
                surf, bar_color, pygame.Rect(rx, ry, 8, card_h), border_radius=4
            )

            # 성(★) 표시
            stars = "★" * card.mastery + "☆" * (card.mastery_max - card.mastery)
            name_txt = self.font.render(f"{card.name}  {stars}", True, COLOR_WHITE)
            surf.blit(name_txt, (rx + 20, ry + 12))

            # 설명 및 현재 위력
            cur_val = card.get_current_value()
            desc_txt = self.font_small.render(
                f"[{type_str}] {card.description}  |  현재 위력: {cur_val}  |  내공: {card.base_cost}",
                True,
                (180, 180, 180),
            )
            surf.blit(desc_txt, (rx + 20, ry + 48))

            # 연마 버튼 or 상태
            if maxed:
                up_label = self.font_small.render("최고 경지", True, (100, 220, 100))
                surf.blit(up_label, (rx + card_w - 100, ry + 38))
            else:
                up_btn = pygame.Rect(rx + card_w - 130, ry + 28, 120, 40)
                self.ui_buttons_next[f"deck_up_{card.name}"] = {
                    "rect": up_btn,
                    "enabled": can_up,
                    "on_click": lambda c=card, p=cost: [
                        setattr(self.player, "xp", self.player.xp - p),
                        c.upgrade(),
                    ],
                }
                pygame.draw.rect(
                    surf,
                    (60, 40, 100) if can_up else (30, 30, 30),
                    up_btn,
                    border_radius=6,
                )
                pygame.draw.rect(
                    surf,
                    (140, 100, 200) if can_up else (60, 60, 60),
                    up_btn,
                    1,
                    border_radius=6,
                )
                cost_label = self.font_small.render(
                    f"연마 XP {cost}", True, COLOR_GOLD if can_up else COLOR_GRAY
                )
                surf.blit(
                    cost_label,
                    (
                        up_btn.x + up_btn.width // 2 - cost_label.get_width() // 2,
                        up_btn.y + 12,
                    ),
                )

    def render_world_to(self, surf):
        surf.blit(self.font_name.render("강호 대지", True, COLOR_WHITE), (530, 80))
        configs = [
            ("북쪽 출도", 100, COLOR_RED, lambda: self._enter_region("north")),
            ("객잔", 350, COLOR_GREEN, lambda: setattr(self, "phase", Phase.INN)),
            ("연무장", 600, COLOR_BLUE, lambda: setattr(self, "phase", Phase.TRAINING)),
            ("비급고", 850, (80, 60, 130), lambda: setattr(self, "phase", Phase.DECK)),
            # [신규] 월드맵 화면 우측 하단에 '저장' 버튼 추가
            ("기록 저장", 1000, COLOR_GOLD, self.save_current_game),
        ]
        for txt, x, col, cmd in configs:
            r = pygame.Rect(
                x,
                200 if txt != "기록 저장" else 600,
                200,
                100 if txt != "기록 저장" else 60,
            )
            self.ui_buttons_next[f"world_{txt}"] = {
                "rect": r,
                "enabled": True,
                "on_click": cmd,
            }
            pygame.draw.rect(surf, col, r, border_radius=10)
            surf.blit(
                self.font.render(txt, True, COLOR_WHITE),
                (r.x + 40, r.y + 35 if txt != "기록 저장" else r.y + 20),
            )

        surf.blit(
            self.font.render(
                f"금자: {self.player.gold} | XP: {self.player.xp} | HP: {self.player.hp}/{self.player.max_hp}",
                True,
                COLOR_GOLD,
            ),
            (100, 100),
        )

    def render_victory_to(self, surf):
        title = self.font_name.render("🎊 비무 승리! 🎊", True, COLOR_GOLD)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        if self.last_battle_rewards:
            r = self.last_battle_rewards
            txt = f"획득: XP +{r['xp']} | 금자 +{r['gold']} ({r['streak']}연승)"
            surf.blit(
                self.font.render(txt, True, COLOR_WHITE), (SCREEN_WIDTH // 2 - 150, 280)
            )

        r_yulang = pygame.Rect(SCREEN_WIDTH // 2 - 260, 500, 240, 60)
        self.ui_buttons_next["yulang"] = {
            "rect": r_yulang,
            "enabled": True,
            "on_click": self._after_battle_continue,
        }
        pygame.draw.rect(surf, (34, 139, 34), r_yulang, border_radius=10)
        surf.blit(
            self.font.render("강호 유랑", True, COLOR_WHITE),
            (r_yulang.x + 70, r_yulang.y + 20),
        )

        r_back = pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 240, 60)
        self.ui_buttons_next["back_world"] = {
            "rect": r_back,
            "enabled": True,
            "on_click": lambda: setattr(self, "phase", Phase.WORLD),
        }
        pygame.draw.rect(surf, COLOR_GRAY, r_back, border_radius=10)
        surf.blit(
            self.font.render("강호 대지로", True, COLOR_WHITE),
            (r_back.x + 60, r_back.y + 20),
        )

    def process_victory(self, set_phase=True):
        is_boss = (
            getattr(self.enemy, "is_boss", False)
            or getattr(self.enemy, "_cycle", None) is not None
        )

        if is_boss:
            # ── 보스 처치 보상 ──
            jajil_bonus = 1.0 + (self.player.stats["자질"] - 10) * 0.03
            xp = int((150 + random.randint(-20, 30)) * jajil_bonus)
            gold_gain = 80 + random.randint(0, 20)
        else:
            # ── 일반 처치 보상 ──
            level_gap = max(0, self.enemy.level - self.encounter)
            jajil_bonus = 1.0 + (self.player.stats["자질"] - 10) * 0.03
            xp = int(
                (20 + random.randint(0, 10))
                * (1.0 + level_gap * 0.15)
                * (1.0 + min(1.0, self.player.win_streak * 0.1))
                * jajil_bonus
            )
            gold_gain = 10 + random.randint(0, 5)

        self.player.xp += xp
        self.player.total_xp += xp

        self.player.gold += gold_gain

        if (
            not is_boss
            and self.encounter % 5 == 0
            and random.random() < 0.2
            and self.player.deck
        ):
            random.choice(self.player.deck).upgrade()

        self.last_battle_rewards = {
            "xp": xp,
            "gold": gold_gain,
            "streak": self.player.win_streak,
            "is_boss": is_boss,
        }

        self.player.win_streak += 1

        # 보스: 항상 비급 보상 (보스 전용 드랍 풀)
        if is_boss:
            self._prepare_boss_card_reward()
            if set_phase:
                self.phase = Phase.CARD_REWARD
        # 일반: 3번마다 비급 보상
        elif self.encounter % 3 == 0:
            self._prepare_card_reward()
            if set_phase:
                self.phase = Phase.CARD_REWARD
        elif set_phase:
            self.phase = Phase.VICTORY_PANEL

    def render_victory_finish_to(self, surf):
        surf.fill(COLOR_DARK_GRAY)

        title = self.font_name.render("⚔️ 결투의 끝, 고요", True, COLOR_GOLD)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        # 서사 2줄
        lines = getattr(self, "victory_story_lines", [])
        y = 240
        for line in lines[:3]:
            s = self.font.render(line, True, COLOR_WHITE)
            surf.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
            y += 35

        # 보상 1줄
        if self.last_battle_rewards:
            r = self.last_battle_rewards
            reward_txt = f"전리품: 공력(XP) +{r['xp']} | 금자 +{r['gold']}  ({r['streak']}연승의 기세)"
            rs = self.font.render(reward_txt, True, (220, 220, 220))
            surf.blit(rs, (SCREEN_WIDTH // 2 - rs.get_width() // 2, y + 20))

        # 버튼
        r_yulang = pygame.Rect(SCREEN_WIDTH // 2 - 260, 520, 240, 60)
        self.ui_buttons_next["yulang"] = {
            "rect": r_yulang,
            "enabled": True,
            "on_click": self._after_battle_continue,
        }
        pygame.draw.rect(surf, (34, 139, 34), r_yulang, border_radius=10)
        surf.blit(
            self.font.render("강호 유랑", True, COLOR_WHITE),
            (r_yulang.x + 70, r_yulang.y + 20),
        )

        r_back = pygame.Rect(SCREEN_WIDTH // 2 + 20, 520, 240, 60)
        self.ui_buttons_next["back_world"] = {
            "rect": r_back,
            "enabled": True,
            "on_click": lambda: setattr(self, "phase", Phase.WORLD),
        }
        pygame.draw.rect(surf, COLOR_GRAY, r_back, border_radius=10)
        surf.blit(
            self.font.render("강호 대지로", True, COLOR_WHITE),
            (r_back.x + 60, r_back.y + 20),
        )

    def draw_mini_card(self, surf, card, rect, is_finished=False):
        """슬롯에 배치된 카드를 렌더링하며 실제 적용 수치를 크게 표시합니다."""
        is_animating = self.clash_anim.get("active", False)
        idle_offset = (
            math.sin(pygame.time.get_ticks() * 0.005) * 3 if is_animating else 0
        )

        draw_rect = rect.copy()
        if not is_finished:
            draw_rect.y += idle_offset
        if self.screen_shake > 0 and not is_finished:
            draw_rect.x += random.randint(-2, 2)

        # 타입별 배경색
        type_bg = {
            "공격": (140, 30, 30),
            "방어": (25, 80, 30),
            "기술": (30, 30, 130),
            "약화": (100, 30, 110),
        }
        type_border = {
            "공격": (220, 80, 80),
            "방어": (80, 200, 100),
            "기술": (80, 120, 230),
            "약화": (180, 80, 200),
        }
        t = card.type.value
        bg = type_bg.get(t, (50, 50, 50))
        border = type_border.get(t, (150, 150, 150))

        pygame.draw.rect(surf, bg, draw_rect, border_radius=6)
        pygame.draw.rect(surf, border, draw_rect, 2, border_radius=6)

        # 카드 이름 (상단, 짧게)
        name_surf = self.font_small.render(card.name[:4], True, COLOR_WHITE)
        surf.blit(name_surf, (draw_rect.x + 5, draw_rect.y + 5))

        # ── 실제 적용 수치 계산 ──
        scaled = card.get_current_value()
        if t == "공격":
            val_str = f"💥 {scaled}"
            val_color = (255, 160, 160)
        elif t == "방어":
            val_str = f"🛡 {scaled}~{scaled + 4}"
            val_color = (120, 220, 160)
        elif card.name in ("삼재공", "운기조식"):
            bonus = 1 + (card.mastery // 3) if card.name == "삼재공" else 2
            val_str = f"⚡+{bonus}"
            val_color = (160, 200, 255)
        elif t == "약화":
            val_str = f"↓ATK {scaled}"
            val_color = (200, 140, 255)
        else:
            val_str = f"+{scaled}"
            val_color = (200, 200, 200)

        # 수치를 카드 중앙에 크게 표시
        val_surf = self.font.render(val_str, True, val_color)
        surf.blit(
            val_surf,
            (
                draw_rect.centerx - val_surf.get_width() // 2,
                draw_rect.centery - val_surf.get_height() // 2 + 8,
            ),
        )

        # 내공 비용 (우하단 작게)
        cost_surf = self.font_small.render(f"氣{card.base_cost}", True, (200, 200, 100))
        surf.blit(
            cost_surf,
            (draw_rect.right - cost_surf.get_width() - 5, draw_rect.bottom - 20),
        )

        if is_finished:
            overlay = pygame.Surface(
                (draw_rect.width, draw_rect.height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            surf.blit(overlay, (draw_rect.x, draw_rect.y))

    def draw_intent_icon_to(self, surf, intent, center_pos):
        """
        적의 의도 슬롯을 무협 원형 아이콘 스타일로 렌더링합니다.
        슬롯 테두리(바깥 rect)는 호출부에서 그리고, 이 함수는 내부만 담당합니다.
        """
        is_animating = self.clash_anim.get("active", False)
        pulse = int(math.sin(pygame.time.get_ticks() * 0.01) * 3) if is_animating else 0
        shake_x = random.randint(-1, 1) if "공격" in intent and is_animating else 0

        # 타입 분류 (accent 색상 결정용)
        ATK_INTENTS = {"살웅 괴력권", "황산 대참", "녹림 파천참", "기본 공격"}
        DEF_INTENTS = {"천악 부동체", "기본 방어"}
        HEAL_INTENTS = {"운기 조식"}
        if intent in ATK_INTENTS:
            type_str = "공격"
            accent = (200, 60, 60)
            bg_dark = (60, 15, 15)
        elif intent in DEF_INTENTS:
            type_str = "방어"
            accent = (60, 160, 60)
            bg_dark = (15, 40, 15)
        elif intent in HEAL_INTENTS:
            type_str = "회복"
            accent = (60, 180, 180)
            bg_dark = (10, 40, 40)
        else:
            type_str = "기세"
            accent = (80, 80, 200)
            bg_dark = (15, 15, 55)

        # 슬롯 내부 배경 (직사각형)
        w, h = 100, 130
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (center_pos[0] + shake_x, center_pos[1] + pulse)
        pygame.draw.rect(surf, bg_dark, rect, border_radius=5)

        # 원형 아이콘 (슬롯 상단 3/5 영역)
        icon_r = 32
        icon_cx = rect.centerx
        icon_cy = rect.y + icon_r + 8
        draw_card_art_icon(surf, intent, type_str, icon_cx, icon_cy, icon_r, accent)

        # 무공명 (하단 텍스트)
        name_short = intent if len(intent) <= 5 else intent[:5]
        name_txt = self.font_small.render(name_short, True, (230, 220, 180))
        surf.blit(
            name_txt,
            name_txt.get_rect(centerx=rect.centerx, y=rect.y + icon_r * 2 + 16),
        )

        # 타입 라벨 (최하단)
        type_txt = self.font_small.render(f"[{type_str}]", True, accent)
        surf.blit(
            type_txt, type_txt.get_rect(centerx=rect.centerx, bottom=rect.bottom - 6)
        )

    def render_player_hand_to(self, surf):
        self.card_rects = []
        c_w, c_h, gap = 140, 190, 15
        total_w = len(self.player.hand) * (c_w + gap) - gap
        start_x, y = (surf.get_width() - total_w) // 2, surf.get_height() - c_h - 40
        for i, card in enumerate(self.player.hand):
            rect = pygame.Rect(start_x + i * (c_w + gap), y, c_w, c_h)
            draw_card_advanced(surf, rect.x, rect.y, card, self.font)
            if card.base_cost > self.current_rem_energy:
                overlay = pygame.Surface((c_w, c_h), pygame.SRCALPHA)
                overlay.fill((60, 0, 0, 160))
                surf.blit(overlay, (rect.x, rect.y))
            self.card_rects.append(rect)

    def render_basic_technique_panel(self, surf):
        """[수선] 버튼 겹침 방지를 위해 시작 y좌표를 450에서 400으로 상향 조정했습니다."""
        # [수정] start_y를 450에서 400으로 변경하여 위쪽으로 패널을 이동
        start_x, start_y, btn_w, btn_h = 1050, 440, 100, 32
        basics = [
            ("기본 공격", COLOR_RED),
            ("기본 방어", COLOR_GREEN),
            ("운기조식", COLOR_BLUE),
        ]
        for i, (name, col) in enumerate(basics):
            r = pygame.Rect(start_x, start_y + i * 40, btn_w, btn_h)
            self.ui_buttons_next[f"basic_{i}"] = {
                "rect": r,
                "enabled": True,
                "on_click": lambda n=name: self.add_basic_card_to_slot(n),
            }
            pygame.draw.rect(surf, (30, 30, 30), r, border_radius=4)
            pygame.draw.rect(surf, col, r, 1, border_radius=4)
            txt = self.font_small.render(name, True, COLOR_WHITE)
            surf.blit(
                txt,
                (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2),
            )

    def render(self):
        try:
            self.ui_buttons_next = {}
            render_offset = [0, 0]
            if self.screen_shake > 0:
                render_offset = [
                    random.randint(-SCREEN_SHAKE_POWER, SCREEN_SHAKE_POWER),
                    random.randint(-SCREEN_SHAKE_POWER, SCREEN_SHAKE_POWER),
                ]
                self.screen_shake -= 1
            self.temp_surf.fill(COLOR_DARK_GRAY)
            self.draw_to_surface(self.temp_surf)
            self.screen.fill(COLOR_BLACK)
            self.screen.blit(self.temp_surf, render_offset)
            if self.flash_alpha > 0:
                self.flash_surf.fill(self.flash_color)
                self.flash_surf.set_alpha(self.flash_alpha)
                self.screen.blit(self.flash_surf, (0, 0))
                self.flash_alpha -= 50
            self.ui_buttons_active = self.ui_buttons_next
            pygame.display.flip()
        except (
            Exception
        ):  # [수정] bare except 대신 Exception을 명시하여 사관의 지적을 해결했습니다.
            print(traceback.format_exc())

    def draw_to_surface(self, surf):
        """[수선] 모든 페이즈 체크 시 PhaseExt 이름을 사용하도록 교정했습니다."""
        # [수정] Phase_Ext를 PhaseExt로 변경
        if self.phase == PhaseExt.LOGIN:  # [신규] 로그인 화면 연결
            self.render_login_to(surf)
        elif self.phase == Phase.WORLD:
            self.render_world_to(surf)
        elif self.phase in [Phase.PLAYER_TURN, Phase.ENEMY_TURN]:
            self.render_battle_screen_to(surf)
            self.draw_clash_particles(surf)
        elif self.phase == Phase.TRAINING:
            self.render_training_to(surf)
        elif self.phase == Phase.VICTORY_PANEL:
            self.render_victory_to(surf)
        elif self.phase == Phase.GAMEOVER:
            self.render_death_scene_to(surf)
        elif self.phase == Phase.INN:
            # [교정] 명상 대신 새롭게 만든 객잔(Inn)를 호출합니다.
            self.render_inn_to(surf)
        elif self.phase == Phase.VICTORY_FINISH:
            self.render_victory_finish_to(surf)
        elif self.phase == Phase.DECK:
            self.render_deck_to(surf)
        elif self.phase == Phase.CARD_REWARD:
            self.render_card_reward_to(surf)
        elif self.phase == Phase.REGION_MAP:
            self.render_region_map_to(surf)
        # 연무장, 객잔, 비급고 하단에 배치되는 공통 '강호 귀환' 버튼
        if self.phase in [Phase.TRAINING, Phase.INN, Phase.DECK]:
            r = pygame.Rect(500, 650, 200, 60)
            _back_cmd = (
                self._back_to_region_map
                if self.current_node_graph
                else (lambda: setattr(self, "phase", Phase.WORLD))
            )
            self.ui_buttons_next["back"] = {
                "rect": r,
                "enabled": True,
                "on_click": _back_cmd,
            }
            pygame.draw.rect(surf, COLOR_GRAY, r, border_radius=10)
            pygame.draw.rect(surf, COLOR_WHITE, r, 2, border_radius=10)
            txt = self.font.render("강호 귀환", True, COLOR_WHITE)
            surf.blit(
                txt,
                (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2),
            )

    def run(self):
        """[수선] 가상 기혈이 실제 기혈을 부드럽게 추격하는 로직을 추가했습니다."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_input(event)

            # [신규] 부드러운 기혈 감소 로직 (0.1 속도로 실제 기혈을 추격)
            if self.player:
                if self.player_visual_hp == 0:
                    self.player_visual_hp = self.player.hp
                self.player_visual_hp -= (self.player_visual_hp - self.player.hp) * 0.1

            if hasattr(self, "enemy") and self.enemy:
                if self.enemy_visual_hp == 0:
                    self.enemy_visual_hp = self.enemy.hp
                self.enemy_visual_hp -= (self.enemy_visual_hp - self.enemy.hp) * 0.1

            if self.clash_anim["active"] and not getattr(
                self, "victory_overlay", False
            ):
                self.update_clash_animation()

            if (
                self.phase == Phase.PLAYER_TURN
                and hasattr(self, "enemy")
                and self.enemy.hp <= 0
            ):
                self.process_victory()
            self.render()
            self.clock.tick(FPS)

    def render_death_scene_to(self, surf):
        surf.fill((30, 10, 10))
        title = self.font_name.render(
            "무인의 마지막 기록: 죽음(死亡)", True, COLOR_WHITE
        )
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
        for i, line in enumerate(self.death_novel):
            l_surf = self.font_novel.render(line, True, (230, 200, 200))
            surf.blit(
                l_surf, (SCREEN_WIDTH // 2 - l_surf.get_width() // 2, 220 + i * 45)
            )
        r = pygame.Rect(SCREEN_WIDTH // 2 - 100, 580, 200, 70)
        self.ui_buttons_next["resurrection"] = {
            "rect": r,
            "enabled": True,
            "on_click": self.resurrect_player,
        }
        pygame.draw.rect(surf, (60, 20, 20), r, border_radius=10)
        txt = self.font.render("다시 태어나기", True, COLOR_WHITE)
        surf.blit(
            txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2)
        )

    def resurrect_player(self):
        """[수선] 죽음 이후, 이름과 '기초 스탯'을 계승하여 다시 시작합니다."""
        # 1. 전생의 스탯과 이름 기억하기
        old_stats = self.player.stats.copy()
        old_name = self.player.name

        # 2. 새로운 몸(객체) 생성
        self.player = Player(old_name)

        # 3. 기억해둔 스탯 덮어씌우기 (계승)
        self.player.stats = old_stats

        # 4. 스탯에 맞춰 최대 체력/내공 재계산
        self.player.recalculate_stats()
        self.player.hp = self.player.max_hp  # 체력 100%로 부활
        self.player.energy = self.player.max_energy

        # 5. 덱과 진행도 초기화 (스탯만 남기고 나머진 리셋)
        self.player.initialize_deck(CARD_REGISTRY)
        self.chapter, self.encounter = 1, 1
        self.run_history = []
        self.add_history(f"{self.player.name}, 죽음을 넘어 다시 강호에 서다.")

        # 6. 월드맵으로 이동
        self.phase = Phase.WORLD

        # (선택) 부활 직후 자동 저장
        self.save_current_game()


if __name__ == "__main__":
    GuunrokGame().run()
