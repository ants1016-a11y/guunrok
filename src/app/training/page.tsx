"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function TrainingPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "battle") router.push("/battle");
  }, [state.screen, router]);

  if (state.screen !== "training") return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-indigo-950/10 to-gray-950 flex flex-col items-center justify-center text-white">
      <div className="text-center">
        <div className="text-5xl mb-4">⚔️</div>
        <h1 className="text-2xl font-bold text-indigo-400 mb-2">연무장</h1>
        <p className="text-gray-500 text-sm mb-8">준비 중</p>
        <button onClick={() => dispatch({ type: "LEAVE_TRAINING" })}
          className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg font-bold transition-colors">
          돌아가기
        </button>
      </div>
    </div>
  );
}
