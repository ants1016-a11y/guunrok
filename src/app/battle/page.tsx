"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { BASIC_ACTIONS } from "@/lib/cards";
import HealthBar from "@/ui/HealthBar";
import CardButton from "@/ui/CardButton";
import BattleLogPanel from "@/ui/BattleLogPanel";
import EnemyDisplay from "@/ui/EnemyDisplay";
import PlayerPanel from "@/ui/PlayerPanel";
import { getChapter } from "@/lib/types";

export default function BattlePage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  // 전투 상태가 아니면 리다이렉트
  useEffect(() => {
    if (!state.player || !state.enemy) {
      if (state.phase === "title") router.push("/");
      else router.push("/world");
    }
  }, [state.player, state.enemy, state.phase, router]);

  if (!state.player || !state.enemy) return null;

  const { player, enemy, battleLogs, clashIndex, encounter, phase } = state;
  const chapter = getChapter(encounter);
  const isBattleActive = phase === "battle_player_turn";

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      {/* 헤더 */}
      <div className="text-center py-3 bg-gray-900/80 border-b border-gray-700">
        <div className="text-xs text-gray-500">{chapter.name}</div>
        <div className="text-sm text-gray-400">
          제 {encounter}차 조우 | 합 {clashIndex + 1}/5
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-4 flex flex-col gap-4">
        {/* 적 정보 */}
        <div className="flex justify-center">
          <EnemyDisplay enemy={enemy} clashIndex={clashIndex} />
        </div>

        {/* 전투 로그 */}
        <BattleLogPanel logs={battleLogs} />

        {/* 플레이어 정보 */}
        <div className="flex justify-center">
          <PlayerPanel player={player} />
        </div>

        {/* 카드 영역 */}
        {isBattleActive && (
          <div className="space-y-4">
            {/* 무공 카드 */}
            <div>
              <h3 className="text-sm text-gray-500 mb-2 text-center">
                무공 카드 (내공 {player.energy}/{player.maxEnergy})
              </h3>
              <div className="flex flex-wrap justify-center gap-3">
                {player.hand.map((card) => (
                  <CardButton
                    key={card.id}
                    card={card}
                    onClick={() => dispatch({ type: "PLAY_CARD", card })}
                    disabled={player.energy < card.cost}
                  />
                ))}
              </div>
            </div>

            {/* 기본 행동 */}
            <div>
              <h3 className="text-sm text-gray-500 mb-2 text-center">
                기본 행동 (비용 없음)
              </h3>
              <div className="flex justify-center gap-3">
                {BASIC_ACTIONS.map((card) => (
                  <CardButton
                    key={card.id}
                    card={card}
                    onClick={() => dispatch({ type: "USE_BASIC", card })}
                    isBasic
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 승리 화면 */}
        {phase === "victory" && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🏆</div>
            <h2 className="text-2xl font-bold text-yellow-400 mb-2">
              비무 승리!
            </h2>
            <p className="text-gray-400 mb-6">
              {enemy.name}을(를) 쓰러뜨렸습니다.
            </p>
            <button
              onClick={() => {
                dispatch({ type: "CONTINUE_AFTER_VICTORY" });
                router.push("/world");
              }}
              className="px-8 py-3 bg-amber-700 hover:bg-amber-600 rounded-lg text-lg font-bold transition-colors"
            >
              강호로 돌아가기
            </button>
          </div>
        )}

        {/* 게임오버 화면 */}
        {phase === "gameover" && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">💀</div>
            <h2 className="text-2xl font-bold text-red-500 mb-2">주화입마</h2>
            <p className="text-gray-400 mb-2">
              의식이 흐려진다... 여기까지인가.
            </p>
            <p className="text-gray-500 text-sm mb-6">
              {encounter}차 조우에서 쓰러짐 | 연승 {player.winStreak}
            </p>
            <button
              onClick={() => {
                dispatch({ type: "RESTART" });
                router.push("/");
              }}
              className="px-8 py-3 bg-red-800 hover:bg-red-700 rounded-lg text-lg font-bold transition-colors"
            >
              처음부터 다시
            </button>
          </div>
        )}

        {/* 에러 메시지 */}
        {state.lastMessage && (
          <div className="text-center text-yellow-500 text-sm animate-pulse">
            {state.lastMessage}
          </div>
        )}
      </div>
    </div>
  );
}
