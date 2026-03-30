"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getChapter } from "@/lib/types";
import PlayerPanel from "@/ui/PlayerPanel";

export default function WorldPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  // screen 라우팅
  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "battle") router.push("/battle");
    if (state.screen === "reward") router.push("/reward");
    if (state.screen === "inn") router.push("/inn");
    if (state.screen === "training") router.push("/training");
  }, [state.screen, router]);

  if (!state.player || state.screen !== "menu") return null;

  const { player, encounter, innBuff, lastMessage, saveNotice } = state;
  const nextEncounter = encounter + 1;
  const chapter = getChapter(nextEncounter);
  const isBoss = nextEncounter % 5 === 0;
  const isMid = nextEncounter % 3 === 0 && !isBoss;

  let nextEnemyPreview = "산채 졸개";
  if (nextEncounter <= 20) {
    if (isBoss) nextEnemyPreview = "녹림왕 마천광";
    else if (isMid) nextEnemyPreview = "녹림 행동대장";
  } else {
    if (isBoss) nextEnemyPreview = "혈교 장로 혈마도";
    else if (isMid) nextEnemyPreview = "혈교 고수";
    else nextEnemyPreview = "혈교 자객";
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-green-950/20 to-gray-950 text-white">
      <div className="text-center py-6 bg-gray-900/80 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-amber-400">{chapter.name}</h1>
        <p className="text-sm text-gray-400 mt-1">{chapter.desc}</p>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-6">
        <div className="flex justify-center">
          <PlayerPanel player={player} />
        </div>

        {/* 알림 메시지 */}
        {(lastMessage || saveNotice) && (
          <div className="text-center text-amber-400 text-sm">{saveNotice || lastMessage}</div>
        )}

        {/* 객잔 버프 표시 */}
        {innBuff && (
          <div className="text-center text-emerald-400 text-xs bg-emerald-950/30 border border-emerald-800/50 rounded-lg py-2">
            식사 버프: {innBuff.name} ({innBuff.type === "energy" ? `내공 +${innBuff.val}` : innBuff.type === "maxHp" ? `최대HP +${innBuff.val}` : `방어 +${innBuff.val}`})
          </div>
        )}

        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-6">
          <h2 className="text-lg font-bold text-gray-300 mb-4 text-center">강호의 길</h2>

          <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
            <span>조우 {encounter}차 완료</span>
            <span>연승 {player.winStreak}</span>
          </div>

          <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden mb-6">
            <div className="h-full bg-amber-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, ((encounter - chapter.range[0] + 1) / (chapter.range[1] - chapter.range[0] + 1)) * 100)}%` }} />
          </div>

          <div className={`text-center p-4 rounded-lg border ${isBoss ? "bg-red-950/40 border-red-700" : isMid ? "bg-orange-950/40 border-orange-700" : "bg-gray-800/40 border-gray-600"}`}>
            <div className="text-xs text-gray-500 mb-1">다음 조우 #{nextEncounter}</div>
            <div className={`text-lg font-bold ${isBoss ? "text-red-400" : isMid ? "text-orange-400" : "text-gray-300"}`}>
              {isBoss ? "👹 " : isMid ? "⚔️ " : "🥷 "}{nextEnemyPreview}
            </div>
            {isBoss && <div className="text-xs text-red-400 mt-1">보스전 — 각오를 단단히 하라!</div>}
          </div>

          <div className="flex flex-col gap-3 mt-6">
            <button onClick={() => dispatch({ type: "START_BATTLE" })}
              className={`w-full py-4 rounded-lg text-lg font-bold transition-all transform hover:scale-[1.02] active:scale-[0.98] ${isBoss ? "bg-red-800 hover:bg-red-700 text-red-100" : "bg-amber-800 hover:bg-amber-700 text-amber-100"}`}>
              {isBoss ? "보스에게 도전하기" : "앞으로 나아가기"}
            </button>
            <div className="flex gap-3">
              <button onClick={() => dispatch({ type: "VISIT_INN" })}
                className="flex-1 py-3 bg-emerald-800 hover:bg-emerald-700 rounded-lg text-base font-bold transition-colors">
                🏮 취선루
              </button>
              <button onClick={() => dispatch({ type: "VISIT_TRAINING" })}
                className="flex-1 py-3 bg-indigo-800 hover:bg-indigo-700 rounded-lg text-base font-bold transition-colors">
                ⚔️ 연무장
              </button>
            </div>
            <button onClick={() => dispatch({ type: "SAVE_GAME" })}
              className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-gray-300 transition-colors">
              기록 저장
            </button>
          </div>
        </div>

        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">비급고 ({player.deck.length}장)</h3>
          <div className="grid grid-cols-2 gap-2">
            {player.deck.map((card, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800/60 rounded px-3 py-2 text-sm">
                <span className="text-white">{card.name}</span>
                <span className="text-xs text-gray-500">비용 {card.cost} | {"★".repeat(card.mastery)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
