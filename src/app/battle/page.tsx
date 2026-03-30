"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { BASIC_ACTIONS } from "@/lib/cards";
import CardButton from "@/ui/CardButton";
import BattleLogPanel from "@/ui/BattleLogPanel";
import EnemyDisplay from "@/ui/EnemyDisplay";
import PlayerPanel from "@/ui/PlayerPanel";
import { getChapter } from "@/lib/types";

// ─── 사망 화면 ──────────────────────────────────────────────
function DeathScreen({ playerName, encounter, deathCount, enemyName, lastUsedCard, winStreak, deckNames, onResurrect }: {
  playerName: string; encounter: number; deathCount: number; enemyName: string;
  lastUsedCard: string; winStreak: number; deckNames: string[]; onResurrect: () => void;
}) {
  const deathNovel = useMemo(() => {
    const cardName = lastUsedCard || deckNames[0] || "무명의 초식";
    return [
      `강호의 어느 이름 모를 산길, ${playerName}이라 불리던 한 무인이 첫 발을 내디뎠다.`,
      encounter > 3
        ? `${encounter}번의 조우를 거치며 ${winStreak > 0 ? winStreak + "연승의 기세" : "고된 싸움"}을 이어갔으나,`
        : "기틀을 닦기도 전에 가혹한 강호의 풍파를 정면으로 마주했다.",
      `마지막 순간, ${enemyName}의 공세를 이기지 못하고 ${cardName}의 여파 속에 쓰러졌다.`,
      "그가 남긴 투지는 먼지처럼 흩어졌으나, 그의 이름은 강호의 전설로 기억되리라.",
    ];
  }, [playerName, encounter, enemyName, lastUsedCard, winStreak, deckNames]);

  return (
    <div className="text-center py-6">
      <div className="bg-red-950/30 rounded-xl border border-red-900/50 p-8 max-w-lg mx-auto">
        <div className="text-5xl mb-4">💀</div>
        <h2 className="text-xl font-bold text-red-400 mb-1">{`이것이 나의 ${deathCount + 1}번째 사망이었다.`}</h2>
        <div className="w-24 h-px bg-red-800 mx-auto my-4" />
        <div className="space-y-3 text-sm text-gray-300 italic leading-relaxed mb-6">
          {deathNovel.map((line, i) => <p key={i}>{line}</p>)}
        </div>
        <div className="text-xs text-gray-500 mb-6 space-y-1">
          <p>{`${encounter}차 조우에서 쓰러짐`}</p>
          <p>{`마지막 초식: ${lastUsedCard || "알 수 없음"}`}</p>
        </div>
        <div className="bg-purple-950/40 border border-purple-800/50 rounded-lg px-4 py-3 mb-6">
          <p className="text-purple-300 text-sm italic">영혼에 새겨진 검로는 기억한다.</p>
          <p className="text-purple-400 text-xs mt-1">다음 생에서 기본 무공 성취도가 +1 계승됩니다.</p>
        </div>
        <button onClick={onResurrect}
          className="px-10 py-3 bg-red-800 hover:bg-red-700 rounded-lg text-lg font-bold transition-all transform hover:scale-105 active:scale-95">
          다시 일어서다
        </button>
      </div>
    </div>
  );
}

// ─── 메인 ───────────────────────────────────────────────────
export default function BattlePage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  // screen 라우팅
  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "reward") router.push("/reward");
    if (state.screen === "inn") router.push("/inn");
  }, [state.screen, router]);

  if (!state.player || !state.battle || (state.screen !== "battle" && state.screen !== "death")) return null;

  const { player, battle, encounter } = state;
  const { enemy, clashIndex, logs, playerTurn } = battle;
  const chapter = getChapter(encounter);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="text-center py-3 bg-gray-900/80 border-b border-gray-700">
        <div className="text-xs text-gray-500">{chapter.name}</div>
        <div className="text-sm text-gray-400">제 {encounter}차 조우 | 합 {clashIndex + 1}/5</div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-4 flex flex-col gap-4">
        <div className="flex justify-center">
          <EnemyDisplay enemy={enemy} clashIndex={clashIndex} />
        </div>

        <BattleLogPanel logs={logs} />

        <div className="flex justify-center">
          <PlayerPanel player={player} />
        </div>

        {/* 카드 영역 (전투 중) */}
        {state.screen === "battle" && playerTurn && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm text-gray-500 mb-2 text-center">무공 카드 (내공 {player.energy}/{player.maxEnergy})</h3>
              <div className="flex flex-wrap justify-center gap-3">
                {player.hand.map((card) => (
                  <CardButton key={card.id} card={card}
                    onClick={() => dispatch({ type: "PLAY_CARD", card })}
                    disabled={player.energy < card.cost} />
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm text-gray-500 mb-2 text-center">기본 행동 (비용 없음)</h3>
              <div className="flex justify-center gap-3">
                {BASIC_ACTIONS.map((card) => (
                  <CardButton key={card.id} card={card}
                    onClick={() => dispatch({ type: "USE_BASIC", card })} isBasic />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 사망 화면 */}
        {state.screen === "death" && (
          <DeathScreen
            playerName={state.playerName || player.name}
            encounter={encounter}
            deathCount={state.deathCount}
            enemyName={enemy.name}
            lastUsedCard={state.lastUsedCard}
            winStreak={player.winStreak}
            deckNames={player.deck.map((c) => c.name)}
            onResurrect={() => dispatch({ type: "RESURRECT" })}
          />
        )}

        {state.lastMessage && (
          <div className="text-center text-yellow-500 text-sm animate-pulse">{state.lastMessage}</div>
        )}
      </div>
    </div>
  );
}
