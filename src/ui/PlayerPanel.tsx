"use client";

import { Player } from "@/lib/types";
import HealthBar from "./HealthBar";

interface Props {
  player: Player;
}

export default function PlayerPanel({ player }: Props) {
  return (
    <div className="w-full max-w-md bg-gray-900/60 rounded-xl border border-gray-700 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="text-3xl">🧑‍🦳</div>
        <div>
          <h3 className="text-lg font-bold text-amber-300">{player.name}</h3>
          <div className="text-xs text-gray-400">
            연승 {player.winStreak} | 금자 {player.gold} | 명성 {player.xp}
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
            <span className="text-gray-300">내공</span>
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
      <div className="grid grid-cols-3 gap-1 mt-3 text-xs text-gray-400">
        {Object.entries(player.stats).map(([key, val]) => (
          <div key={key} className="text-center">
            <span className="text-gray-500">{key}</span>{" "}
            <span className="text-white">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
