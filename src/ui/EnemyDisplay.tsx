"use client";

import { Enemy } from "@/lib/types";
import { INTENT_DISPLAY, estimateIntentDamage } from "@/lib/enemies";
import HealthBar from "./HealthBar";

interface Props {
  enemy: Enemy;
  clashIndex: number;
  compact?: boolean; // 전투 화면 상단 고정용 축약 레이아웃
}

export default function EnemyDisplay({ enemy, compact }: Props) {
  const currentIntent = enemy.intentQueue[0];
  const intentInfo = currentIntent
    ? INTENT_DISPLAY[currentIntent] || { icon: "❓", color: "text-gray-300" }
    : null;

  const enemyEmoji: Record<string, string> = {
    nokrim_minion: "🥷",
    nokrim_captain: "⚔️",
    boss_macheon: "👹",
    hyulgyo_jaGaek: "🗡️",
    hyulgyo_gosu: "🩸",
    hyulgyo_jangro: "😈",
  };
  const emoji = enemyEmoji[enemy.type] || "👤";

  // 예상 데미지 (null = 비공격)
  const estDmg = currentIntent ? estimateIntentDamage(currentIntent, enemy.atk) : null;
  const isAttack = estDmg !== null;

  // ── compact: 전투 화면용 가로 레이아웃 ────────────
  if (compact) {
    return (
      <div className="w-full max-w-md mx-auto bg-gray-900/50 rounded-xl border border-gray-700 p-2">
        <div className="flex items-start gap-3">
          <div className="text-4xl shrink-0 leading-none">{emoji}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-base font-bold text-red-300 truncate">{enemy.name}</h2>
              <span className="text-[11px] text-gray-200 shrink-0">Lv.{enemy.level}</span>
            </div>
            <div className="mt-1">
              <HealthBar
                current={enemy.hp}
                max={enemy.maxHp}
                label="기혈"
                color="bg-red-600"
                showDefense={enemy.defense}
              />
            </div>
            {/* 다음 의도 — 강조 박스 (공격은 빨강 펄스, 비공격은 파랑) */}
            {intentInfo && currentIntent && (
              <div
                className={`mt-1.5 flex items-center justify-between gap-2 rounded-md px-2 py-1 border ${
                  isAttack
                    ? "bg-red-950/60 border-red-600 animate-pulse"
                    : "bg-blue-950/50 border-blue-700"
                }`}
              >
                <div className={`flex items-center gap-1.5 ${intentInfo.color} min-w-0`}>
                  <span className="text-2xl leading-none shrink-0">{intentInfo.icon}</span>
                  <span className="text-sm font-bold truncate">{currentIntent}</span>
                </div>
                {isAttack && (
                  <span className="text-base font-extrabold text-red-300 shrink-0 tabular-nums">
                    −{estDmg}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 상태 뱃지 + 남은 의도 큐 */}
        {(enemy.isOverloaded || enemy.isImmovable || enemy.isImmortal || enemy.intentQueue.length > 1) && (
          <div className="mt-1.5 flex items-center justify-between gap-2">
            <div className="flex gap-1 flex-wrap">
              {enemy.isOverloaded && (
                <span className="text-[11px] bg-red-900 text-red-200 px-1.5 py-0.5 rounded">근육과부하</span>
              )}
              {enemy.isImmovable && (
                <span className="text-[11px] bg-gray-700 text-gray-200 px-1.5 py-0.5 rounded">천악부동체</span>
              )}
              {enemy.isImmortal && (
                <span className="text-[11px] bg-orange-900 text-orange-200 px-1.5 py-0.5 rounded">불멸진</span>
              )}
            </div>
            {enemy.intentQueue.length > 1 && (
              <div className="flex gap-1">
                {enemy.intentQueue.slice(0, 5).map((intent, i) => {
                  const info = INTENT_DISPLAY[intent] || { icon: "❓", color: "text-gray-300" };
                  return (
                    <div
                      key={i}
                      className={`w-6 h-6 rounded flex items-center justify-center text-[11px]
                        ${i === 0 ? "bg-gray-700 ring-1 ring-amber-400" : "bg-gray-800"}
                      `}
                      title={intent}
                    >
                      {i === 0 ? info.icon : "?"}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── 기존 full 레이아웃 (다른 화면 호환) ────────────
  return (
    <div className="flex flex-col items-center gap-3 w-full max-w-md">
      <div className="text-center">
        <div className="text-5xl mb-2">{emoji}</div>
        <h2 className="text-xl font-bold text-red-400">{enemy.name}</h2>
        <div className="text-xs text-gray-300">Lv.{enemy.level}</div>
      </div>

      <div className="flex gap-2">
        {enemy.isOverloaded && (
          <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded">근육 과부하</span>
        )}
        {enemy.isImmovable && (
          <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">천악부동체</span>
        )}
        {enemy.isImmortal && (
          <span className="text-xs bg-orange-900 text-orange-300 px-2 py-0.5 rounded">불멸진</span>
        )}
      </div>

      <div className="w-full">
        <HealthBar current={enemy.hp} max={enemy.maxHp} label="기혈" color="bg-red-600" showDefense={enemy.defense} />
      </div>

      {intentInfo && currentIntent && (
        <div className={`text-sm ${intentInfo.color} bg-gray-900/60 px-4 py-2 rounded-lg border border-gray-700`}>
          다음 수: {intentInfo.icon} {currentIntent}
        </div>
      )}

      <div className="flex gap-1">
        {enemy.intentQueue.map((intent, i) => {
          const info = INTENT_DISPLAY[intent] || { icon: "❓", color: "text-gray-300" };
          return (
            <div
              key={i}
              className={`w-8 h-8 rounded flex items-center justify-center text-sm
                ${i === 0 ? "bg-gray-700 ring-2 ring-yellow-500" : "bg-gray-800"}
              `}
              title={intent}
            >
              {i === 0 ? info.icon : "?"}
            </div>
          );
        })}
      </div>
    </div>
  );
}
