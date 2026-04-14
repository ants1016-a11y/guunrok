"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { BASIC_ACTIONS } from "@/lib/cards";
import CardButton from "@/ui/CardButton";
import BattleLogPanel from "@/ui/BattleLogPanel";
import EnemyDisplay from "@/ui/EnemyDisplay";
import PlayerPanel from "@/ui/PlayerPanel";
import { getChapter, Card } from "@/lib/types";

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
    <div className="flex flex-col h-dvh bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="bg-red-950/30 rounded-xl border border-red-900/50 p-6 max-w-lg mx-auto">
          <div className="text-5xl mb-4 text-center">💀</div>
          <h2 className="text-xl font-bold text-red-400 mb-1 text-center">{`이것이 나의 ${deathCount + 1}번째 사망이었다.`}</h2>
          <div className="w-24 h-px bg-red-800 mx-auto my-4" />
          <div className="space-y-3 text-sm text-gray-200 italic leading-relaxed mb-6">
            {deathNovel.map((line, i) => <p key={i}>{line}</p>)}
          </div>
          <div className="text-[13px] text-gray-400 mb-6 space-y-1 text-center">
            <p>{`${encounter}차 조우에서 쓰러짐`}</p>
            <p>{`마지막 초식: ${lastUsedCard || "알 수 없음"}`}</p>
          </div>
          <div className="bg-purple-950/40 border border-purple-800/50 rounded-lg px-4 py-3">
            <p className="text-purple-300 text-sm italic">영혼에 새겨진 검로는 기억한다.</p>
            <p className="text-purple-400 text-xs mt-1">기초 스탯과 해금된 무공은 다음 생에 이어진다.</p>
            <p className="text-purple-500 text-xs mt-0.5">무공 성취도·월드맵 진행·연승은 초기화됩니다.</p>
          </div>
        </div>
      </div>
      {/* sticky 하단 버튼 — 항상 보이게 */}
      <div
        className="shrink-0 px-4 py-3 bg-gray-950/95 backdrop-blur border-t border-red-900/50"
        style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
      >
        <button onClick={onResurrect}
          className="w-full max-w-lg mx-auto block px-10 py-4 bg-red-800 hover:bg-red-700 rounded-lg text-lg font-bold transition-all active:scale-95">
          다시 강호에 발을 딛는다
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

  // 카드 2단계 선택: 첫 탭=선택, 같은 카드 재탭=사용
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedBasicId, setSelectedBasicId] = useState<string | null>(null);

  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "reward") router.push("/reward");
    if (state.screen === "inn") router.push("/inn");
    if (state.screen === "worldmap") router.push("/worldmap");
  }, [state.screen, router]);

  // 합/턴 바뀌면 선택 초기화
  useEffect(() => {
    setSelectedId(null);
    setSelectedBasicId(null);
  }, [state.battle?.clashIndex, state.battle?.playerTurn]);

  if (!state.player || !state.battle || (state.screen !== "battle" && state.screen !== "death")) return null;

  const { player, battle, encounter } = state;
  const { enemy, clashIndex, logs, playerTurn } = battle;
  const chapter = getChapter(encounter);

  function handleCardTap(card: Card) {
    setSelectedBasicId(null);
    if (selectedId === card.id) {
      dispatch({ type: "PLAY_CARD", card });
      setSelectedId(null);
    } else {
      setSelectedId(card.id);
    }
  }
  function handleBasicTap(card: Card) {
    setSelectedId(null);
    if (selectedBasicId === card.id) {
      dispatch({ type: "USE_BASIC", card });
      setSelectedBasicId(null);
    } else {
      setSelectedBasicId(card.id);
    }
  }

  // 사망 화면 단독 렌더
  if (state.screen === "death") {
    return (
      <DeathScreen
        playerName={state.playerName || player.name}
        encounter={encounter}
        deathCount={state.legacy.deathCount}
        enemyName={enemy.name}
        lastUsedCard={state.lastUsedCard}
        winStreak={player.winStreak}
        deckNames={player.deck.map((c) => c.name)}
        onResurrect={() => dispatch({ type: "RESURRECT" })}
      />
    );
  }

  return (
    <div className="flex flex-col h-dvh bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      {/* 상단 고정: 장/조우/합 */}
      <header
        className="shrink-0 text-center py-2 bg-gray-900/90 backdrop-blur border-b border-gray-700"
        style={{ paddingTop: "max(0.5rem, env(safe-area-inset-top))" }}
      >
        <div className="text-[13px] text-gray-300">{chapter.name}</div>
        <div className="text-sm text-gray-200">
          제 {encounter}차 조우 · <span className="text-amber-300 font-bold">합 {clashIndex + 1}/5</span>
        </div>
      </header>

      {/* 적 영역 (컴팩트) */}
      <section className="shrink-0 px-3 pt-2">
        <EnemyDisplay enemy={enemy} clashIndex={clashIndex} compact />
      </section>

      {/* 전투 로그 — flex-1 로 남은 공간 */}
      <section className="flex-1 min-h-0 px-3 py-2">
        <BattleLogPanel logs={logs} fill />
      </section>

      {/* 하단 고정: 플레이어 + 카드 */}
      <footer
        className="shrink-0 bg-gray-950/95 backdrop-blur border-t border-gray-700 px-3 pt-2"
        style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}
      >
        <PlayerPanel player={player} compact />

        {playerTurn && (
          <div className="mt-2 space-y-2">
            {/* 손패 */}
            <div>
              <div className="flex items-center justify-between text-xs text-gray-300 mb-1 px-1">
                <span>무공 카드</span>
                <span>
                  내공 <span className="text-white font-mono">{player.energy}/{player.maxEnergy}</span>
                </span>
              </div>
              <div className="flex gap-1.5 overflow-x-auto pb-1 snap-x snap-mandatory">
                {player.hand.map((card) => (
                  <div key={card.id} className="snap-start shrink-0">
                    <CardButton
                      card={card}
                      onClick={() => handleCardTap(card)}
                      disabled={player.energy < card.cost}
                      isSelected={selectedId === card.id}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* 기본 행동 — 한 줄 꽉 채움 */}
            <div>
              <div className="text-xs text-gray-300 mb-1 px-1">기본 행동 (비용 0)</div>
              <div className="flex gap-1.5 justify-center">
                {BASIC_ACTIONS.map((card) => (
                  <div key={card.id} className="shrink-0">
                    <CardButton
                      card={card}
                      onClick={() => handleBasicTap(card)}
                      isBasic
                      isSelected={selectedBasicId === card.id}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {state.lastMessage && (
          <div className="text-center text-amber-300 text-sm animate-pulse pt-1">{state.lastMessage}</div>
        )}
      </footer>
    </div>
  );
}
