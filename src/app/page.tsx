"use client";

import { useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";

export default function TitlePage() {
  const dispatch = useGameDispatch();
  const router = useRouter();

  const handleStart = () => {
    dispatch({ type: "START_GAME" });
    router.push("/world");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 flex flex-col items-center justify-center text-white">
      <div className="text-center mb-12">
        <div className="text-6xl mb-6">{"\u2694\uFE0F"}</div>
        <h1 className="text-5xl font-bold text-amber-400 mb-2 tracking-wider">
          {"구운록"}
        </h1>
        <p className="text-lg text-gray-400 mt-4">{"회귀한 둔재의 강호"}</p>
        <div className="w-32 h-px bg-amber-700 mx-auto mt-4" />
      </div>

      <div className="text-center text-gray-500 text-sm max-w-md mb-12 leading-relaxed">
        <p>{"한때 강호 최약의 둔재라 불렸던 사내가 회귀했다."}</p>
        <p className="mt-2">
          {"이번 생에선 다르다. 무공 카드를 갈고닦아,"}
          <br />
          {"녹림의 산적부터 혈교의 장로까지 \u2014 모두 쓰러뜨린다."}
        </p>
      </div>

      <button
        onClick={handleStart}
        className="group relative px-12 py-4 bg-amber-800 hover:bg-amber-700 rounded-lg text-xl font-bold transition-all duration-300 transform hover:scale-105 active:scale-95"
      >
        <span className="relative z-10">{"강호에 발을 딛다"}</span>
        <div className="absolute inset-0 bg-amber-600/20 rounded-lg blur-xl group-hover:blur-2xl transition-all" />
      </button>

      <div className="mt-16 text-center text-xs text-gray-600 space-y-1">
        <p>{"턴제 카드 배틀 \u2014 5합 1턴"}</p>
        <p>{"무공 카드를 선택하면 적과 동시에 초식을 겨룬다"}</p>
      </div>

      <div className="absolute bottom-4 text-xs text-gray-700">
        {"구운록 v3.0 \u2014 Next.js Web"}
      </div>
    </div>
  );
}
