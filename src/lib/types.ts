// ─── 카드 시스템 ────────────────────────────────────────────
export type CardType = "공격" | "방어" | "기술" | "약화";

export interface Card {
  id: string;
  name: string;
  type: CardType;
  cost: number;
  description: string;
  baseValue: number;
  mastery: number;
  masteryMax: number;
}

export function getCurrentValue(card: Card): number {
  const multiplier = 1 + (card.mastery - 1) * 0.2;
  return Math.floor(card.baseValue * multiplier);
}

export function getUpgradeCost(card: Card): number {
  return 100 * card.mastery ** 2;
}

// ─── 플레이어 ───────────────────────────────────────────────
export interface PlayerStats {
  근골: number;
  심법: number;
  외공: number;
  경공: number;
  자질: number;
  행운: number;
}

export interface Player {
  name: string;
  stats: PlayerStats;
  hp: number;
  maxHp: number;
  energy: number;
  maxEnergy: number;
  energyRegen: number;
  attackPower: number;
  attackPowerBonus: number;
  baseDefense: number;
  defense: number;
  evasion: number;
  fleeChance: number;
  clashHpRegen: number;
  clashEnRegen: number;
  gold: number;
  xp: number;
  totalXp: number;
  enlightenmentIdx: number;
  winStreak: number;
  deck: Card[];
  hand: Card[];
  drawPile: Card[];
  discardPile: Card[];
  tempMaxEnergyBonus: number;
}

// ─── 적 의도 ────────────────────────────────────────────────
export type EnemyIntent =
  | "공격"
  | "강공"
  | "방어"
  | "약화"
  // 녹림 졸개
  | "돌팔매"
  | "주먹질"
  | "난도질"
  | "멱살잡이"
  // 녹림왕 마천광
  | "천악 부동체"
  | "살웅 괴력권"
  | "운기 조식"
  | "황산 대참"
  | "패왕의 포효"
  | "녹림 파천참"
  // 혈교
  | "독침"
  | "혈공"
  | "절식"
  | "혈마강타"
  | "불멸진"
  | "혈천만상"
  | "흡혈";

export type EnemyType =
  | "nokrim_minion"
  | "nokrim_captain"
  | "boss_macheon"
  | "hyulgyo_jaGaek"
  | "hyulgyo_gosu"
  | "hyulgyo_jangro";

export interface Enemy {
  type: EnemyType;
  name: string;
  hp: number;
  maxHp: number;
  atk: number;
  level: number;
  defense: number;
  intentQueue: EnemyIntent[];
  isOverloaded?: boolean;
  isImmovable?: boolean;
  isImmortal?: boolean;
  cycle?: number;
  specialMove?: string;
}

// ─── 전투 로그 ──────────────────────────────────────────────
export interface BattleLog {
  text: string;
  color: string; // tailwind color class
}

// ─── 객잔 버프 ──────────────────────────────────────────────
export interface InnBuff {
  type: "energy" | "maxHp" | "defense";
  val: number;
  name: string;
}

// ─── 화면(Screen) — 단일 진실 ────────────────────────────────
export type Screen =
  | "title"
  | "menu"
  | "battle"
  | "reward"
  | "inn"
  | "training"
  | "death"
  | "worldmap";

// ─── 챕터 ───────────────────────────────────────────────────
export interface ChapterInfo {
  chapter: number;
  name: string;
  range: [number, number];
  desc: string;
  enemies: EnemyType[];
}

export const CHAPTERS: Record<number, ChapterInfo> = {
  1: {
    chapter: 1,
    name: "제1장: 산중 표창",
    range: [1, 5],
    desc: "첩첩산중을 헤치며 처음 강호에 발을 딛다.",
    enemies: ["nokrim_minion", "nokrim_captain", "boss_macheon"],
  },
  2: {
    chapter: 2,
    name: "제2장: 녹림의 그늘",
    range: [6, 20],
    desc: "녹림왕 마천광의 영역. 산채 졸개들이 길을 막는다.",
    enemies: ["nokrim_minion", "nokrim_captain", "boss_macheon"],
  },
  3: {
    chapter: 3,
    name: "제3장: 혈교의 음모",
    range: [21, 999],
    desc: "혈교가 강호를 잠식하기 시작했다.",
    enemies: ["hyulgyo_jaGaek", "hyulgyo_gosu", "hyulgyo_jangro"],
  },
};

export function getChapter(encounter: number): ChapterInfo {
  for (const info of Object.values(CHAPTERS)) {
    const [lo, hi] = info.range;
    if (encounter >= lo && encounter <= hi) return info;
  }
  return CHAPTERS[3];
}
