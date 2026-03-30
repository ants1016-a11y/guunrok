"use client";

import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  ReactNode,
  Dispatch,
} from "react";
import {
  Player,
  Enemy,
  BattleLog,
  Screen,
  Card,
  InnBuff,
} from "@/lib/types";
import { createPlayer, startBattle, drawCards, startTurnRegen, applyClashRegen } from "@/lib/player";
import { createEnemy, refreshIntents, executeEnemyIntent } from "@/lib/enemies";
import { executeCardEffect } from "@/lib/cards";

// ─── 저장 데이터 ────────────────────────────────────────────
export interface SaveData {
  playerName: string;
  deathCount: number;
  inheritedMastery: number;
  xp: number;
  totalXp: number;
  gold: number;
  winStreak: number;
  hp: number;
  maxHp: number;
  encounter: number;
  deckMasteries: { name: string; mastery: number }[];
  innBuff: InnBuff | null;
}

// ─── 보상 데이터 ────────────────────────────────────────────
export interface LastRewards {
  xp: number;
  gold: number;
  streak: number;
  isBoss: boolean;
}

// ─── 전투 서브 상태 ─────────────────────────────────────────
export interface BattleState {
  enemy: Enemy;
  clashIndex: number;
  logs: BattleLog[];
  playerTurn: boolean; // true = 플레이어 턴, false = 연출 중
}

// ─── GameState ──────────────────────────────────────────────
export interface GameState {
  screen: Screen;
  playerName: string;
  player: Player | null;
  encounter: number;
  deathCount: number;
  inheritedMastery: number;
  innBuff: InnBuff | null;
  lastRewards: LastRewards | null;
  lastUsedCard: string;
  lastMessage: string;
  battle: BattleState | null;
  saveNotice: string;
}

const initialState: GameState = {
  screen: "title",
  playerName: "",
  player: null,
  encounter: 0,
  deathCount: 0,
  inheritedMastery: 0,
  innBuff: null,
  lastRewards: null,
  lastUsedCard: "",
  lastMessage: "",
  battle: null,
  saveNotice: "",
};

// ─── Actions ────────────────────────────────────────────────
type Action =
  | { type: "START_GAME"; name: string }
  | { type: "START_BATTLE" }
  | { type: "PLAY_CARD"; card: Card }
  | { type: "USE_BASIC"; card: Card }
  | { type: "CONTINUE_TO_NEXT" }
  | { type: "VISIT_INN" }
  | { type: "INN_REST"; ratio: number; cost: number }
  | { type: "INN_EAT"; buff: InnBuff; cost: number }
  | { type: "LEAVE_INN" }
  | { type: "RESURRECT" }
  | { type: "SAVE_GAME" }
  | { type: "LOAD_GAME"; data: SaveData }
  | { type: "GO_MENU" };

// ─── 헬퍼 ───────────────────────────────────────────────────
function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function calculateRewards(enemy: Enemy, winStreak: number): LastRewards {
  const isBoss = enemy.type === "boss_macheon" || enemy.type === "hyulgyo_jangro";
  if (isBoss) {
    return { xp: 130 + randInt(0, 50), gold: 80 + randInt(0, 20), streak: winStreak + 1, isBoss };
  }
  const mul = Math.min(2, 1 + winStreak * 0.1);
  return { xp: Math.round((20 + randInt(0, 10)) * mul), gold: 10 + randInt(0, 5), streak: winStreak + 1, isBoss };
}

function buildSaveData(state: GameState): SaveData | null {
  if (!state.player) return null;
  return {
    playerName: state.playerName,
    deathCount: state.deathCount,
    inheritedMastery: state.inheritedMastery,
    xp: state.player.xp,
    totalXp: state.player.totalXp,
    gold: state.player.gold,
    winStreak: state.player.winStreak,
    hp: state.player.hp,
    maxHp: state.player.maxHp,
    encounter: state.encounter,
    deckMasteries: state.player.deck.map((c) => ({ name: c.name, mastery: c.mastery })),
    innBuff: state.innBuff,
  };
}

// ─── 전투 합 처리 ───────────────────────────────────────────
function processClash(state: GameState, card: Card, isFromHand: boolean, isCrit: boolean): GameState {
  if (!state.player || !state.battle) return state;
  const { enemy } = state.battle;

  const pCost = isFromHand
    ? { ...state.player, energy: state.player.energy - card.cost }
    : state.player;

  const { player: pAfter, enemy: eAfter, message } = executeCardEffect(card.name, pCost, enemy, card, isCrit);

  const intent = eAfter.intentQueue[0];
  let fp = pAfter;
  let fe = eAfter;
  let eMsg = "";

  if (intent) {
    fe = { ...eAfter, intentQueue: eAfter.intentQueue.slice(1) };
    const r = executeEnemyIntent(intent, fe, fp);
    fp = r.player;
    fe = r.enemy;
    eMsg = r.message;
  }

  fp = applyClashRegen(fp);

  if (isFromHand) {
    const hand = fp.hand.filter((c) => c.id !== card.id);
    fp = { ...fp, hand, discardPile: [...fp.discardPile, card] };
  }

  const logs: BattleLog[] = [
    ...state.battle.logs,
    { text: `${isCrit ? "🔥 회심! " : ""}${message}`, color: isCrit ? "text-yellow-300" : isFromHand ? "text-amber-200" : "text-gray-300" },
  ];
  if (eMsg) logs.push({ text: `👹 ${enemy.name}: ${eMsg}`, color: "text-red-300" });
  logs.push({ text: `기혈 ${fp.hp}/${fp.maxHp} | ${fe.name} ${fe.hp}/${fe.maxHp}`, color: "text-gray-400" });

  const newClash = state.battle.clashIndex + 1;

  // 적 사망 → reward
  if (fe.hp <= 0) {
    const rewards = calculateRewards(fe, fp.winStreak);
    fp = { ...fp, xp: fp.xp + rewards.xp, totalXp: fp.totalXp + rewards.xp, gold: fp.gold + rewards.gold, winStreak: fp.winStreak + 1 };
    logs.push({ text: `🏆 ${fe.name}을(를) 쓰러뜨렸다! (명성 +${rewards.xp}, 금자 +${rewards.gold})`, color: "text-yellow-400" });
    return { ...state, screen: "reward", player: fp, battle: { ...state.battle, enemy: fe, clashIndex: newClash, logs, playerTurn: false }, lastRewards: rewards };
  }

  // 플레이어 사망
  if (fp.hp <= 0) {
    logs.push({ text: "주화입마... 의식이 흐려진다.", color: "text-red-600" });
    return { ...state, screen: "death", player: fp, battle: { ...state.battle, enemy: fe, clashIndex: newClash, logs, playerTurn: false }, lastUsedCard: card.name };
  }

  // 5합 종료 → 새 턴
  if (newClash >= 5 || fe.intentQueue.length === 0) {
    fe = refreshIntents(fe);
    fp = startTurnRegen(fp);
    fp = drawCards(fp, Math.max(0, 5 - fp.hand.length));
    let newDef = 0;
    if (state.innBuff?.type === "defense") newDef = state.innBuff.val;
    fp = { ...fp, defense: newDef };
    fe = { ...fe, defense: 0 };
    logs.push({ text: "─── 새로운 합이 시작된다 ───", color: "text-cyan-400" });
    return { ...state, player: fp, battle: { enemy: fe, clashIndex: 0, logs, playerTurn: true } };
  }

  return { ...state, player: fp, battle: { ...state.battle, enemy: fe, clashIndex: newClash, logs } };
}

// ─── Reducer ────────────────────────────────────────────────
function gameReducer(state: GameState, action: Action): GameState {
  switch (action.type) {

    case "START_GAME": {
      // localStorage에서 계승 데이터 로드
      let deathCount = 0;
      let inheritedMastery = 0;
      if (typeof window !== "undefined") {
        deathCount = parseInt(localStorage.getItem("guunrok_deathCount") || "0", 10);
        inheritedMastery = parseInt(localStorage.getItem("guunrok_enlightenment") || "0", 10);
      }
      const player = createPlayer(action.name);
      if (inheritedMastery > 0) {
        player.deck = player.deck.map((c) => ({ ...c, mastery: Math.min(c.masteryMax, c.mastery + inheritedMastery) }));
      }
      return {
        ...state,
        screen: "menu",
        player,
        playerName: action.name,
        encounter: 0,
        deathCount,
        inheritedMastery,
        innBuff: null,
        lastRewards: null,
        battle: null,
        lastMessage: inheritedMastery > 0 ? "육체는 잊었으나, 영혼에 새겨진 검로는 기억한다." : "강호에 발을 딛다...",
        saveNotice: "",
      };
    }

    case "START_BATTLE": {
      if (!state.player) return state;
      const enc = state.encounter + 1;
      const enemy = refreshIntents(createEnemy(enc));
      const player = startBattle(state.player, state.innBuff);
      return {
        ...state,
        screen: "battle",
        player,
        encounter: enc,
        battle: {
          enemy,
          clashIndex: 0,
          logs: [{ text: `${enemy.name}이(가) 앞을 막아선다!`, color: "text-red-400" }],
          playerTurn: true,
        },
        lastMessage: "",
      };
    }

    case "PLAY_CARD": {
      if (!state.player || !state.battle) return state;
      if (state.player.energy < action.card.cost) return { ...state, lastMessage: "내공이 부족합니다!" };
      return processClash(state, action.card, true, Math.random() < 0.15);
    }

    case "USE_BASIC": {
      if (!state.player || !state.battle) return state;
      return processClash(state, action.card, false, false);
    }

    case "CONTINUE_TO_NEXT": {
      if (!state.player) return state;
      const heal = Math.floor(state.player.maxHp * 0.3);
      return {
        ...state,
        screen: "menu",
        player: { ...state.player, hp: Math.min(state.player.maxHp, state.player.hp + heal) },
        battle: null,
        innBuff: null,
      };
    }

    case "VISIT_INN":
      return { ...state, screen: "inn" };

    case "INN_REST": {
      if (!state.player || state.player.gold < action.cost) return state;
      const heal = Math.floor(state.player.maxHp * action.ratio);
      return { ...state, player: { ...state.player, gold: state.player.gold - action.cost, hp: Math.min(state.player.maxHp, state.player.hp + heal) } };
    }

    case "INN_EAT": {
      if (!state.player || state.player.gold < action.cost || state.innBuff) return state;
      return { ...state, player: { ...state.player, gold: state.player.gold - action.cost }, innBuff: action.buff };
    }

    case "LEAVE_INN":
      return { ...state, screen: "menu" };

    case "GO_MENU":
      return { ...state, screen: "menu", battle: null };

    case "RESURRECT": {
      const newDeath = state.deathCount + 1;
      if (typeof window !== "undefined") {
        const prev = parseInt(localStorage.getItem("guunrok_enlightenment") || "0", 10);
        localStorage.setItem("guunrok_enlightenment", String(prev + 1));
        localStorage.setItem("guunrok_deathCount", String(newDeath));
      }
      return { ...initialState, deathCount: newDeath };
    }

    case "SAVE_GAME": {
      const data = buildSaveData(state);
      if (data && typeof window !== "undefined") {
        localStorage.setItem("guunrok_save", JSON.stringify(data));
      }
      return { ...state, saveNotice: "기록을 저장했습니다." };
    }

    case "LOAD_GAME": {
      const d = action.data;
      const player = createPlayer(d.playerName);
      // mastery 복원
      player.deck = player.deck.map((c) => {
        const saved = d.deckMasteries.find((m) => m.name === c.name);
        return saved ? { ...c, mastery: saved.mastery } : c;
      });
      player.xp = d.xp;
      player.totalXp = d.totalXp;
      player.gold = d.gold;
      player.winStreak = d.winStreak;
      player.hp = d.hp;
      player.maxHp = d.maxHp;
      return {
        ...state,
        screen: "menu",
        player,
        playerName: d.playerName,
        encounter: d.encounter,
        deathCount: d.deathCount,
        inheritedMastery: d.inheritedMastery,
        innBuff: d.innBuff,
        battle: null,
        lastMessage: `${d.playerName}의 기록을 불러왔습니다.`,
        saveNotice: "",
      };
    }

    default:
      return state;
  }
}

// ─── Context + Provider ─────────────────────────────────────
const GameStateContext = createContext<GameState>(initialState);
const GameDispatchContext = createContext<Dispatch<Action>>(() => {});

export function GameProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // 자동 로드
  useEffect(() => {
    try {
      const raw = localStorage.getItem("guunrok_save");
      if (raw) {
        const data: SaveData = JSON.parse(raw);
        dispatch({ type: "LOAD_GAME", data });
      }
    } catch { /* 저장 데이터 없음 */ }
  }, []);

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
