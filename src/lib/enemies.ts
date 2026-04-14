import { Enemy, EnemyIntent, EnemyType, Player } from "./types";

// ─── 적 생성 ────────────────────────────────────────────────
function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const MINION_SPECIALS = ["난도질", "멱살잡이"] as const;

export function createEnemy(encounter: number): Enemy {
  // 5의 배수: 보스
  if (encounter % 5 === 0) {
    if (encounter <= 20) {
      return {
        type: "boss_macheon",
        name: "녹림왕 마천광",
        hp: 320,
        maxHp: 320,
        atk: 20,
        level: 10,
        defense: 0,
        intentQueue: [],
        isOverloaded: false,
        isImmovable: false,
        cycle: 0,
      };
    }
    return {
      type: "hyulgyo_jangro",
      name: "혈교 장로 혈마도",
      hp: 500,
      maxHp: 500,
      atk: 24,
      level: 15,
      defense: 0,
      intentQueue: [],
      isImmortal: false,
    };
  }

  // 3의 배수: 중간 적
  if (encounter % 3 === 0) {
    if (encounter <= 20) {
      return {
        type: "nokrim_captain",
        name: "녹림 행동대장",
        hp: 65,
        maxHp: 65,
        atk: 10,
        level: 3,
        defense: 0,
        intentQueue: [],
      };
    }
    return {
      type: "hyulgyo_gosu",
      name: "혈교 고수",
      hp: 90,
      maxHp: 90,
      atk: 16,
      level: 5,
      defense: 0,
      intentQueue: [],
    };
  }

  // 일반: 졸개
  if (encounter <= 20) {
    const special = MINION_SPECIALS[
      Math.floor(Math.random() * MINION_SPECIALS.length)
    ] as EnemyIntent;
    return {
      type: "nokrim_minion",
      name: "산채 졸개",
      hp: 40,
      maxHp: 40,
      atk: 7,
      level: 1,
      defense: 0,
      intentQueue: [],
      specialMove: special,
    };
  }
  return {
    type: "hyulgyo_jaGaek",
    name: "혈교 자객",
    hp: 55,
    maxHp: 55,
    atk: 13,
    level: 3,
    defense: 0,
    intentQueue: [],
  };
}

// ─── 티어 기반 적 생성 (월드맵용) ───────────────────────────
export function createEnemyByTier(tier: number): Enemy {
  if (tier >= 5) {
    return { type: "boss_macheon", name: "녹림왕 마천광", hp: 320, maxHp: 320, atk: 20, level: 10, defense: 0, intentQueue: [], isOverloaded: false, isImmovable: false, cycle: 0 };
  }
  if (tier >= 3) {
    return { type: "nokrim_captain", name: "녹림 행동대장", hp: 65, maxHp: 65, atk: 10, level: 3, defense: 0, intentQueue: [] };
  }
  if (tier >= 2) {
    return { type: "nokrim_captain", name: "녹림 행동대장", hp: 65, maxHp: 65, atk: 10, level: 3, defense: 0, intentQueue: [] };
  }
  const special = MINION_SPECIALS[Math.floor(Math.random() * MINION_SPECIALS.length)] as EnemyIntent;
  return { type: "nokrim_minion", name: "산채 졸개", hp: 40, maxHp: 40, atk: 7, level: 1, defense: 0, intentQueue: [], specialMove: special };
}

// ─── 의도 생성 ──────────────────────────────────────────────
export function refreshIntents(enemy: Enemy): Enemy {
  const e = { ...enemy, intentQueue: [] as EnemyIntent[] };

  switch (e.type) {
    case "nokrim_minion": {
      const special = (e.specialMove || "난도질") as EnemyIntent;
      const template: EnemyIntent[] = [
        "돌팔매", "주먹질", "주먹질", special, "주먹질",
      ];
      e.intentQueue = shuffle(template);
      break;
    }
    case "nokrim_captain": {
      const pool: EnemyIntent[] = ["공격", "방어", "공격", "공격", "약화"];
      e.intentQueue = shuffle(pool);
      break;
    }
    case "boss_macheon": {
      const cycle = e.cycle ?? 0;
      if (cycle === 0) {
        e.intentQueue = [
          "천악 부동체",
          "살웅 괴력권",
          "운기 조식",
          "황산 대참",
          "녹림 파천참",
        ];
      } else {
        e.intentQueue = shuffle([
          "천악 부동체",
          "패왕의 포효",
          "운기 조식",
          "살웅 괴력권",
          "녹림 파천참",
        ]);
      }
      e.cycle = cycle + 1;
      break;
    }
    case "hyulgyo_jaGaek": {
      e.intentQueue = shuffle(["공격", "강공", "약화", "공격", "독침"]);
      break;
    }
    case "hyulgyo_gosu": {
      e.intentQueue = shuffle(["혈공", "혈공", "공격", "방어", "절식"]);
      break;
    }
    case "hyulgyo_jangro": {
      e.intentQueue = shuffle<EnemyIntent>([
        "혈마강타", "혈마강타", "불멸진", "혈천만상", "공격", "방어", "흡혈",
      ]).slice(0, 5);
      break;
    }
    default: {
      e.intentQueue = shuffle(["공격", "방어", "강공", "공격", "약화"]);
    }
  }

  return e;
}

// ─── 적 의도 실행 ───────────────────────────────────────────
function applyDamageToPlayer(player: Player, dmg: number): [Player, number] {
  // 회피 판정
  if (Math.random() < player.evasion) {
    return [player, 0];
  }
  const actual = Math.max(0, dmg - player.defense);
  const newDef = Math.max(0, player.defense - dmg);
  const newHp = Math.max(0, player.hp - actual);
  return [{ ...player, defense: newDef, hp: newHp }, actual];
}

export function executeEnemyIntent(
  intent: EnemyIntent,
  enemy: Enemy,
  player: Player
): { enemy: Enemy; player: Player; message: string } {
  let e = { ...enemy };
  let p = { ...player };
  let msg = "";

  const randInt = (min: number, max: number) =>
    Math.floor(Math.random() * (max - min + 1)) + min;

  switch (intent) {
    // 기본
    case "공격": {
      const dmg = e.atk + randInt(-1, 2);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = actual > 0
        ? `혈풍 같은 일격! (피해 ${actual})`
        : `일격을 피했다!`;
      break;
    }
    case "강공": {
      const dmg = Math.floor(e.atk * 1.5);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `패왕의 기세! (피해 ${actual})`;
      break;
    }
    case "방어": {
      const defVal = e.atk + randInt(3, 7);
      e.defense += defVal;
      msg = `철벽의 호신강기 (방어 +${defVal})`;
      break;
    }
    case "약화": {
      const drain = 2;
      p = { ...p, energy: Math.max(0, p.energy - drain) };
      msg = `탁한 기운이 내공을 ${drain} 흩뜨린다.`;
      break;
    }

    // 녹림 졸개
    case "돌팔매": {
      const dmg = Math.max(1, e.atk - 3) + randInt(0, 2);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `돌을 집어 던진다! (피해 ${actual})`;
      break;
    }
    case "주먹질": {
      const dmg = e.atk + randInt(-1, 2);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `거친 주먹이 턱을 노린다! (피해 ${actual})`;
      break;
    }
    case "난도질": {
      const dmg = e.atk + 4;
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `어설픈 도날이 허공을 찢는다! (피해 ${actual})`;
      break;
    }
    case "멱살잡이": {
      p = { ...p, energy: Math.max(0, p.energy - 1) };
      const dmg = Math.max(1, Math.floor(e.atk / 2));
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `멱살을 잡고 균형을 무너뜨린다! (내공 -1, 피해 ${actual})`;
      break;
    }

    // 녹림왕
    case "천악 부동체": {
      e.isImmovable = true;
      if (!e.isOverloaded) {
        const defVal = 30 + e.level * 2;
        e.defense += defVal;
        msg = `천악 부동체! 강기 +${defVal}, 피해 경감 12`;
      } else {
        msg = `부동체를 취하려 했으나 과부하로 자세가 무너진다!`;
      }
      break;
    }
    case "살웅 괴력권": {
      const dmg = e.atk + 8;
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `살웅 괴력권! (피해 ${actual})`;
      break;
    }
    case "운기 조식": {
      e.hp = Math.min(e.maxHp, e.hp + 30);
      e.isImmovable = false;
      msg = `운기 조식 (기혈 +30) — 빈틈!`;
      break;
    }
    case "황산 대참": {
      const dmg = Math.floor(e.atk * 1.6);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `황산 대참! (피해 ${actual})`;
      break;
    }
    case "패왕의 포효": {
      p = { ...p, energy: Math.max(0, p.energy - 3) };
      msg = `패왕의 포효! 내공 3 흩어짐`;
      break;
    }
    case "녹림 파천참": {
      const dmg = e.atk * 3;
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `녹림 파천참! 하늘을 가르는 섬광! (피해 ${actual})`;
      break;
    }

    // 혈교
    case "독침": {
      p = { ...p, energy: Math.max(0, p.energy - 3) };
      const dmg = Math.floor(e.atk * 0.6);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `독침! 기혈 -${actual}, 내공 -3`;
      break;
    }
    case "혈공": {
      const dmg = Math.floor(e.atk * 1.4);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `혈공! (피해 ${actual})`;
      break;
    }
    case "절식": {
      const defVal = e.atk + 15;
      e.defense += defVal;
      msg = `절식! 호신강기 +${defVal}`;
      break;
    }
    case "혈마강타": {
      const dmg = e.atk + 10;
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      msg = `혈마강타! (피해 ${actual})`;
      break;
    }
    case "불멸진": {
      e.isImmortal = true;
      e.defense += 40;
      msg = `불멸진! 피해 20 감소, 강기 +40`;
      break;
    }
    case "혈천만상": {
      const dmg = e.atk * 2;
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = { ...np, energy: Math.max(0, np.energy - 4) };
      msg = `혈천만상! 피해 ${actual}, 내공 -4`;
      break;
    }
    case "흡혈": {
      const dmg = Math.floor(e.atk * 0.8);
      const [np, actual] = applyDamageToPlayer(p, dmg);
      p = np;
      const heal = Math.floor(actual / 2);
      e.hp = Math.min(e.maxHp, e.hp + heal);
      msg = `흡혈! 피해 ${actual}, 적 회복 ${heal}`;
      break;
    }

    default:
      msg = `${e.name}: ${intent}`;
  }

  return { enemy: e, player: p, message: msg };
}

// ─── 적 의도 표시 이름 매핑 ─────────────────────────────────
export const INTENT_DISPLAY: Record<string, { icon: string; color: string }> = {
  공격: { icon: "⚔️", color: "text-red-400" },
  강공: { icon: "💥", color: "text-red-600" },
  방어: { icon: "🛡️", color: "text-blue-400" },
  약화: { icon: "☠️", color: "text-purple-400" },
  돌팔매: { icon: "🪨", color: "text-yellow-600" },
  주먹질: { icon: "👊", color: "text-red-400" },
  난도질: { icon: "🔪", color: "text-red-500" },
  멱살잡이: { icon: "🤜", color: "text-orange-400" },
  "천악 부동체": { icon: "🏔️", color: "text-gray-400" },
  "살웅 괴력권": { icon: "🐻", color: "text-red-500" },
  "운기 조식": { icon: "🧘", color: "text-green-400" },
  "황산 대참": { icon: "⚡", color: "text-yellow-500" },
  "패왕의 포효": { icon: "📢", color: "text-purple-500" },
  "녹림 파천참": { icon: "🌟", color: "text-yellow-300" },
  독침: { icon: "🧪", color: "text-green-600" },
  혈공: { icon: "🩸", color: "text-red-600" },
  절식: { icon: "🛡️", color: "text-blue-500" },
  혈마강타: { icon: "👹", color: "text-red-700" },
  불멸진: { icon: "🔥", color: "text-orange-600" },
  혈천만상: { icon: "🌊", color: "text-red-800" },
  흡혈: { icon: "🧛", color: "text-purple-700" },
};

// 예상 데미지 추정 — UI 표시용 (랜덤 변동은 평균치로)
// executeEnemyIntent 의 데미지 공식과 동기화. null = 비공격(버프/디버프)
export function estimateIntentDamage(intent: string, atk: number): number | null {
  switch (intent) {
    case "공격": return atk;                       // atk + randInt(-1, 2) → 평균
    case "강공": return Math.floor(atk * 1.5);
    case "주먹질": return atk;
    case "돌팔매": return Math.max(1, atk - 2);
    case "난도질": return atk + 4;
    case "멱살잡이": return Math.max(1, Math.floor(atk / 2));
    case "살웅 괴력권": return atk + 8;
    case "황산 대참": return Math.floor(atk * 1.6);
    case "녹림 파천참": return atk * 3;
    case "독침": return Math.floor(atk * 0.6);
    case "혈공": return Math.floor(atk * 1.4);
    case "혈마강타": return atk + 10;
    case "혈천만상": return atk * 2;
    case "흡혈": return Math.floor(atk * 0.8);
    default: return null;
  }
}
