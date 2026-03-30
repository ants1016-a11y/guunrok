import { PlayerStats, Card } from "./types";

// ─── 기본 상수 ──────────────────────────────────────────────
export const BASE_ATK = 5;
export const BASE_DEF = 0;
export const BASE_EN = 5;
export const BASE_HP = 100;
export const STAT_BASELINE = 10; // 초기 스탯 기준

// ─── 파생값 계산 ────────────────────────────────────────────
export function calcAtk(stats: PlayerStats): number {
  return Math.floor(BASE_ATK + stats.외공 * 1.0 + stats.근골 * 0.1);
}

export function calcDef(stats: PlayerStats): number {
  return Math.floor(BASE_DEF + stats.근골 * 0.6 + stats.외공 * 0.2);
}

export function calcEva(stats: PlayerStats): number {
  return Math.min(0.25, 0.05 + stats.경공 * 0.007);
}

export function calcFlee(stats: PlayerStats): number {
  return Math.min(0.60, 0.10 + stats.경공 * 0.012);
}

export function calcMaxEn(stats: PlayerStats): number {
  return BASE_EN + Math.floor(stats.심법 / 10);
}

export function calcMaxHp(stats: PlayerStats): number {
  return BASE_HP + (stats.근골 - STAT_BASELINE) * 2;
}

export function calcEnRegen(stats: PlayerStats): number {
  return 3 + Math.floor(stats.심법 / 5);
}

export function calcClashHpRegen(stats: PlayerStats): number {
  return Math.min(3, Math.floor(stats.근골 / 10));
}

export function calcClashEnRegen(stats: PlayerStats): number {
  return Math.min(2, Math.floor(stats.심법 / 12));
}

// ─── 카드 스케일링 ──────────────────────────────────────────
// scalingType: 물리계(공격) vs 내공계(기술/약화)
export function getCardScalingType(card: Card): "physical" | "internal" {
  return card.type === "공격" ? "physical" : "internal";
}

export function calcCardPower(card: Card, stats: PlayerStats): number {
  const base = card.baseValue;
  const masteryMul = 1 + (card.mastery - 1) * 0.2;
  const scaledBase = Math.floor(base * masteryMul);

  const scaling = getCardScalingType(card);
  const highMasteryBonus = card.mastery >= 5 ? 0.1 : 0;

  if (scaling === "physical") {
    // 물리계: 외공 주력, 심법 보조 (+5성 이상 심법 추가)
    return Math.floor(scaledBase + stats.외공 * 0.8 + stats.심법 * (0.2 + highMasteryBonus));
  }
  // 내공계: 심법 주력, 외공 보조 (+5성 이상 심법 추가)
  return Math.floor(scaledBase + stats.심법 * (0.8 + highMasteryBonus) + stats.외공 * 0.2);
}
