import { Card, CardType, Player, Enemy, getCurrentValue } from "./types";
import { calcCardPower } from "./formulas";

// ─── 카드 효과 함수 ─────────────────────────────────────────
type EffectFn = (
  player: Player,
  enemy: Enemy,
  card: Card
) => { player: Player; enemy: Enemy; message: string };

const CRIT_MULTIPLIER = 1.5;

function applyDamageToEnemy(enemy: Enemy, amount: number): [Enemy, number] {
  const isImmortal = enemy.isImmortal;
  const effective = isImmortal ? Math.max(0, amount - 20) : amount;
  const actual = Math.max(0, effective - enemy.defense);
  const newDef = Math.max(0, enemy.defense - effective);
  const newHp = Math.max(0, enemy.hp - actual);

  let e = { ...enemy, defense: newDef, hp: newHp };

  // 녹림왕 과부하 체크
  if (
    e.type === "boss_macheon" &&
    !e.isOverloaded &&
    e.hp <= e.maxHp * 0.4
  ) {
    e = {
      ...e,
      isOverloaded: true,
      atk: Math.floor(e.atk * 1.8),
      defense: 0,
      isImmovable: false,
    };
  }

  return [e, actual];
}

// ─── 기본 5종 무공 + 기초 3종 ───────────────────────────────
const effects: Record<string, EffectFn> = {
  // 기초 (UI 버튼용, 비용 0)
  "기본 공격": (p, e, _c) => {
    const dmg = 5 + p.attackPowerBonus;
    const [ne, actual] = applyDamageToEnemy(e, dmg);
    return { player: p, enemy: ne, message: `기본 공격: ${actual}의 피해` };
  },
  "기본 방어": (p, e, _c) => {
    const np = { ...p, defense: p.defense + 5 };
    return { player: np, enemy: e, message: `기본 방어: 호신강기 +5` };
  },
  운기조식: (p, e, _c) => {
    const np = { ...p, energy: Math.min(p.maxEnergy, p.energy + 2) };
    return { player: np, enemy: e, message: `운기조식: 내공 2 회복` };
  },

  // 정예 5대 초식
  삼재공: (p, e, card) => {
    const breakthrough = 1 + Math.floor(card.mastery / 3);
    const newBonus = p.tempMaxEnergyBonus + breakthrough;
    const np = {
      ...p,
      tempMaxEnergyBonus: newBonus,
      maxEnergy: p.maxEnergy + breakthrough,
      energy: Math.min(p.maxEnergy + breakthrough, p.energy + breakthrough),
    };
    return {
      player: np,
      enemy: e,
      message: `삼재공 돌파! 내공 그릇이 ${breakthrough} 커졌습니다.`,
    };
  },
  육합권: (p, e, card) => {
    const dmg = calcCardPower(card, p.stats);
    const [ne, actual] = applyDamageToEnemy(e, dmg);
    return { player: p, enemy: ne, message: `육합권: ${actual}의 피해!` };
  },
  포천삼: (p, e, card) => {
    const base = calcCardPower(card, p.stats);
    const defense = base + Math.floor(Math.random() * 5);
    const np = { ...p, defense: p.defense + defense };
    return {
      player: np,
      enemy: e,
      message: `포천삼: 호신강기 +${defense}`,
    };
  },
  복호장: (p, e, card) => {
    const dmg = calcCardPower(card, p.stats);
    const [ne, actual] = applyDamageToEnemy(e, dmg);
    return {
      player: p,
      enemy: ne,
      message: `복호장: ${actual}의 파괴적 피해!`,
    };
  },
  유운지: (p, e, card) => {
    const debuff = calcCardPower(card, p.stats);
    const ne = { ...e, atk: Math.max(1, e.atk - debuff) };
    return {
      player: p,
      enemy: ne,
      message: `유운지: 적 공격력 ${debuff} 감소!`,
    };
  },

  // 고급 무공
  용호권: (p, e, card) => {
    const hit = Math.floor(calcCardPower(card, p.stats) * 0.6);
    const [e1, a1] = applyDamageToEnemy(e, hit);
    const [e2, a2] = applyDamageToEnemy(e1, hit);
    return {
      player: p,
      enemy: e2,
      message: `용호권: 연속 이격! 합계 ${a1 + a2}의 피해!`,
    };
  },
  철사장: (p, e, card) => {
    const defGain = calcCardPower(card, p.stats);
    const strip = Math.floor(defGain * 0.5);
    const np = { ...p, defense: p.defense + defGain };
    const ne = { ...e, defense: Math.max(0, e.defense - strip) };
    return {
      player: np,
      enemy: ne,
      message: `철사장: 호신강기 +${defGain}, 적 강기 ${strip} 분쇄`,
    };
  },
  내가일소: (p, e, card) => {
    const heal = calcCardPower(card, p.stats);
    const actual = Math.min(heal, p.maxHp - p.hp);
    const np = { ...p, hp: Math.min(p.maxHp, p.hp + heal) };
    return { player: np, enemy: e, message: `내가일소: 기혈 ${actual} 회복` };
  },
  점혈타: (p, e, card) => {
    const debuff = calcCardPower(card, p.stats);
    const ne = { ...e, atk: Math.max(1, e.atk - debuff), defense: 0 };
    return {
      player: p,
      enemy: ne,
      message: `점혈타: 적 공격력 -${debuff}, 방어 자세 파괴!`,
    };
  },
  비연보: (p, e, card) => {
    const defGain = calcCardPower(card, p.stats);
    const np = {
      ...p,
      energy: Math.min(p.maxEnergy, p.energy + 2),
      defense: p.defense + defGain,
    };
    return {
      player: np,
      enemy: e,
      message: `비연보: 내공 +2, 호신강기 +${defGain}`,
    };
  },

  // 녹림 보스 드랍 비급
  녹림패도법: (p, e, card) => {
    const shatter = Math.min(e.defense, 15);
    const ne1 = { ...e, defense: Math.max(0, e.defense - 15) };
    const dmg = calcCardPower(card, p.stats);
    const [ne2, actual] = applyDamageToEnemy(ne1, dmg);
    return {
      player: p,
      enemy: ne2,
      message:
        shatter > 0
          ? `녹림패도법: 방어 ${shatter} 파쇄 후 ${actual}의 피해!`
          : `녹림패도법: ${actual}의 피해!`,
    };
  },
  천근추: (p, e, card) => {
    const defVal = calcCardPower(card, p.stats) + Math.floor(e.atk / 2);
    const np = { ...p, defense: p.defense + defVal };
    return {
      player: np,
      enemy: e,
      message: `천근추: 호신강기 ${defVal} 획득`,
    };
  },
  산악붕: (p, e, card) => {
    const hit = Math.floor(calcCardPower(card, p.stats) / 2);
    const [e1, a1] = applyDamageToEnemy(e, hit);
    const [e2, a2] = applyDamageToEnemy(e1, hit);
    return {
      player: p,
      enemy: e2,
      message: `산악붕: 2타 연격! 합계 ${a1 + a2}의 피해!`,
    };
  },
};

export function executeCardEffect(
  cardName: string,
  player: Player,
  enemy: Enemy,
  card: Card,
  isCrit: boolean
): { player: Player; enemy: Enemy; message: string } {
  const fn = effects[cardName];
  if (!fn) {
    return { player, enemy, message: `[알 수 없는 초식: ${cardName}]` };
  }

  // 치명타 시 baseValue를 임시로 올림
  const origBase = card.baseValue;
  if (isCrit) {
    card = {
      ...card,
      baseValue: Math.floor(getCurrentValue(card) * CRIT_MULTIPLIER),
    };
  }

  const result = fn({ ...player }, { ...enemy }, card);
  card.baseValue = origBase;
  return result;
}

// ─── 카드 데이터 정의 ───────────────────────────────────────
export const CARD_DEFS: Record<
  string,
  { type: CardType; cost: number; desc: string; baseValue: number }
> = {
  복호장: { type: "공격", cost: 4, desc: "18~25의 파괴적 피해", baseValue: 18 },
  육합권: { type: "공격", cost: 2, desc: "8~12의 무작위 피해", baseValue: 12 },
  포천삼: { type: "방어", cost: 2, desc: "8~12의 호신강기", baseValue: 8 },
  삼재공: { type: "기술", cost: 1, desc: "내공 그릇 확장", baseValue: 1 },
  유운지: { type: "기술", cost: 3, desc: "적 공격력 5 감소", baseValue: 5 },
  // 고급
  용호권: {
    type: "공격",
    cost: 3,
    desc: "연속 이격 (각 60% × 2회)",
    baseValue: 20,
  },
  철사장: {
    type: "방어",
    cost: 3,
    desc: "방어 + 적 강기 분쇄",
    baseValue: 14,
  },
  내가일소: { type: "기술", cost: 2, desc: "기혈 회복", baseValue: 15 },
  점혈타: {
    type: "약화",
    cost: 2,
    desc: "적 공격력 감소 + 방어 자세 파괴",
    baseValue: 6,
  },
  비연보: {
    type: "기술",
    cost: 1,
    desc: "내공 회복 + 방어도 획득",
    baseValue: 6,
  },
  // 보스 드랍
  녹림패도법: {
    type: "공격",
    cost: 3,
    desc: "방어 15 파쇄 후 강타",
    baseValue: 20,
  },
  천근추: {
    type: "방어",
    cost: 2,
    desc: "기본 방어 + 적 공격력/2 강기",
    baseValue: 12,
  },
  산악붕: { type: "공격", cost: 3, desc: "2타 연격", baseValue: 18 },
};

export const BASIC_ACTIONS: Card[] = [
  {
    id: "basic_attack",
    name: "기본 공격",
    type: "공격",
    cost: 0,
    description: "기초적인 타격 (5+보너스)",
    baseValue: 5,
    mastery: 1,
    masteryMax: 1,
  },
  {
    id: "basic_defense",
    name: "기본 방어",
    type: "방어",
    cost: 0,
    description: "기초 방어 (호신강기 +5)",
    baseValue: 5,
    mastery: 1,
    masteryMax: 1,
  },
  {
    id: "meditation",
    name: "운기조식",
    type: "기술",
    cost: 0,
    description: "내공 2 회복",
    baseValue: 0,
    mastery: 1,
    masteryMax: 1,
  },
];

export function createCard(name: string): Card {
  const def = CARD_DEFS[name];
  if (!def) throw new Error(`Unknown card: ${name}`);
  return {
    id: `${name}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    name,
    type: def.type,
    cost: def.cost,
    description: def.desc,
    baseValue: def.baseValue,
    mastery: 1,
    masteryMax: 5,
  };
}

export function createStarterDeck(): Card[] {
  return ["복호장", "육합권", "포천삼", "삼재공", "유운지"].map(createCard);
}
