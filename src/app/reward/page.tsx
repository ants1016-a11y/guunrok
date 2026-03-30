"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function RewardPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  // screen 라우팅
  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "battle") router.push("/battle");
    if (state.screen === "inn") router.push("/inn");
  }, [state.screen, router]);

  if (state.screen !== "reward" || !state.lastRewards || !state.player || !state.battle) return null;

  const { lastRewards, player, battle, encounter } = state;
  const canVisitInn = encounter % 3 === 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-amber-950/10 to-gray-950 flex flex-col items-center justify-center text-white">
      <div className="max-w-lg w-full px-4">
        <div className="bg-gray-900/80 rounded-xl border border-amber-700/50 p-8 text-center">
          <div className="text-5xl mb-4">🏆</div>
          <h1 className="text-2xl font-bold text-yellow-400 mb-2">비무 승리!</h1>
          <p className="text-gray-400 mb-6">{battle.enemy.name}을(를) 쓰러뜨렸다.</p>

          <div className="bg-gray-800/60 rounded-lg border border-gray-700 p-4 mb-6">
            <div className="flex justify-center gap-8 text-lg">
              <div>
                <span className="text-gray-400 text-sm">명성</span>
                <p className="text-amber-300 font-bold">+{lastRewards.xp}</p>
              </div>
              <div>
                <span className="text-gray-400 text-sm">금자</span>
                <p className="text-yellow-400 font-bold">+{lastRewards.gold}</p>
              </div>
              <div>
                <span className="text-gray-400 text-sm">연승</span>
                <p className="text-orange-400 font-bold">{lastRewards.streak}</p>
              </div>
            </div>
            {lastRewards.isBoss && (
              <p className="text-red-400 text-sm mt-3 italic">보스를 쓰러뜨린 전리품이 손에 쥐어진다.</p>
            )}
          </div>

          <div className="text-xs text-gray-500 mb-6 space-y-1">
            <p>기혈 {player.hp}/{player.maxHp} | 금자 {player.gold} | 명성 {player.xp}</p>
            <p>제 {encounter}차 조우 완료</p>
          </div>

          <div className="flex flex-col gap-3">
            {canVisitInn && (
              <button onClick={() => dispatch({ type: "VISIT_INN" })}
                className="w-full py-3 bg-emerald-800 hover:bg-emerald-700 rounded-lg text-lg font-bold transition-colors">
                🏮 객잔에 들르다
              </button>
            )}
            <button onClick={() => dispatch({ type: "CONTINUE_TO_NEXT" })}
              className="w-full py-3 bg-amber-800 hover:bg-amber-700 rounded-lg text-lg font-bold transition-colors">
              계속 산을 오른다
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
