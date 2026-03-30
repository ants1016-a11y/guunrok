"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getCurrentValue } from "@/lib/types";

const CARD_UPGRADE_BASE = 100;
const CARD_MASTERY_MAX = 12;
const STAT_MAX = 30;

const STAT_INFO: { key: string; label: string; desc: string }[] = [
  { key: "근골", label: "근골", desc: "최대 기혈 · 방어 시작치 · 회복의 바닥" },
  { key: "심법", label: "심법", desc: "최대 내공 · 내공 기반 무공 위력" },
  { key: "외공", label: "외공", desc: "공격력 · 물리 무공 스케일링" },
  { key: "자질", label: "자질", desc: "명성 획득량 보정 · 연마 효율" },
];

export default function TrainingPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "battle") router.push("/battle");
    if (state.screen === "worldmap") router.push("/worldmap");
  }, [state.screen, router]);

  if (!state.player || state.screen !== "training") return null;

  const { player } = state;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-indigo-950/10 to-gray-950 text-white">
      {/* 헤더 */}
      <div className="text-center py-6 bg-gray-900/80 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-indigo-400">⚔️ 연무장</h1>
        <p className="text-sm text-gray-400 mt-1">
          {player.name} | 기혈 {player.hp}/{player.maxHp} | 금자 {player.gold} | 명성 {player.xp}
        </p>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-6">
        {/* 섹션 1: 기초 단련 */}
        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-bold text-amber-300 mb-4">기초 단련</h2>
          <div className="flex flex-col gap-3">
            {STAT_INFO.map(({ key, label, desc }) => {
              const val = player.stats[key as keyof typeof player.stats];
              const atMax = val >= STAT_MAX;
              const cost = val + 40;
              const canUpgrade = !atMax && player.xp >= cost;
              return (
                <div key={key}
                  className="flex items-center justify-between bg-gray-800/60 rounded-lg border border-gray-700 p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold">{label}</span>
                      <span className="text-amber-400 font-mono text-lg">{val}</span>
                      {atMax && <span className="text-xs text-emerald-400">(극)</span>}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{desc}</p>
                  </div>
                  <button
                    disabled={!canUpgrade}
                    onClick={() => dispatch({ type: "UPGRADE_STAT", stat: key })}
                    className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${
                      canUpgrade
                        ? "bg-amber-800 hover:bg-amber-700 text-amber-100"
                        : "bg-gray-800 text-gray-600 cursor-not-allowed"
                    }`}
                  >
                    {atMax ? "극의" : `강화 (명성 ${cost})`}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* 섹션 2: 무공 연마 */}
        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-5">
          <h2 className="text-lg font-bold text-purple-300 mb-4">무공 연마</h2>
          <div className="flex flex-col gap-3">
            {player.deck.map((card) => {
              const cost = CARD_UPGRADE_BASE * (card.mastery ** 2);
              const maxed = card.mastery >= CARD_MASTERY_MAX;
              const canUpgrade = !maxed && player.xp >= cost;
              const stars = "★".repeat(card.mastery) + "☆".repeat(CARD_MASTERY_MAX - card.mastery);
              const curVal = getCurrentValue(card);

              return (
                <div key={card.id}
                  className={`flex items-center justify-between rounded-lg border p-4 ${
                    maxed ? "bg-emerald-950/20 border-emerald-800/50" : "bg-gray-800/60 border-gray-700"
                  }`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-white font-bold">{card.name}</span>
                      <span className="text-xs text-gray-500">[{card.type}]</span>
                    </div>
                    <div className="text-xs text-amber-400 mt-1">{stars}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      위력 {curVal} | 내공 {card.cost} | {card.description}
                    </div>
                  </div>
                  <div className="ml-3 text-right shrink-0">
                    {maxed ? (
                      <span className="text-xs text-emerald-400 font-bold">최고 경지</span>
                    ) : (
                      <button
                        disabled={!canUpgrade}
                        onClick={() => dispatch({ type: "UPGRADE_CARD", cardId: card.id })}
                        className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${
                          canUpgrade
                            ? "bg-purple-800 hover:bg-purple-700 text-purple-100"
                            : "bg-gray-800 text-gray-600 cursor-not-allowed"
                        }`}
                      >
                        연마 (명성 {cost})
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 하단 버튼 */}
        <button onClick={() => dispatch({ type: "LEAVE_TRAINING" })}
          className="w-full py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg font-bold transition-colors">
          강호로 돌아간다
        </button>
      </div>
    </div>
  );
}
