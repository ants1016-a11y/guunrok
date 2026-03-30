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
  InnBuff,
} from "@/lib/types";
import { createPlayer, startBattle, drawCards, startTurnRegen, applyClashRegen } from "@/lib/player";
import { createEnemy, refreshIntents, executeEnemyIntent } from "@/lib/enemies";
import { executeCardEffect, BASIC_ACTIONS } from "@/lib/cards";

// ─── State ──────────────────────────────────────────────────
export interface LastRewards {
  xp: number;
  gold: number;
  streak: number;
  isBoss: boolean;
}

export interface GameState {
  phase: GamePhase;
  player: Player | null;
  enemy: Enemy | null;
  encounter: number;
  clashIndex: number;
  battleLogs: BattleLog[];
  lastMessage: string;
  playerName: string;
  deathCount: number;
  lastUsedCard: string;
  innBuff: InnBuff | null;
  lastRewards: LastRewards | null;
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
  innBuff: null,
  lastRewards: null,
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
  | { type: "CONTINUE_TO_NEXT" }
  | { type: "VISIT_INN" }
  | { type: "INN_REST"; ratio: number; cost: number }
  | { type: "INN_EAT"; buff: InnBuff; cost: number }
  | { type: "LEAVE_INN_TO_BATTLE" }
  | { type: "LEAVE_INN_TO_WORLD" }
  | { type: "RESTART" }
  | { type: "GO_TO_WORLD" }
  | { type: "RESURRECT" };

// ─── 보상 계산 헬퍼 ─────────────────────────────────────────
function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function calculateRewards(enemy: Enemy, winStreak: number): LastRewards {
  const isBoss = enemy.type === "boss_macheon" || enemy.type === "hyulgyo_jangro";
  let xp: number;
  let gold: number;

  if (isBoss) {
    xp = 130 + randInt(0, 50);
    gold = 80 + randInt(0, 20);
  } else {
    const streakMul = Math.min(2, 1 + winStreak * 0.1);
    xp = Math.round((20 + randInt(0, 10)) * streakMul);
    gold = 10 + randInt(0, 5);
  }

  return { xp, gold, streak: winStreak + 1, isBoss };
}

// ─── 전투 합 처리 공통 로직 ─────────────────────────────────
function processClash(
  state: GameState,
  card: Card,
  isFromHand: boolean,
  isCrit: boolean,
): GameState {
  if (!state.player || !state.enemy) return state;

  const playerAfterCost = isFromHand
    ? { ...state.player, energy: state.player.energy - card.cost }
    : state.player;

  const { player: pAfter, enemy: eAfter, message } = executeCardEffect(
    card.name,
    playerAfterCost,
    state.enemy,
    card,
    isCrit,
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

  // 카드를 버린 더미로 (기본 행동 제외)
  if (isFromHand) {
    const hand = finalPlayer.hand.filter((c) => c.id !== card.id);
    const discardPile = [...finalPlayer.discardPile, card];
    finalPlayer = { ...finalPlayer, hand, discardPile };
  }

  const newLogs: BattleLog[] = [
    ...state.battleLogs,
    {
      text: `${isCrit ? "🔥 회심! " : ""}${message}`,
      color: isCrit ? "text-yellow-300" : isFromHand ? "text-amber-200" : "text-gray-300",
    },
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

  // 적 사망 → 보상 계산 → reward 화면
  if (finalEnemy.hp <= 0) {
    const rewards = calculateRewards(finalEnemy, finalPlayer.winStreak);
    finalPlayer = {
      ...finalPlayer,
      xp: finalPlayer.xp + rewards.xp,
      totalXp: finalPlayer.totalXp + rewards.xp,
      gold: finalPlayer.gold + rewards.gold,
      winStreak: finalPlayer.winStreak + 1,
    };
    newLogs.push({
      text: `🏆 ${finalEnemy.name}을(를) 쓰러뜨렸다! (명성 +${rewards.xp}, 금자 +${rewards.gold})`,
      color: "text-yellow-400",
    });
    return {
      ...state,
      phase: "reward",
      player: finalPlayer,
      enemy: finalEnemy,
      clashIndex: newClash,
      battleLogs: newLogs,
      lastRewards: rewards,
    };
  }

  // 플레이어 사망
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

  // 5합 종료 → 새 턴
  if (newClash >= 5 || finalEnemy.intentQueue.length === 0) {
    finalEnemy = refreshIntents(finalEnemy);
    finalPlayer = startTurnRegen(finalPlayer);
    finalPlayer = drawCards(finalPlayer, Math.max(0, 5 - finalPlayer.hand.length));
    // 방어 리셋 + 용정차 버프 적용
    let newDef = 0;
    if (state.innBuff?.type === "defense") {
      newDef = state.innBuff.val;
    }
    finalPlayer = { ...finalPlayer, defense: newDef };
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

// ─── Reducer ────────────────────────────────────────────────
function gameReducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "START_GAME": {
      const player = createPlayer(action.name);
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
        innBuff: null,
        lastRewards: null,
        lastMessage: action.inheritedMastery > 0
          ? "육체는 잊었으나, 영혼에 새겨진 검로는 기억한다."
          : "강호에 발을 딛다...",
      };
    }

    case "START_ENCOUNTER": {
      if (!state.player) return state;
      const enc = state.encounter + 1;
      const enemy = refreshIntents(createEnemy(enc));
      const player = startBattle(state.player, state.innBuff);
      return {
        ...state,
        phase: "battle_player_turn",
        player,
        enemy,
        encounter: enc,
        clashIndex: 0,
        battleLogs: [
          { text: `${enemy.name}이(가) 앞을 막아선다!`, color: "text-red-400" },
        ],
        lastMessage: "",
      };
    }

    case "PLAY_CARD": {
      if (!state.player || !state.enemy) return state;
      if (state.player.energy < action.card.cost) {
        return { ...state, lastMessage: "내공이 부족합니다!" };
      }
      return processClash(state, action.card, true, Math.random() < 0.15);
    }

    case "USE_BASIC": {
      if (!state.player || !state.enemy) return state;
      return processClash(state, action.card, false, false);
    }

    // ─── 보상 화면에서 다음으로 ───
    case "CONTINUE_TO_NEXT": {
      if (!state.player) return state;
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
        innBuff: null, // 식사 버프 소모
      };
    }

    // ─── 객잔 ───
    case "VISIT_INN": {
      return { ...state, phase: "inn" };
    }

    case "INN_REST": {
      if (!state.player || state.player.gold < action.cost) return state;
      const heal = Math.floor(state.player.maxHp * action.ratio);
      return {
        ...state,
        player: {
          ...state.player,
          gold: state.player.gold - action.cost,
          hp: Math.min(state.player.maxHp, state.player.hp + heal),
        },
      };
    }

    case "INN_EAT": {
      if (!state.player || state.player.gold < action.cost || state.innBuff) return state;
      return {
        ...state,
        player: {
          ...state.player,
          gold: state.player.gold - action.cost,
        },
        innBuff: action.buff,
      };
    }

    case "LEAVE_INN_TO_BATTLE": {
      return { ...state, phase: "world" };
    }

    case "LEAVE_INN_TO_WORLD": {
      return { ...state, phase: "world" };
    }

    case "GO_TO_WORLD": {
      return { ...state, phase: "world" };
    }

    case "RESTART": {
      return { ...initialState };
    }

    case "RESURRECT": {
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
