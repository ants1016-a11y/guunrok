"use client";

import { Enemy } from "@/lib/types";
import { INTENT_DISPLAY } from "@/lib/enemies";
import HealthBar from "./HealthBar";

interface Props {
  enemy: Enemy;
  clashIndex: number;
}

export default function EnemyDisplay({ enemy, clashIndex }: Props) {
  const currentIntent = enemy.intentQueue[0];
  const intentInfo = currentIntent
    ? INTENT_DISPLAY[currentIntent] || { icon: "❓", color: "text-gray-400" }
    : null;

  // 적 타입별 이모지
  const enemyEmoji: Record<string, string> = {
    nokrim_minion: "🥷",
    nokrim_captain: "⚔️",
    boss_macheon: "👹",
    hyulgyo_jaGaek: "🗡️",
    hyulgyo_gosu: "🩸",
    hyulgyo_jangro: "😈",
  };

  const emoji = enemyEmoji[enemy.type] || "👤";

  return (
    <div className="flex flex-col items-center gap-3 w-full max-w-md">
      {/* 적 이름 + 상태 */}
      <div className="text-center">
        <div className="text-5xl mb-2">{emoji}</div>
        <h2 className="text-xl font-bold text-red-400">{enemy.name}</h2>
        <div className="text-xs text-gray-500">Lv.{enemy.level}</div>
      </div>

      {/* 상태 뱃지 */}
      <div className="flex gap-2">
        {enemy.isOverloaded && (
          <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded">
            근육 과부하
          </span>
        )}
        {enemy.isImmovable && (
          <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
            천악부동체
          </span>
        )}
        {enemy.isImmortal && (
          <span className="text-xs bg-orange-900 text-orange-300 px-2 py-0.5 rounded">
            불멸진
          </span>
        )}
      </div>

      {/* HP */}
      <div className="w-full">
        <HealthBar
          current={enemy.hp}
          max={enemy.maxHp}
          label="기혈"
          color="bg-red-600"
          showDefense={enemy.defense}
        />
      </div>

      {/* 다음 의도 */}
      {intentInfo && currentIntent && (
        <div
          className={`text-sm ${intentInfo.color} bg-gray-900/60 px-4 py-2 rounded-lg border border-gray-700`}
        >
          다음 수: {intentInfo.icon} {currentIntent}
        </div>
      )}

      {/* 남은 의도 표시 */}
      <div className="flex gap-1">
        {enemy.intentQueue.map((intent, i) => {
          const info = INTENT_DISPLAY[intent] || {
            icon: "❓",
            color: "text-gray-500",
          };
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
