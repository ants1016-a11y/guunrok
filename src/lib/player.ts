import { Player, PlayerStats } from "./types";
import { createStarterDeck } from "./cards";

const BASE_ATK = 5;
const BASELINE_ATK = 16;

export function recalculateStats(p: Player): Player {
  const stats = p.stats;

  // 1. 기혈
  const maxHp = 100 + (stats.근골 - 10) * 10;

  // 2. 내공
  const v = stats.심법;
  let bonus: number;
  if (v <= 15) bonus = v - 10;
  else if (v <= 22) bonus = 5 + Math.floor((v - 15) / 2);
  else bonus = 5 + 3 + Math.floor((v - 22) / 3);
  const maxEnergy = 5 + bonus + p.tempMaxEnergyBonus;

  // 3. 공격력
  const attackPower = Math.floor(BASE_ATK + stats.외공 * 1.0 + stats.근골 * 0.1);
  const attackPowerBonus = Math.max(0, attackPower - BASELINE_ATK);

  // 4. 방어 시작치
  const baseDefense = Math.floor(stats.근골 * 0.6 + stats.외공 * 0.2);

  // 5. 내공 회복
  const energyRegen = 3 + Math.floor(stats.심법 / 5);

  // 6. 회피율
  const evasion = Math.min(0.25, 0.05 + stats.경공 * 0.007);

  // 7. 도주 확률
  const fleeChance = Math.min(60, 10 + stats.경공 * 1.2);

  // 8. 합 종료 회복
  const clashHpRegen = Math.min(3, Math.floor(stats.근골 / 10));
  const clashEnRegen = Math.min(2, Math.floor(stats.심법 / 12));

  return {
    ...p,
    maxHp,
    maxEnergy,
    attackPower,
    attackPowerBonus,
    baseDefense,
    energyRegen,
    evasion,
    fleeChance,
    clashHpRegen,
    clashEnRegen,
  };
}

export function createPlayer(name: string = "회귀한 둔재"): Player {
  const stats: PlayerStats = {
    근골: 10,
    심법: 10,
    외공: 10,
    경공: 10,
    자질: 10,
    행운: 10,
  };

  const deck = createStarterDeck();

  const base: Player = {
    name,
    stats,
    hp: 0,
    maxHp: 100,
    energy: 0,
    maxEnergy: 5,
    energyRegen: 3,
    attackPower: 0,
    attackPowerBonus: 0,
    baseDefense: 0,
    defense: 0,
    evasion: 0,
    fleeChance: 0,
    clashHpRegen: 0,
    clashEnRegen: 0,
    gold: 0,
    xp: 0,
    totalXp: 0,
    enlightenmentIdx: 0,
    winStreak: 0,
    deck,
    hand: [],
    drawPile: [],
    discardPile: [],
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

export function startBattle(player: Player): Player {
  let p = { ...player, tempMaxEnergyBonus: 0, defense: 0 };
  p = recalculateStats(p);

  const drawPile = shuffle([...p.deck]);
  const hand = drawPile.splice(0, 5);

  return { ...p, hp: Math.min(p.hp, p.maxHp), drawPile, hand, discardPile: [] };
}

export function drawCards(player: Player, count: number): Player {
  let p = { ...player, hand: [...player.hand], drawPile: [...player.drawPile], discardPile: [...player.discardPile] };

  for (let i = 0; i < count; i++) {
    if (p.drawPile.length === 0) {
      if (p.discardPile.length === 0) break;
      p.drawPile = shuffle(p.discardPile);
      p.discardPile = [];
    }
    if (p.drawPile.length > 0) {
      p.hand.push(p.drawPile.pop()!);
    }
  }

  return p;
}

export function startTurnRegen(player: Player): Player {
  const regen = player.energyRegen;
  return {
    ...player,
    energy: Math.min(player.maxEnergy, player.energy + regen),
  };
}

export function applyClashRegen(player: Player): Player {
  let p = { ...player };
  if (p.clashHpRegen > 0) {
    p.hp = Math.min(p.maxHp, p.hp + p.clashHpRegen);
  }
  if (p.clashEnRegen > 0) {
    p.energy += p.clashEnRegen;
  }
  return p;
}
