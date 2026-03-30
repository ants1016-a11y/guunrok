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
  PlayerStats,
} from "@/lib/types";
import { createPlayer, startBattle, drawCards, startTurnRegen, applyClashRegen } from "@/lib/player";
import { createEnemy, createEnemyByTier, refreshIntents, executeEnemyIntent } from "@/lib/enemies";
import { executeCardEffect, createDeckFromUnlocked, STARTER_CARD_NAMES } from "@/lib/cards";
import { recalculateStats } from "@/lib/player";
import { MapNode, generateNorthRoute } from "@/lib/worldmap";

// ─── 상수 ───────────────────────────────────────────────────
const CARD_UPGRADE_BASE = 100;
const CARD_MASTERY_MAX = 12;
const STAT_MAX = 30;

// ─── 영구 저장 (guunrok_legacy) ─────────────────────────────
export interface LegacyData {
  statsBase: PlayerStats;
  unlockedCards: string[]; // 스타터 외 해금된 카드 이름 목록
  deathCount: number;
}

const DEFAULT_LEGACY: LegacyData = {
  statsBase: { 근골: 10, 심법: 10, 외공: 10, 경공: 10, 자질: 10, 행운: 10 },
  unlockedCards: [],
  deathCount: 0,
};

function loadLegacy(): LegacyData {
  if (typeof window === "undefined") return DEFAULT_LEGACY;
  try {
    const raw = localStorage.getItem("guunrok_legacy");
    if (raw) return { ...DEFAULT_LEGACY, ...JSON.parse(raw) };
  } catch { /* noop */ }
  return DEFAULT_LEGACY;
}

function saveLegacy(data: LegacyData) {
  if (typeof window === "undefined") return;
  localStorage.setItem("guunrok_legacy", JSON.stringify(data));
}

// ─── 임시 저장 (guunrok_save) ───────────────────────────────
export interface RegionProgress {
  mapNodes: MapNode[];
  currentNodeId: number;
}

export interface SaveData {
  playerName: string;
  xp: number;
  totalXp: number;
  gold: number;
  winStreak: number;
  hp: number;
  maxHp: number;
  encounter: number;
  deckMasteries: { name: string; mastery: number }[];
  deckNames: string[];
  innBuff: InnBuff | null;
  regionProgress: RegionProgress | null;
  stats: PlayerStats;
}

// ─── 보상 / 전투 서브 상태 ──────────────────────────────────
export interface LastRewards {
  xp: number;
  gold: number;
  streak: number;
  isBoss: boolean;
}

export interface BattleState {
  enemy: Enemy;
  clashIndex: number;
  logs: BattleLog[];
  playerTurn: boolean;
}

// ─── GameState ──────────────────────────────────────────────
export interface GameState {
  screen: Screen;
  playerName: string;
  player: Player | null;
  encounter: number;
  legacy: LegacyData;
  innBuff: InnBuff | null;
  lastRewards: LastRewards | null;
  lastUsedCard: string;
  lastMessage: string;
  battle: BattleState | null;
  saveNotice: string;
  mapNodes: MapNode[] | null;
  currentNodeId: number;
}

const initialState: GameState = {
  screen: "title",
  playerName: "",
  player: null,
  encounter: 0,
  legacy: DEFAULT_LEGACY,
  innBuff: null,
  lastRewards: null,
  lastUsedCard: "",
  lastMessage: "",
  battle: null,
  saveNotice: "",
  mapNodes: null,
  currentNodeId: -1,
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
  | { type: "VISIT_TRAINING" }
  | { type: "LEAVE_TRAINING" }
  | { type: "UPGRADE_STAT"; stat: string }
  | { type: "UPGRADE_CARD"; cardId: string }
  | { type: "RESURRECT" }
  | { type: "SAVE_GAME" }
  | { type: "LOAD_GAME"; data: SaveData }
  | { type: "GO_MENU" }
  | { type: "ENTER_WORLDMAP" }
  | { type: "VISIT_NODE"; nodeId: number }
  | { type: "BACK_TO_WORLDMAP" };

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

function getStatUpgradeCost(currentStatValue: number): number {
  return currentStatValue + 40;
}

function buildSaveData(state: GameState): SaveData | null {
  if (!state.player) return null;
  return {
    playerName: state.playerName,
    xp: state.player.xp,
    totalXp: state.player.totalXp,
    gold: state.player.gold,
    winStreak: state.player.winStreak,
    hp: state.player.hp,
    maxHp: state.player.maxHp,
    encounter: state.encounter,
    deckMasteries: state.player.deck.map((c) => ({ name: c.name, mastery: c.mastery })),
    deckNames: state.player.deck.map((c) => c.name),
    innBuff: state.innBuff,
    regionProgress: state.mapNodes ? { mapNodes: state.mapNodes, currentNodeId: state.currentNodeId } : null,
    stats: state.player.stats,
  };
}

// ─── 전투 합 처리 ───────────────────────────────────────────
function processClash(state: GameState, card: Card, isFromHand: boolean, isCrit: boolean): GameState {
  if (!state.player || !state.battle) return state;
  const { enemy } = state.battle;

  const pCost = isFromHand ? { ...state.player, energy: state.player.energy - card.cost } : state.player;
  const { player: pAfter, enemy: eAfter, message } = executeCardEffect(card.name, pCost, enemy, card, isCrit);

  const intent = eAfter.intentQueue[0];
  let fp = pAfter;
  let fe = eAfter;
  let eMsg = "";

  if (intent) {
    fe = { ...eAfter, intentQueue: eAfter.intentQueue.slice(1) };
    const r = executeEnemyIntent(intent, fe, fp);
    fp = r.player; fe = r.enemy; eMsg = r.message;
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

  if (fe.hp <= 0) {
    const rewards = calculateRewards(fe, fp.winStreak);
    fp = { ...fp, xp: fp.xp + rewards.xp, totalXp: fp.totalXp + rewards.xp, gold: fp.gold + rewards.gold, winStreak: fp.winStreak + 1 };
    logs.push({ text: `🏆 ${fe.name}을(를) 쓰러뜨렸다! (명성 +${rewards.xp}, 금자 +${rewards.gold})`, color: "text-yellow-400" });
    return { ...state, screen: "reward", player: fp, battle: { ...state.battle, enemy: fe, clashIndex: newClash, logs, playerTurn: false }, lastRewards: rewards };
  }

  if (fp.hp <= 0) {
    logs.push({ text: "주화입마... 의식이 흐려진다.", color: "text-red-600" });
    return { ...state, screen: "death", player: fp, battle: { ...state.battle, enemy: fe, clashIndex: newClash, logs, playerTurn: false }, lastUsedCard: card.name };
  }

  if (newClash >= 5 || fe.intentQueue.length === 0) {
    fe = refreshIntents(fe);
    fp = startTurnRegen(fp);
    fp = drawCards(fp, Math.max(0, 5 - fp.hand.length));
    let newDef = fp.baseDefense;
    if (state.innBuff?.type === "defense") newDef += state.innBuff.val;
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
      const legacy = loadLegacy();
      const player = createPlayer(action.name);
      // 영구 스탯 적용
      player.stats = { ...legacy.statsBase };
      // 해금된 카드로 덱 구성 (mastery 1성)
      player.deck = createDeckFromUnlocked(legacy.unlockedCards);
      const p = recalculateStats(player);
      return {
        ...state,
        screen: "menu",
        player: { ...p, hp: p.maxHp, energy: p.maxEnergy },
        playerName: action.name,
        encounter: 0,
        legacy,
        innBuff: null,
        lastRewards: null,
        battle: null,
        mapNodes: null,
        currentNodeId: -1,
        lastMessage: legacy.deathCount > 0 ? "다시 강호에 발을 딛는다." : "강호에 발을 딛다...",
        saveNotice: "",
      };
    }

    case "START_BATTLE": {
      if (!state.player) return state;
      const enc = state.encounter + 1;
      const enemy = refreshIntents(createEnemy(enc));
      const player = startBattle(state.player, state.innBuff);
      return {
        ...state, screen: "battle", player, encounter: enc,
        battle: { enemy, clashIndex: 0, logs: [{ text: `${enemy.name}이(가) 앞을 막아선다!`, color: "text-red-400" }], playerTurn: true },
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
      const nextScreen: Screen = state.mapNodes ? "worldmap" : "menu";
      return { ...state, screen: nextScreen, player: { ...state.player, hp: Math.min(state.player.maxHp, state.player.hp + heal) }, battle: null, innBuff: null };
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
      return { ...state, screen: state.mapNodes ? "worldmap" : "menu" };

    case "VISIT_TRAINING":
      return { ...state, screen: "training" };

    case "LEAVE_TRAINING":
      return { ...state, screen: state.mapNodes ? "worldmap" : "menu" };

    case "UPGRADE_STAT": {
      if (!state.player) return state;
      const stat = action.stat as keyof PlayerStats;
      if (!(stat in state.player.stats)) return state;
      if (state.player.stats[stat] >= STAT_MAX) return state;
      const cost = getStatUpgradeCost(state.player.stats[stat]);
      if (state.player.xp < cost) return state;
      const newStats = { ...state.player.stats, [stat]: state.player.stats[stat] + 1 };
      let p = { ...state.player, stats: newStats, xp: state.player.xp - cost };
      p = recalculateStats(p);
      const newLegacy = { ...state.legacy, statsBase: newStats };
      saveLegacy(newLegacy);
      return { ...state, player: p, legacy: newLegacy };
    }

    case "UPGRADE_CARD": {
      if (!state.player) return state;
      const idx = state.player.deck.findIndex((c) => c.id === action.cardId);
      if (idx === -1) return state;
      const card = state.player.deck[idx];
      if (card.mastery >= CARD_MASTERY_MAX) return state;
      const cost = CARD_UPGRADE_BASE * (card.mastery ** 2);
      if (state.player.xp < cost) return state;
      const newDeck = [...state.player.deck];
      newDeck[idx] = { ...card, mastery: card.mastery + 1 };
      return { ...state, player: { ...state.player, deck: newDeck, xp: state.player.xp - cost } };
    }

    case "GO_MENU":
      return { ...state, screen: "menu", battle: null };

    case "ENTER_WORLDMAP": {
      if (state.mapNodes && state.currentNodeId >= 0) return { ...state, screen: "worldmap" };
      return { ...state, screen: "worldmap", mapNodes: generateNorthRoute(), currentNodeId: 0 };
    }

    case "VISIT_NODE": {
      if (!state.player || !state.mapNodes) return state;
      const node = state.mapNodes.find((n) => n.id === action.nodeId);
      if (!node || node.visited) return state;
      const current = state.mapNodes.find((n) => n.id === state.currentNodeId);
      if (!current || !current.connections.includes(action.nodeId)) return state;
      const updatedNodes = state.mapNodes.map((n) => n.id === action.nodeId ? { ...n, visited: true } : n);

      if (node.type === "combat" || node.type === "boss") {
        const enc = state.encounter + 1;
        const enemy = refreshIntents(createEnemyByTier(node.tier));
        const player = startBattle(state.player, state.innBuff);
        return { ...state, screen: "battle", player, encounter: enc, mapNodes: updatedNodes, currentNodeId: action.nodeId,
          battle: { enemy, clashIndex: 0, logs: [{ text: `${enemy.name}이(가) 앞을 막아선다!`, color: "text-red-400" }], playerTurn: true }, lastMessage: "" };
      }
      if (node.type === "inn") return { ...state, screen: "inn", mapNodes: updatedNodes, currentNodeId: action.nodeId };
      if (node.type === "training") return { ...state, screen: "training", mapNodes: updatedNodes, currentNodeId: action.nodeId };
      return { ...state, mapNodes: updatedNodes, currentNodeId: action.nodeId };
    }

    case "BACK_TO_WORLDMAP":
      return state.mapNodes ? { ...state, screen: "worldmap" } : { ...state, screen: "menu" };

    case "RESURRECT": {
      // 영구 데이터 업데이트: 스탯 유지, 해금 카드 유지, 사망 횟수 +1
      const legacy = loadLegacy();
      // 현재 스탯을 영구에 저장 (이미 UPGRADE_STAT에서 저장되지만 안전장치)
      if (state.player) {
        legacy.statsBase = { ...state.player.stats };
        // 현재 덱에 스타터가 아닌 카드가 있으면 해금 목록에 추가
        for (const c of state.player.deck) {
          if (!STARTER_CARD_NAMES.includes(c.name) && !legacy.unlockedCards.includes(c.name)) {
            legacy.unlockedCards.push(c.name);
          }
        }
      }
      legacy.deathCount += 1;
      saveLegacy(legacy);
      // guunrok_save 삭제
      if (typeof window !== "undefined") {
        localStorage.removeItem("guunrok_save");
      }
      return { ...initialState, legacy };
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
      const legacy = loadLegacy();
      const player = createPlayer(d.playerName);
      player.deck = createDeckFromUnlocked(legacy.unlockedCards);
      // mastery 복원
      player.deck = player.deck.map((c) => {
        const saved = d.deckMasteries.find((m) => m.name === c.name);
        return saved ? { ...c, mastery: saved.mastery } : c;
      });
      player.stats = d.stats || legacy.statsBase;
      player.xp = d.xp; player.totalXp = d.totalXp;
      player.gold = d.gold; player.winStreak = d.winStreak;
      player.hp = d.hp; player.maxHp = d.maxHp;
      const restoredPlayer = recalculateStats(player);
      return {
        ...state, screen: "menu", player: restoredPlayer, playerName: d.playerName,
        encounter: d.encounter, legacy, innBuff: d.innBuff, battle: null,
        mapNodes: d.regionProgress?.mapNodes ?? null,
        currentNodeId: d.regionProgress?.currentNodeId ?? -1,
        lastMessage: `${d.playerName}의 기록을 불러왔습니다.`, saveNotice: "",
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

  useEffect(() => {
    try {
      const raw = localStorage.getItem("guunrok_save");
      if (raw) {
        const data: SaveData = JSON.parse(raw);
        dispatch({ type: "LOAD_GAME", data });
      }
    } catch { /* noop */ }
  }, []);

  return (
    <GameStateContext.Provider value={state}>
      <GameDispatchContext.Provider value={dispatch}>
        {children}
      </GameDispatchContext.Provider>
    </GameStateContext.Provider>
  );
}

export function useGameState() { return useContext(GameStateContext); }
export function useGameDispatch() { return useContext(GameDispatchContext); }
