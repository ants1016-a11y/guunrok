import random
from infra.config import CRIT_MULTIPLIER


class BattleManager:
    def __init__(self, player, enemy, game_instance):
        self.player = player
        self.enemy = enemy
        self.game_instance = game_instance
        self.cards_played_this_turn = 0

    def prepare_enemy_intents(self):
        """
        [수선] 적의 5합 의도를 준비합니다.
        보스급 적(refresh_intents 메서드 보유)은 자신의 독문무공을 사용하고,
        일반 산적은 강공이 제외된 기본 풀을 사용하도록 분기 처리했습니다.
        """
        # 1. 보스급 적이 스스로 의도를 생성할 줄 안다면 그 로직을 존중함
        if hasattr(self.enemy, "refresh_intents"):
            self.enemy.refresh_intents()
            self.cards_played_this_turn = 0
            return

        # 2. 일반 적들을 위한 기본 무공 풀 관리
        self.enemy.intent_queue.clear()
        pool = ["공격", "방어", "강공", "공격", "약화"]

        # 산적 계열은 강공을 구사하지 못하도록 필터링
        if "산적" in self.enemy.name:
            pool = [act for act in pool if act != "강공"]
            while len(pool) < 5:
                pool.append("공격")

        random.shuffle(pool)

        # 의도 큐 채우기
        for i in range(5):
            self.enemy.intent_queue.append(pool[i % len(pool)])

        self.cards_played_this_turn = 0

    def resolve_single_clash(self, card, enemy_intent):
        """[서사 확장] 무협지 톤으로 '전개-응수-파쇄-결말'을 한 문단처럼 기록합니다."""
        # --- 전투 전 상태 스냅샷 ---
        p_hp_before = self.player.hp
        e_hp_before = self.enemy.hp
        p_def_before = self.player.defense
        e_def_before = getattr(self.enemy, "defense", 0)

        p_card_name = "무방비"
        is_p_crit = False

        # 1) 나의 초식 전개
        if card:
            p_card_name = card.name
            current_mastery_val = card.get_current_value()
            is_p_crit = self.game_instance.calculate_crit(card.type.value)

            orig_base = card.base_value
            card.base_value = (
                int(current_mastery_val * CRIT_MULTIPLIER)
                if is_p_crit
                else current_mastery_val
            )

            card.effect_func(self.player, self.enemy, card)
            card.base_value = orig_base

        # 2) 적의 초식 응수
        dmg_dealt, def_gained, e_msg = self.enemy.execute_single_intent(
            enemy_intent, self.player
        )

        # --- 전투 후 변화량 산출 ---
        p_hp_loss = p_hp_before - self.player.hp
        e_hp_loss = e_hp_before - self.enemy.hp

        p_def_after = self.player.defense
        e_def_after = getattr(self.enemy, "defense", 0)

        # 방어 변화량(나의 방어 상승)
        p_def_gain = p_def_after - p_def_before

        # 호신강기 소모(=막아낸 양으로 해석 가능)
        e_def_loss = max(0, e_def_before - e_def_after)
        p_def_loss = max(0, p_def_before - p_def_after)

        # 이번 합의 "총 위력"을 서사에 쓰기 좋게 재구성
        my_total_force = e_def_loss + e_hp_loss
        enemy_total_force = p_def_loss + p_hp_loss

        # --- 무협 서사 로그 구성 ---
        res_data = []

        # (A) 전개 / 선언
        if card:
            if is_p_crit:
                res_data.append(
                    (f"🔥 나: 「{p_card_name}」를 벼락같이 펼친다.", (255, 215, 0))
                )
            else:
                res_data.append(
                    (
                        f"✨ 나: 「{p_card_name}」의 식을 밟아 기운을 몰아친다.",
                        (255, 215, 0),
                    )
                )
        else:
            res_data.append(
                (
                    "💨 나: 한 박자 늦었다… 빈틈을 보이며 자세를 흐트러뜨린다.",
                    (180, 180, 180),
                )
            )

        # (B) 적의 응수(기술명 맛 살리기)
        if enemy_intent in ["공격", "강공", "방어", "약화"]:
            intent_name_map = {
                "공격": "혈풍참",
                "강공": "패왕쇄",
                "방어": "철벽진",
                "약화": "탁기난류",
            }
            enemy_style = intent_name_map.get(enemy_intent, enemy_intent)
            res_data.append(
                (
                    f"👹 {self.enemy.name}: 「{enemy_style}」로 맞받아친다.",
                    (255, 80, 80),
                )
            )
        else:
            res_data.append(
                (
                    f"👹 {self.enemy.name}: 「{enemy_intent}」의 기세로 맞선다!",
                    (255, 80, 80),
                )
            )

        # (C) 내가 준 피해를 '서사 한 문장'으로 정리 (네가 원하던 스타일)
        # 예: "복부를 공격해 5를 줬다. 적은 혈풍참으로 막아 2만 입었다" 같은 느낌
        if my_total_force > 0:
            if e_def_loss > 0 and e_hp_loss > 0:
                # 호신강기로 일부 막고 일부는 기혈로 관통
                res_data.append(
                    (
                        f"🗡️ 내 공세가 {self.enemy.name}의 호신강기를 {e_def_loss}만큼 깎아내고, "
                        f"남은 기운 {e_hp_loss}가 기혈을 파고든다. (총 위력 {my_total_force})",
                        (255, 215, 0),
                    )
                )
            elif e_def_loss > 0 and e_hp_loss == 0:
                res_data.append(
                    (
                        f"🛡️ {self.enemy.name}이(가) 호신강기로 받아냈다. "
                        f"공세 {my_total_force}는 고스란히 강기만 {e_def_loss} 깎아낸다.",
                        (200, 200, 200),
                    )
                )
            elif e_hp_loss > 0:
                res_data.append(
                    (
                        f"🗡️ 막을 틈을 주지 않았다. {self.enemy.name}의 기혈이 {e_hp_loss} 흔들린다. "
                        f"(총 위력 {my_total_force})",
                        (255, 215, 0),
                    )
                )

        # (D) 내가 받은 피해도 같은 방식으로 '무협 문장'으로 정리
        if enemy_total_force > 0:
            if p_def_loss > 0 and p_hp_loss > 0:
                res_data.append(
                    (
                        f"🩸 {self.enemy.name}의 공세가 내 호신강기를 {p_def_loss} 갈아내고, "
                        f"남은 힘 {p_hp_loss}가 기혈에 스민다. ({e_msg})",
                        (255, 80, 80),
                    )
                )
            elif p_def_loss > 0 and p_hp_loss == 0:
                res_data.append(
                    (
                        f"🛡️ 나는 호신강기로 받아냈다. 강기만 {p_def_loss} 소모된다. ({e_msg})",
                        (200, 200, 200),
                    )
                )
            elif p_hp_loss > 0:
                res_data.append(
                    (
                        f"🩸 막지 못했다. 기혈이 {p_hp_loss}나 흔들린다. ({e_msg})",
                        (255, 80, 80),
                    )
                )

        # (E) 방어 상승(내가 방어 올린 경우)도 문장 톤 유지
        if p_def_gain > 0:
            res_data.append(
                (
                    f"🛡️ 나는 기운을 거두어 호신강기를 다시 다진다. (호신강기 +{p_def_gain})",
                    (100, 150, 255),
                )
            )

        # (F) '결산' 대신, 무협지처럼 짧은 마무리 한 줄 (시스템 느낌 제거)
        # 숫자를 남기되, '결산/요약' 단어를 쓰지 않는다.
        res_data.append(
            (
                f"…숨을 삼킨다. 나의 기혈 {self.player.hp}/{self.player.max_hp}, "
                f"{self.enemy.name}의 기혈 {self.enemy.hp}/{self.enemy.max_hp}.",
                (240, 240, 240),
            )
        )

        return res_data

    def execute_enemy_turn(self):
        """[교정] 정산 로직만 남기고 렌더링 호출을 제거했습니다."""
        logs = []
        self.enemy.defense = 0
        while self.enemy.intent_queue:
            action = self.enemy.intent_queue.popleft()
            if action == "공격":
                actual = self.player.take_damage(self.enemy.atk)
                logs.append(f"◈ 적의 공격! {actual}의 피해!")
            elif action == "강공":
                actual = self.player.take_damage(int(self.enemy.atk * 1.5))
                logs.append(f"◈ 적의 강공! {actual}의 무거운 피해!")
            elif action == "방어":
                added_def = 5 + (self.enemy.level * 2)
                self.enemy.defense += added_def
                logs.append(f"◈ 적이 방어도를 {added_def}만큼 쌓았습니다.")
        return logs
