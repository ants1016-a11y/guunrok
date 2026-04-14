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
    if (state.screen === "worldmap") router.push("/worldmap");
  }, [state.screen, router]);

  if (!state.player || state.screen !== "menu") return null;

  const { player, encounter, innBuff, lastMessage, saveNotice } = state;
  const nextEncounter = encounter + 1;
  const chapter = getChapter(nextEncounter);
  const isBoss = nextEncounter % 5 === 0;
  const isMid = nextEncounter % 3 === 0 && !isBoss;

  // 다음 적 미리보기 — 이름/예상 HP/난이도/힌트 (enemies.ts 값 기반)
  let nextEnemyPreview = "산채 졸개";
  let nextEnemyHp = 40;
  let nextEnemyDifficulty = 1; // 별 개수 1-5
  let nextEnemyHint = "무리하지 말고 기본 무공으로 천천히.";
  if (nextEncounter <= 20) {
    if (isBoss) {
      nextEnemyPreview = "녹림왕 마천광";
      nextEnemyHp = 320;
      nextEnemyDifficulty = 5;
      nextEnemyHint = "내공을 비축해 강공 타이밍을 노리자.";
    } else if (isMid) {
      nextEnemyPreview = "녹림 행동대장";
      nextEnemyHp = 65;
      nextEnemyDifficulty = 3;
      nextEnemyHint = "방어 카드 한 장은 꺼두자.";
    } else {
      nextEnemyPreview = "산채 졸개";
      nextEnemyHp = 40;
      nextEnemyDifficulty = 1;
      nextEnemyHint = "평범한 일격이면 충분.";
    }
  } else {
    if (isBoss) {
      nextEnemyPreview = "혈교 장로 혈마도";
      nextEnemyHp = 420;
      nextEnemyDifficulty = 5;
      nextEnemyHint = "혈천만상이 올 합엔 방어 필수.";
    } else if (isMid) {
      nextEnemyPreview = "혈교 고수";
      nextEnemyHp = 110;
      nextEnemyDifficulty = 4;
      nextEnemyHint = "혈공 데미지가 크다 — 방어 교대로.";
    } else {
      nextEnemyPreview = "혈교 자객";
      nextEnemyHp = 70;
      nextEnemyDifficulty = 2;
      nextEnemyHint = "독침 내공 차감 조심.";
    }
  }
  const difficultyStars = "★".repeat(nextEnemyDifficulty) + "☆".repeat(5 - nextEnemyDifficulty);

  return (
    <div className="min-h-dvh bg-gradient-to-b from-gray-950 via-green-950/20 to-gray-950 text-white">
      <div
        className="relative text-center py-3 bg-gray-900/80 border-b border-gray-700"
        style={{ paddingTop: "max(0.75rem, env(safe-area-inset-top))" }}
      >
        <h1 className="text-lg sm:text-2xl font-bold text-amber-400 leading-tight">{chapter.name}</h1>
        <p className="text-xs sm:text-sm text-gray-300 mt-0.5 line-clamp-1">{chapter.desc}</p>
        {/* 저장 버튼 헤더 우측 고정 */}
        <button
          onClick={() => dispatch({ type: "SAVE_GAME" })}
          className="absolute right-3 top-1/2 -translate-y-1/2 px-2 py-1 text-[11px] bg-gray-700 hover:bg-gray-600 rounded text-gray-200"
        >
          💾 저장
        </button>
      </div>

      <div className="max-w-2xl mx-auto px-3 py-3 flex flex-col gap-3">
        <PlayerPanel player={player} compact />

        {/* 알림 + 버프 (한 줄 축약) */}
        {(lastMessage || saveNotice) && (
          <div className="text-center text-amber-300 text-[13px] leading-snug">{saveNotice || lastMessage}</div>
        )}
        {innBuff && (
          <div className="text-center text-emerald-300 text-[12px] bg-emerald-950/30 border border-emerald-800/50 rounded-lg py-1">
            🍽️ {innBuff.name} ({innBuff.type === "energy" ? `내공 +${innBuff.val}` : innBuff.type === "maxHp" ? `최대HP +${innBuff.val}` : `방어 +${innBuff.val}`})
          </div>
        )}

        <div className="bg-gray-900/60 rounded-xl border border-gray-700 p-3">
          {/* 진행 정보 한 줄 */}
          <div className="flex items-center justify-between text-[12px] text-gray-300 mb-1.5">
            <span>조우 {encounter}차 완료</span>
            <span>연승 {player.winStreak}</span>
          </div>
          <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden mb-3">
            <div className="h-full bg-amber-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, ((encounter - chapter.range[0] + 1) / (chapter.range[1] - chapter.range[0] + 1)) * 100)}%` }} />
          </div>

          {/* 다음 조우 — 미리보기 확장 */}
          <div className={`p-2 rounded-lg border mb-3 ${isBoss ? "bg-red-950/40 border-red-700" : isMid ? "bg-orange-950/40 border-orange-700" : "bg-gray-800/40 border-gray-600"}`}>
            <div className="flex items-center justify-between text-[11px] text-gray-300">
              <span>다음 조우 #{nextEncounter}</span>
              <span className="text-amber-400 tracking-tight">{difficultyStars}</span>
            </div>
            <div className={`text-base font-bold leading-tight mt-0.5 ${isBoss ? "text-red-400" : isMid ? "text-orange-400" : "text-gray-100"}`}>
              {isBoss ? "👹 " : isMid ? "⚔️ " : "🥷 "}{nextEnemyPreview}
            </div>
            <div className="mt-1 flex items-center gap-2 text-[11px] text-gray-200">
              <span>❤ HP ~{nextEnemyHp}</span>
            </div>
            <div className="mt-1 text-[11px] text-gray-300 italic leading-snug">
              💡 {nextEnemyHint}
            </div>
            {isBoss && <div className="mt-1 text-[11px] text-red-300 font-bold">⚠ 보스전 — 각오를 단단히 하라!</div>}
          </div>

          {/* 액션 버튼 — 위계 정리, 모바일 py 축소 */}
          <div className="flex flex-col gap-2">
            <button onClick={() => dispatch({ type: "START_BATTLE" })}
              className={`w-full py-3 rounded-lg text-base font-bold transition-all active:scale-[0.98] ${isBoss ? "bg-red-800 hover:bg-red-700 text-red-100" : "bg-amber-800 hover:bg-amber-700 text-amber-100"}`}>
              {isBoss ? "⚔️ 보스에게 도전하기" : "▶ 앞으로 나아가기"}
            </button>
            <button onClick={() => dispatch({ type: "ENTER_WORLDMAP" })}
              className="w-full py-2.5 bg-red-900 hover:bg-red-800 rounded-lg text-sm font-bold text-red-100 transition-all active:scale-[0.98]">
              🗺️ 북쪽 출도 (녹림 루트)
            </button>
            <div className="flex gap-2">
              <button onClick={() => dispatch({ type: "VISIT_INN" })}
                className="flex-1 py-2.5 bg-emerald-800 hover:bg-emerald-700 rounded-lg text-sm font-bold">
                🏮 취선루
              </button>
              <button onClick={() => dispatch({ type: "VISIT_TRAINING" })}
                className="flex-1 py-2.5 bg-indigo-800 hover:bg-indigo-700 rounded-lg text-sm font-bold">
                ⚔️ 연무장
              </button>
            </div>
          </div>
        </div>

        {/* 비급고 — details 로 기본 접힘 */}
        <details className="bg-gray-900/60 rounded-xl border border-gray-700 p-3">
          <summary className="text-[13px] font-bold text-gray-200 cursor-pointer select-none">
            📜 비급고 ({player.deck.length}장)
          </summary>
          <div className="grid grid-cols-2 gap-1.5 mt-2">
            {player.deck.map((card, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800/60 rounded px-2 py-1.5 text-[12px]">
                <span className="text-white truncate">{card.name}</span>
                <span className="text-[11px] text-gray-300 shrink-0 ml-1">
                  {card.cost}·{"★".repeat(card.mastery)}
                </span>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
}
