import { Player, PlayerStats, InnBuff } from "./types";
import { createStarterDeck } from "./cards";
import {
  calcAtk, calcDef, calcEva, calcFlee, calcMaxEn, calcMaxHp,
  calcEnRegen, calcClashHpRegen, calcClashEnRegen, BASE_ATK,
} from "./formulas";

const BASELINE_ATK = 16;

export function recalculateStats(p: Player): Player {
  const stats = p.stats;

  const maxHp = calcMaxHp(stats);
  const maxEnergy = calcMaxEn(stats) + p.tempMaxEnergyBonus;
  const attackPower = calcAtk(stats);
  const attackPowerBonus = Math.max(0, attackPower - BASELINE_ATK);
  const baseDefense = calcDef(stats);
  const energyRegen = calcEnRegen(stats);
  const evasion = calcEva(stats);
  const fleeChance = calcFlee(stats);
  const clashHpRegen = calcClashHpRegen(stats);
  const clashEnRegen = calcClashEnRegen(stats);

  return {
    ...p,
    maxHp, maxEnergy, attackPower, attackPowerBonus,
    baseDefense, energyRegen, evasion, fleeChance,
    clashHpRegen, clashEnRegen,
  };
}

export function createPlayer(name: string = "회귀한 둔재"): Player {
  const stats: PlayerStats = {
    근골: 10, 심법: 10, 외공: 10, 경공: 10, 자질: 10, 행운: 10,
  };

  const deck = createStarterDeck();

  const base: Player = {
    name, stats,
    hp: 0, maxHp: 100,
    energy: 0, maxEnergy: 5, energyRegen: 3,
    attackPower: 0, attackPowerBonus: 0,
    baseDefense: 0, defense: 0,
    evasion: 0, fleeChance: 0,
    clashHpRegen: 0, clashEnRegen: 0,
    gold: 0, xp: 0, totalXp: 0,
    enlightenmentIdx: 0, winStreak: 0,
    deck, hand: [], drawPile: [], discardPile: [],
    tempMaxEnergyBonus: 0,
  };

  const p = recalculateStats(base);
  return { ...p, hp: p.maxHp, energy: p.maxEnergy };
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function startBattle(player: Player, innBuff: InnBuff | null = null): Player {
  let p = { ...player, tempMaxEnergyBonus: 0, defense: 0 };
  p = recalculateStats(p);

  // 전투 시작 시 방어도 = calcDef (스탯 기반 DEF0)
  p = { ...p, defense: p.baseDefense };

  // 객잔 버프 적용
  if (innBuff) {
    if (innBuff.type === "energy") {
      p = { ...p, energy: (p.energy || 0) + innBuff.val };
    } else if (innBuff.type === "maxHp") {
      p = { ...p, maxHp: p.maxHp + innBuff.val, hp: p.hp + innBuff.val };
    }
  }

  const drawPile = shuffle([...p.deck]);
  const hand = drawPile.splice(0, 5);

  return { ...p, hp: Math.min(p.hp, p.maxHp), energy: p.maxEnergy, drawPile, hand, discardPile: [] };
}

export function drawCards(player: Player, count: number): Player {
  let p = { ...player, hand: [...player.hand], drawPile: [...player.drawPile], discardPile: [...player.discardPile] };
  for (let i = 0; i < count; i++) {
    if (p.drawPile.length === 0) {
      if (p.discardPile.length === 0) break;
      p.drawPile = shuffle(p.discardPile);
      p.discardPile = [];
    }
    if (p.drawPile.length > 0) p.hand.push(p.drawPile.pop()!);
  }
  return p;
}

export function startTurnRegen(player: Player): Player {
  return {
    ...player,
    energy: Math.min(player.maxEnergy, player.energy + player.energyRegen),
  };
}

export function applyClashRegen(player: Player): Player {
  let p = { ...player };
  if (p.hp <= 0) return p;
  if (p.clashHpRegen > 0) p.hp = Math.min(p.maxHp, p.hp + p.clashHpRegen);
  if (p.clashEnRegen > 0) p.energy += p.clashEnRegen;
  return p;
}
