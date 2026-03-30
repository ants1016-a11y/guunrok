"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { InnBuff } from "@/lib/types";

const REST_MENUS = [
  { label: "쪽잠 (50%)", ratio: 0.5, cost: 15 },
  { label: "숙면 (100%)", ratio: 1.0, cost: 30 },
];

const FOOD_MENUS: { name: string; desc: string; cost: number; buff: InnBuff }[] = [
  { name: "죽엽청", desc: "전투 시작 내공 +2", cost: 10, buff: { type: "energy", val: 2, name: "죽엽청" } },
  { name: "장육", desc: "최대 체력 +30", cost: 20, buff: { type: "maxHp", val: 30, name: "장육" } },
  { name: "용정차", desc: "합 시작 방어 +3", cost: 10, buff: { type: "defense", val: 3, name: "용정차" } },
];

export default function InnPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  useEffect(() => {
    if (state.phase !== "inn") {
      if (state.phase === "world") router.push("/world");
      else if (state.phase === "title") router.push("/");
    }
  }, [state.phase, router]);

  if (!state.player || state.phase !== "inn") return null;

  const { player, innBuff } = state;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-green-950/10 to-gray-950 text-white">
      {/* 헤더 */}
      <div className="text-center py-6 bg-gray-900/80 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-amber-400">🏮 객잔</h1>
        <p className="text-sm text-gray-400 mt-1">
          기혈 {player.hp}/{player.maxHp} | 금자 {player.gold}
          {innBuff && <span className="text-emerald-400 ml-2">식사: {innBuff.name}</span>}
        </p>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-6">
        {/* 투숙 */}
        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-bold text-amber-300 mb-4">투숙 (기혈 회복)</h2>
          <div className="grid grid-cols-2 gap-3">
            {REST_MENUS.map((menu, i) => {
              const canBuy = player.gold >= menu.cost && player.hp < player.maxHp;
              return (
                <button
                  key={i}
                  disabled={!canBuy}
                  onClick={() => dispatch({ type: "INN_REST", ratio: menu.ratio, cost: menu.cost })}
                  className={`p-4 rounded-lg border text-center transition-colors ${
                    canBuy
                      ? "bg-gray-800 border-amber-700/50 hover:bg-gray-700 cursor-pointer"
                      : "bg-gray-900 border-gray-800 opacity-40 cursor-not-allowed"
                  }`}
                >
                  <div className="text-sm font-bold text-white">{menu.label}</div>
                  <div className="text-xs text-amber-400 mt-1">{menu.cost}냥</div>
                  {player.hp >= player.maxHp && (
                    <div className="text-xs text-gray-500 mt-1">기혈 충만</div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* 식사 */}
        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-bold text-emerald-300 mb-2">식사 및 반주</h2>
          <p className="text-xs text-gray-500 mb-4">
            {innBuff ? `이미 ${innBuff.name}을(를) 먹었습니다. (다음 전투에 적용)` : "하나를 골라 다음 전투에 대비합니다."}
          </p>
          <div className="flex flex-col gap-3">
            {FOOD_MENUS.map((food, i) => {
              const canEat = player.gold >= food.cost && !innBuff;
              return (
                <button
                  key={i}
                  disabled={!canEat}
                  onClick={() => dispatch({ type: "INN_EAT", buff: food.buff, cost: food.cost })}
                  className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                    canEat
                      ? "bg-gray-800 border-emerald-700/50 hover:bg-gray-700 cursor-pointer"
                      : "bg-gray-900 border-gray-800 opacity-40 cursor-not-allowed"
                  }`}
                >
                  <div className="text-left">
                    <div className="text-sm font-bold text-white">{food.name}</div>
                    <div className="text-xs text-gray-400">{food.desc}</div>
                  </div>
                  <div className="text-sm text-amber-400 font-bold">{food.cost}냥</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 이탈 버튼 */}
        <div className="flex gap-3">
          <button
            onClick={() => {
              dispatch({ type: "LEAVE_INN_TO_BATTLE" });
              router.push("/world");
            }}
            className="flex-1 py-3 bg-amber-800 hover:bg-amber-700 rounded-lg text-lg font-bold transition-colors"
          >
            유랑을 계속한다
          </button>
          <button
            onClick={() => {
              dispatch({ type: "LEAVE_INN_TO_WORLD" });
              router.push("/world");
            }}
            className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg font-bold transition-colors"
          >
            강호 대지로
          </button>
        </div>
      </div>
    </div>
  );
}
