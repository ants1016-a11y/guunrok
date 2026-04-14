"use client";

import { Player } from "@/lib/types";
import HealthBar from "./HealthBar";

interface Props {
  player: Player;
  compact?: boolean; // 전투 하단 고정 영역용 한 줄 요약 레이아웃
}

export default function PlayerPanel({ player, compact }: Props) {
  // ── compact: 전투 화면 하단 고정용 ────────────
  if (compact) {
    return (
      <div className="w-full max-w-md mx-auto bg-gray-900/50 rounded-lg border border-gray-700 px-3 py-2">
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2 min-w-0">
            <div className="text-2xl leading-none shrink-0">🧑‍🦳</div>
            <h3 className="text-sm font-bold text-amber-300 truncate">{player.name}</h3>
          </div>
          <div className="text-[11px] text-gray-300 shrink-0">
            연승 {player.winStreak} · 금자 {player.gold}
          </div>
        </div>
        <HealthBar
          current={player.hp}
          max={player.maxHp}
          label="기혈"
          color="bg-red-500"
          showDefense={player.defense}
        />
      </div>
    );
  }

  // ── 기존 full 레이아웃 ────────────
  return (
    <div className="w-full max-w-md bg-gray-900/60 rounded-xl border border-gray-700 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="text-3xl">🧑‍🦳</div>
        <div>
          <h3 className="text-lg font-bold text-amber-300">{player.name}</h3>
          <div className="text-[13px] text-gray-300">
            연승 {player.winStreak} · 금자 {player.gold} · 명성 {player.xp}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <HealthBar
          current={player.hp}
          max={player.maxHp}
          label="기혈"
          color="bg-red-500"
          showDefense={player.defense}
        />

        {/* 내공 바 */}
        <div className="w-full">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-200">내공</span>
            <span className="text-white font-mono">
              {player.energy}/{player.maxEnergy}
            </span>
          </div>
          <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden border border-gray-600">
            <div
              className="h-full bg-blue-500 transition-all duration-500 ease-out rounded-full"
              style={{
                width: `${Math.min(100, (player.energy / player.maxEnergy) * 100)}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* 스탯 */}
      <div className="grid grid-cols-3 gap-1 mt-3 text-[13px] text-gray-300">
        {Object.entries(player.stats).map(([key, val]) => (
          <div key={key} className="text-center">
            <span className="text-gray-300">{key}</span>{" "}
            <span className="text-white font-semibold">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
