"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function TitlePage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [name, setName] = useState("");

  // screen 라우팅
  useEffect(() => {
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "battle") router.push("/battle");
    if (state.screen === "reward") router.push("/reward");
    if (state.screen === "inn") router.push("/inn");
    if (state.screen === "worldmap") router.push("/worldmap");
  }, [state.screen, router]);

  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem("guunrok_playerName");
      if (saved) setName(saved);
    } catch { /* noop */ }
  }, []);

  if (!mounted || state.screen !== "title") {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="text-6xl mb-4">{"⚔️"}</div>
          <p className="text-gray-400 text-sm animate-pulse">불러오는 중...</p>
        </div>
      </div>
    );
  }

  const deathCount = state.legacy.deathCount;
  const hasLegacy = deathCount > 0;

  const handleStart = () => {
    const finalName = name.trim() || "회귀한 둔재";
    localStorage.setItem("guunrok_playerName", finalName);
    dispatch({ type: "START_GAME", name: finalName });
  };

  return (
    <div className="min-h-dvh bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 flex flex-col items-center justify-center text-white px-4 py-4">
      <div className="text-center mb-4">
        <div className="text-4xl sm:text-6xl mb-2 sm:mb-6">⚔️</div>
        <h1 className="text-3xl sm:text-5xl font-bold text-amber-400 tracking-wider leading-tight">구운록</h1>
        <p className="text-xs sm:text-base text-gray-300 mt-1 tracking-wide">느리게, 그러나 끝까지</p>
        <div className="w-24 h-px bg-amber-700 mx-auto mt-2" />
      </div>

      {/* 설명 — 모바일은 축약 */}
      <div className="text-center text-sm text-gray-300 max-w-md mb-3 leading-relaxed">
        {deathCount > 0 ? (
          <p className="italic text-gray-200">같은 산길이 또다시 펼쳐졌다.</p>
        ) : (
          <>
            <p className="hidden sm:block">나는 천재가 아니다. 하지만 포기하지 않는 법은 배웠다.</p>
            <p className="sm:hidden text-gray-200">포기하지 않는 법은 배웠다.</p>
          </>
        )}
      </div>

      {/* 회귀 경지 — martial_arts.md 의 9경지 이름 차용 (라벨만, 추후 조정 예정) */}
      {deathCount > 0 && (() => {
        const realms = [
          { n: 100, name: "자연경", hanja: "自然境", color: "text-cyan-200" },
          { n: 50,  name: "생사경", hanja: "生死境", color: "text-purple-300" },
          { n: 30,  name: "현경",   hanja: "玄境",   color: "text-violet-300" },
          { n: 20,  name: "화경",   hanja: "化境",   color: "text-rose-300" },
          { n: 12,  name: "초절정", hanja: "超絶頂", color: "text-red-300" },
          { n: 7,   name: "절정",   hanja: "絶頂",   color: "text-orange-300" },
          { n: 4,   name: "일류",   hanja: "一流",   color: "text-yellow-300" },
          { n: 2,   name: "이류",   hanja: "二流",   color: "text-emerald-300" },
          { n: 1,   name: "삼류",   hanja: "三流",   color: "text-gray-200" },
        ];
        const current = realms.find((r) => deathCount >= r.n);
        const next = [...realms].reverse().find((r) => deathCount < r.n);
        return (
          <div className="w-full max-w-sm mb-4 rounded-xl border border-amber-800/40 bg-amber-950/20 px-4 py-3 text-center">
            <div className="text-[11px] uppercase tracking-wider text-amber-400/80">회귀 {deathCount}회</div>
            {current && (
              <div className={`mt-1 flex items-baseline justify-center gap-2 ${current.color}`}>
                <span className="text-3xl sm:text-4xl font-extrabold leading-none">{current.name}</span>
                <span className="text-[12px] opacity-70">{current.hanja}</span>
              </div>
            )}
            {next && (
              <div className="mt-1.5 text-[11px] text-gray-300">
                다음 경지 <span className="text-amber-300">{next.name}</span> 까지 {next.n - deathCount}회
              </div>
            )}
          </div>
        );
      })()}

      <div className="w-full max-w-sm mb-3">
        <label className="block text-center text-amber-300 text-[13px] mb-1.5">무와 협을 좋아하는 당신은?</label>
        <input
          type="text" value={name} onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleStart()}
          placeholder="이름을 입력하시오" maxLength={12}
          className="w-full px-4 py-2.5 bg-gray-800 border-2 border-amber-700/50 rounded-lg text-center text-lg text-white placeholder-gray-600 focus:outline-none focus:border-amber-500"
        />
      </div>

      {hasLegacy && (
        <div className="text-center mb-3 px-3 py-1.5 bg-purple-950/40 border border-purple-700/50 rounded-lg">
          <p className="text-purple-300 text-[12px] italic">영혼에 새겨진 검로는 기억한다.</p>
          <p className="text-purple-400 text-[11px]">기초 스탯과 해금 무공이 이어집니다.</p>
        </div>
      )}

      <button onClick={handleStart}
        className="px-8 py-3 sm:px-12 sm:py-4 bg-amber-800 hover:bg-amber-700 rounded-lg text-lg sm:text-xl font-bold transition-all active:scale-95">
        {deathCount > 0 ? "다시 발걸음을 옮기다" : "강호에 발을 딛다"}
      </button>

      {/* 태그라인 — 모바일에선 한 줄 */}
      <div className="mt-4 text-center text-[11px] text-gray-300">
        턴제 카드 비무 · 5합 1턴
      </div>
    </div>
  );
}
