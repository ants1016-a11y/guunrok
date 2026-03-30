"use client";

import { useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function TitlePage() {
  const dispatch = useGameDispatch();
  const router = useRouter();
  const [name, setName] = useState("");
  const [inheritedMastery, setInheritedMastery] = useState(0);
  const [deathCount, setDeathCount] = useState(0);

  useEffect(() => {
    const saved = localStorage.getItem("guunrok_playerName");
    if (saved) setName(saved);
    const enlightenment = parseInt(localStorage.getItem("guunrok_enlightenment") || "0", 10);
    setInheritedMastery(enlightenment);
    const deaths = parseInt(localStorage.getItem("guunrok_deathCount") || "0", 10);
    setDeathCount(deaths);
  }, []);

  const handleStart = () => {
    const finalName = name.trim() || "회귀한 둔재";
    localStorage.setItem("guunrok_playerName", finalName);
    dispatch({ type: "START_GAME", name: finalName, inheritedMastery });
    router.push("/world");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 flex flex-col items-center justify-center text-white">
      <div className="text-center mb-8">
        <div className="text-6xl mb-6">{"⚔️"}</div>
        <h1 className="text-5xl font-bold text-amber-400 mb-2 tracking-wider">
          구운록
        </h1>
        <p className="text-base text-gray-400 mt-3 tracking-wide">
          느리게, 그러나 끝까지
        </p>
        <div className="w-32 h-px bg-amber-700 mx-auto mt-4" />
      </div>

      <div className="text-center text-gray-500 text-sm max-w-md mb-8 leading-relaxed">
        {deathCount > 0 ? (
          <>
            <p className="text-gray-400 italic">
              같은 산길이 또다시 펼쳐졌다.
            </p>
            <p className="text-gray-500 mt-2">
              {`익숙한 바람결\u2026 나는 다시 이곳에 서 있다. (${deathCount}번째 되풀이)`}
            </p>
          </>
        ) : (
          <>
            <p className="text-gray-400">나는 천재가 아니다.</p>
            <p className="text-gray-400">하지만 포기하지 않는 법은 배웠다.</p>
            <p className="mt-3 text-gray-500">
              남이 한 번에 깨우치는 수를, 나는 열 번 갈고
            </p>
            <p className="text-gray-500">
              남이 가볍게 넘기는 합을, 나는 백 번 되새긴다.
            </p>
          </>
        )}
      </div>

      <div className="w-full max-w-sm mb-8">
        <label className="block text-center text-amber-300 text-sm mb-3">
          무와 협을 좋아하는 당신은 누구인가?
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleStart()}
          placeholder="이름을 입력하시오"
          maxLength={12}
          className="w-full px-4 py-3 bg-gray-800 border-2 border-amber-700/50 rounded-lg text-center text-lg text-white placeholder-gray-600 focus:outline-none focus:border-amber-500 transition-colors"
        />
      </div>

      {inheritedMastery > 0 && (
        <div className="text-center mb-6 px-4 py-2 bg-purple-950/40 border border-purple-700/50 rounded-lg">
          <p className="text-purple-300 text-sm italic">
            영혼에 새겨진 검로는 기억한다.
          </p>
          <p className="text-purple-400 text-xs mt-1">
            {`기본 무공 성취도 +${inheritedMastery} 계승`}
          </p>
        </div>
      )}

      <button
        onClick={handleStart}
        className="group relative px-12 py-4 bg-amber-800 hover:bg-amber-700 rounded-lg text-xl font-bold transition-all duration-300 transform hover:scale-105 active:scale-95"
      >
        <span className="relative z-10">
          {deathCount > 0 ? "다시 발걸음을 옮기다" : "강호에 발을 딛다"}
        </span>
        <div className="absolute inset-0 bg-amber-600/20 rounded-lg blur-xl group-hover:blur-2xl transition-all" />
      </button>

      <div className="mt-16 text-center text-xs text-gray-600 space-y-1">
        <p>{"턴제 카드 비무 \u2014 5합 1턴"}</p>
        <p>무공을 고르면, 적과 동시에 초식을 겨룬다.</p>
        <p>{"한 합, 한 합\u2014강호는 끝내 나를 인정한다."}</p>
      </div>

      <div className="absolute bottom-4 text-xs text-gray-700">
        {"구운록 v3.0 \u2014 Next.js Web"}
      </div>
    </div>
  );
}
