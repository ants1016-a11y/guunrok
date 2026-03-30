"use client";

import React, {
  createContext,
  useContext,
  useReducer,
  ReactNode,
  Dispatch,
} from "react";
import {
  Player,
  Enemy,
  BattleLog,
  GamePhase,
  Card,
  EnemyIntent,
  getChapter,
} from "@/lib/types";
import { createPlayer, startBattle, drawCards, startTurnRegen, applyClashRegen, recalculateStats } from "@/lib/player";
import { createEnemy, refreshIntents, executeEnemyIntent } from "@/lib/enemies";
import { executeCardEffect, BASIC_ACTIONS } from "@/lib/cards";

// ─── State ──────────────────────────────────────────────────
export interface GameState {
  phase: GamePhase;
  player: Player | null;
  enemy: Enemy | null;
  encounter: number;
  clashIndex: number; // 현재 합 번호 (0~4)
  battleLogs: BattleLog[];
  lastMessage: string;
  playerName: string;
  deathCount: number;
  lastUsedCard: string;
}

const initialState: GameState = {
  phase: "title",
  player: null,
  enemy: null,
  encounter: 0,
  clashIndex: 0,
  battleLogs: [],
  lastMessage: "",
  playerName: "",
  deathCount: 0,
  lastUsedCard: "",
};

// ─── Actions ────────────────────────────────────────────────
type Action =
  | { type: "START_GAME"; name: string; inheritedMastery: number }
  | { type: "START_ENCOUNTER" }
  | { type: "PLAY_CARD"; card: Card }
  | { type: "USE_BASIC"; card: Card }
  | { type: "END_TURN" }
  | { type: "NEXT_CLASH" }
  | { type: "FINISH_ENEMY_TURN" }
  | { type: "CONTINUE_AFTER_VICTORY" }
  | { type: "RESTART" }
  | { type: "GO_TO_WORLD" }
  | { type: "RESURRECT" };

// ─── Reducer ────────────────────────────────────────────────
function gameReducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "START_GAME": {
      const player = createPlayer(action.name);
      // 계승 적용: 이전 생의 깨달음으로 기본 카드 성취도 상승
      if (action.inheritedMastery > 0) {
        player.deck = player.deck.map((c) => ({
          ...c,
          mastery: Math.min(c.masteryMax, c.mastery + action.inheritedMastery),
        }));
      }
      return {
        ...state,
        phase: "world",
        player,
        playerName: action.name,
        encounter: 0,
        battleLogs: [],
        lastMessage: action.inheritedMastery > 0
          ? "육체는 잊었으나, 영혼에 새겨진 검로는 기억한다."
          : "강호에 발을 딛다...",
      };
    }

    case "START_ENCOUNTER": {
      if (!state.player) return state;
      const enc = state.encounter + 1;
      const enemy = refreshIntents(createEnemy(enc));
      const player = startBattle(state.player);
      return {
        ...state,
        phase: "battle_player_turn",
        player,
        enemy,
        encounter: enc,
        clashIndex: 0,
        battleLogs: [
          {
            text: `${enemy.name}이(가) 앞을 막아선다!`,
            color: "text-red-400",
          },
        ],
        lastMessage: "",
      };
    }

    case "PLAY_CARD": {
      if (!state.player || !state.enemy) return state;
      const card = action.card;

      // 내공 부족 체크
      if (state.player.energy < card.cost) {
        return {
          ...state,
          lastMessage: "내공이 부족합니다!",
        };
      }

      // 카드 사용
      const isCrit = Math.random() < 0.15;
      const playerAfterCost = {
        ...state.player,
        energy: state.player.energy - card.cost,
      };

      const { player: pAfter, enemy: eAfter, message } = executeCardEffect(
        card.name,
        playerAfterCost,
        state.enemy,
        card,
        isCrit
      );

      // 적의 현재 합 의도 실행
      const enemyIntent = eAfter.intentQueue[0];
      let finalPlayer = pAfter;
      let finalEnemy = eAfter;
      let enemyMsg = "";

      if (enemyIntent) {
        finalEnemy = { ...eAfter, intentQueue: eAfter.intentQueue.slice(1) };
        const result = executeEnemyIntent(enemyIntent, finalEnemy, finalPlayer);
        finalPlayer = result.player;
        finalEnemy = result.enemy;
        enemyMsg = result.message;
      }

      // 합 종료 회복
      finalPlayer = applyClashRegen(finalPlayer);

      // 카드를 버린 더미로
      const hand = finalPlayer.hand.filter((c) => c.id !== card.id);
      const discardPile = [...finalPlayer.discardPile, card];
      finalPlayer = { ...finalPlayer, hand, discardPile };

      const newLogs: BattleLog[] = [
        ...state.battleLogs,
        {
          text: `${isCrit ? "🔥 회심! " : ""}${message}`,
          color: isCrit ? "text-yellow-300" : "text-amber-200",
        },
      ];

      if (enemyMsg) {
        newLogs.push({
          text: `👹 ${state.enemy.name}: ${enemyMsg}`,
          color: "text-red-300",
        });
      }

      // 상태 요약
      newLogs.push({
        text: `기혈 ${finalPlayer.hp}/${finalPlayer.maxHp} | ${finalEnemy.name} ${finalEnemy.hp}/${finalEnemy.maxHp}`,
        color: "text-gray-400",
      });

      const newClash = state.clashIndex + 1;

      // 적 사망 체크
      if (finalEnemy.hp <= 0) {
        const xpGain = 50 + finalEnemy.level * 10;
        const goldGain = 10 + finalEnemy.level * 5;
        finalPlayer = {
          ...finalPlayer,
          xp: finalPlayer.xp + xpGain,
          totalXp: finalPlayer.totalXp + xpGain,
          gold: finalPlayer.gold + goldGain,
          winStreak: finalPlayer.winStreak + 1,
        };
        newLogs.push({
          text: `🏆 ${finalEnemy.name}을(를) 쓰러뜨렸다! (경험치 +${xpGain}, 금 +${goldGain})`,
          color: "text-yellow-400",
        });
        return {
          ...state,
          phase: "victory",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: newClash,
          battleLogs: newLogs,
        };
      }

      // 플레이어 사망 체크
      if (finalPlayer.hp <= 0) {
        newLogs.push({ text: "주화입마... 의식이 흐려진다.", color: "text-red-600" });
        return {
          ...state,
          phase: "gameover",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: newClash,
          battleLogs: newLogs,
          lastUsedCard: card.name,
        };
      }

      // 5합 종료 → 새 턴 시작
      if (newClash >= 5 || finalEnemy.intentQueue.length === 0) {
        finalEnemy = refreshIntents(finalEnemy);
        finalPlayer = startTurnRegen(finalPlayer);
        finalPlayer = drawCards(finalPlayer, Math.max(0, 5 - finalPlayer.hand.length));
        finalPlayer = { ...finalPlayer, defense: 0 };
        finalEnemy = { ...finalEnemy, defense: 0 };
        newLogs.push({
          text: "─── 새로운 합이 시작된다 ───",
          color: "text-cyan-400",
        });
        return {
          ...state,
          phase: "battle_player_turn",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: 0,
          battleLogs: newLogs,
        };
      }

      return {
        ...state,
        player: finalPlayer,
        enemy: finalEnemy,
        clashIndex: newClash,
        battleLogs: newLogs,
      };
    }

    case "USE_BASIC": {
      // 기본 행동 (비용 0) — PLAY_CARD와 동일 로직이지만 hand에서 제거 안 함
      if (!state.player || !state.enemy) return state;
      const card = action.card;

      const { player: pAfter, enemy: eAfter, message } = executeCardEffect(
        card.name,
        state.player,
        state.enemy,
        card,
        false
      );

      const enemyIntent = eAfter.intentQueue[0];
      let finalPlayer = pAfter;
      let finalEnemy = eAfter;
      let enemyMsg = "";

      if (enemyIntent) {
        finalEnemy = { ...eAfter, intentQueue: eAfter.intentQueue.slice(1) };
        const result = executeEnemyIntent(enemyIntent, finalEnemy, finalPlayer);
        finalPlayer = result.player;
        finalEnemy = result.enemy;
        enemyMsg = result.message;
      }

      finalPlayer = applyClashRegen(finalPlayer);

      const newLogs: BattleLog[] = [
        ...state.battleLogs,
        { text: message, color: "text-gray-300" },
      ];
      if (enemyMsg) {
        newLogs.push({
          text: `👹 ${state.enemy.name}: ${enemyMsg}`,
          color: "text-red-300",
        });
      }
      newLogs.push({
        text: `기혈 ${finalPlayer.hp}/${finalPlayer.maxHp} | ${finalEnemy.name} ${finalEnemy.hp}/${finalEnemy.maxHp}`,
        color: "text-gray-400",
      });

      const newClash = state.clashIndex + 1;

      if (finalEnemy.hp <= 0) {
        const xpGain = 50 + finalEnemy.level * 10;
        const goldGain = 10 + finalEnemy.level * 5;
        finalPlayer = {
          ...finalPlayer,
          xp: finalPlayer.xp + xpGain,
          totalXp: finalPlayer.totalXp + xpGain,
          gold: finalPlayer.gold + goldGain,
          winStreak: finalPlayer.winStreak + 1,
        };
        newLogs.push({
          text: `🏆 승리! (경험치 +${xpGain}, 금 +${goldGain})`,
          color: "text-yellow-400",
        });
        return {
          ...state,
          phase: "victory",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: newClash,
          battleLogs: newLogs,
        };
      }

      if (finalPlayer.hp <= 0) {
        newLogs.push({ text: "주화입마...", color: "text-red-600" });
        return {
          ...state,
          phase: "gameover",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: newClash,
          battleLogs: newLogs,
          lastUsedCard: card.name,
        };
      }

      if (newClash >= 5 || finalEnemy.intentQueue.length === 0) {
        finalEnemy = refreshIntents(finalEnemy);
        finalPlayer = startTurnRegen(finalPlayer);
        finalPlayer = drawCards(finalPlayer, Math.max(0, 5 - finalPlayer.hand.length));
        finalPlayer = { ...finalPlayer, defense: 0 };
        finalEnemy = { ...finalEnemy, defense: 0 };
        newLogs.push({
          text: "─── 새로운 합이 시작된다 ───",
          color: "text-cyan-400",
        });
        return {
          ...state,
          phase: "battle_player_turn",
          player: finalPlayer,
          enemy: finalEnemy,
          clashIndex: 0,
          battleLogs: newLogs,
        };
      }

      return {
        ...state,
        player: finalPlayer,
        enemy: finalEnemy,
        clashIndex: newClash,
        battleLogs: newLogs,
      };
    }

    case "CONTINUE_AFTER_VICTORY": {
      if (!state.player) return state;
      // 체력 일부 회복 후 월드맵으로
      const healAmount = Math.floor(state.player.maxHp * 0.3);
      const player = {
        ...state.player,
        hp: Math.min(state.player.maxHp, state.player.hp + healAmount),
      };
      return {
        ...state,
        phase: "world",
        player,
        enemy: null,
        battleLogs: [],
      };
    }

    case "GO_TO_WORLD": {
      return { ...state, phase: "world" };
    }

    case "RESTART": {
      return { ...initialState };
    }

    case "RESURRECT": {
      // 사망 카운트 증가, 깨달음 XP를 localStorage에 저장
      const newDeathCount = state.deathCount + 1;
      if (typeof window !== "undefined") {
        const prevEnlightenment = parseInt(localStorage.getItem("guunrok_enlightenment") || "0", 10);
        localStorage.setItem("guunrok_enlightenment", String(prevEnlightenment + 1));
        localStorage.setItem("guunrok_deathCount", String(newDeathCount));
      }
      return {
        ...initialState,
        deathCount: newDeathCount,
      };
    }

    default:
      return state;
  }
}

// ─── Context ────────────────────────────────────────────────
const GameStateContext = createContext<GameState>(initialState);
const GameDispatchContext = createContext<Dispatch<Action>>(() => {});

export function GameProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(gameReducer, initialState);
  return (
    <GameStateContext.Provider value={state}>
      <GameDispatchContext.Provider value={dispatch}>
        {children}
      </GameDispatchContext.Provider>
    </GameStateContext.Provider>
  );
}

export function useGameState() {
  return useContext(GameStateContext);
}

export function useGameDispatch() {
  return useContext(GameDispatchContext);
}
