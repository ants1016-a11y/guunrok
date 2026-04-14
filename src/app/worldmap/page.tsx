"use client";

import { useGameState, useGameDispatch } from "@/state/game";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { NODE_COLORS, getReachableNodes } from "@/lib/worldmap";
import PlayerPanel from "@/ui/PlayerPanel";

export default function WorldMapPage() {
  const state = useGameState();
  const dispatch = useGameDispatch();
  const router = useRouter();

  useEffect(() => {
    if (state.screen === "title") router.push("/");
    if (state.screen === "menu") router.push("/world");
    if (state.screen === "battle") router.push("/battle");
    if (state.screen === "reward") router.push("/reward");
    if (state.screen === "inn") router.push("/inn");
    if (state.screen === "training") router.push("/training");
  }, [state.screen, router]);

  if (!state.player || !state.mapNodes || state.screen !== "worldmap") return null;

  const { player, mapNodes, currentNodeId } = state;
  const reachable = getReachableNodes(mapNodes, currentNodeId);

  // 모든 연결 노드가 방문 완료되면 클리어
  const currentNode = mapNodes.find((n) => n.id === currentNodeId);
  const isRouteComplete = currentNode && currentNode.connections.length === 0 && currentNode.visited;

  // 6열 3행 그리드로 노드 배치
  const cols = 6;
  const rows = 3;

  return (
    <div className="min-h-dvh bg-gradient-to-b from-gray-950 via-stone-950/30 to-gray-950 text-white">
      <div
        className="text-center py-4 bg-gray-900/80 border-b border-gray-700"
        style={{ paddingTop: "max(1rem, env(safe-area-inset-top))" }}
      >
        <h1 className="text-xl font-bold text-amber-400">녹림 루트 — 북쪽 강호</h1>
        <p className="text-[13px] text-gray-300 mt-1">
          기혈 {player.hp}/{player.maxHp} · 금자 {player.gold} · 명성 {player.xp}
        </p>
      </div>

      <div className="max-w-4xl mx-auto px-2 sm:px-4 py-3 sm:py-6">
        {/* 노드맵 그리드 — 모바일 노드 44px + gap 4px = 284px, 320px 폭에 fit */}
        <div className="relative bg-gray-900/40 rounded-xl border border-gray-800 p-2 sm:p-6 mb-4">
          {/* 연결선 (SVG) */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
            {mapNodes.map((node) =>
              node.connections.map((cid) => {
                const target = mapNodes.find((n) => n.id === cid);
                if (!target) return null;
                const x1 = (node.col + 0.5) * (100 / cols);
                const y1 = (node.row + 0.5) * (100 / rows);
                const x2 = (target.col + 0.5) * (100 / cols);
                const y2 = (target.row + 0.5) * (100 / rows);
                const bothVisited = node.visited && target.visited;
                return (
                  <line
                    key={`${node.id}-${cid}`}
                    x1={`${x1}%`} y1={`${y1}%`}
                    x2={`${x2}%`} y2={`${y2}%`}
                    stroke={bothVisited ? "#d97706" : "#374151"}
                    strokeWidth="2"
                    strokeDasharray={bothVisited ? "0" : "6 4"}
                  />
                );
              })
            )}
          </svg>

          {/* 노드 그리드 — 모바일은 gap-1 (4px) 로 6열이 320px 내 fit */}
          <div
            className="relative grid gap-1 sm:gap-4"
            style={{
              gridTemplateColumns: `repeat(${cols}, 1fr)`,
              gridAutoRows: "minmax(56px, auto)",
            }}
          >
            {/* 빈 셀 채우기 */}
            {Array.from({ length: cols * rows }).map((_, i) => {
              const col = i % cols;
              const row = Math.floor(i / cols);
              const node = mapNodes.find((n) => n.col === col && n.row === row);

              if (!node) return <div key={i} />;

              const isCurrent = node.id === currentNodeId;
              const isReachable = reachable.includes(node.id);
              const colorClass = NODE_COLORS[node.type];

              return (
                <div key={i} className="flex items-center justify-center" style={{ zIndex: 1 }}>
                  <button
                    disabled={!isReachable}
                    onClick={() => dispatch({ type: "VISIT_NODE", nodeId: node.id })}
                    className={`
                      relative w-11 h-11 sm:w-16 sm:h-16 rounded-lg flex flex-col items-center justify-center
                      transition-all duration-200
                      ${colorClass}
                      ${isCurrent ? "border-4 border-amber-400 scale-110 shadow-lg shadow-amber-500/40" : "border-2"}
                      ${isReachable && !isCurrent ? "border-green-400 ring-2 ring-green-400/50 hover:scale-110 cursor-pointer animate-pulse" : ""}
                      ${node.visited && !isCurrent ? "opacity-50 border-dashed" : ""}
                      ${!isReachable && !node.visited && !isCurrent ? "opacity-30" : ""}
                    `}
                    title={node.label}
                  >
                    <span className="text-sm sm:text-lg leading-none">{node.icon}</span>
                    <span className="text-[10px] sm:text-[11px] text-gray-200 leading-tight mt-0.5 max-w-full truncate px-0.5">{node.label}</span>
                    {isCurrent && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full" />
                    )}
                    {/* 색약 대응: 도달 가능 표시 아이콘 (현재 위치/방문 제외) */}
                    {isReachable && !isCurrent && !node.visited && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-green-500 border border-gray-900 flex items-center justify-center text-[10px] font-bold text-white leading-none">
                        →
                      </div>
                    )}
                    {node.visited && !isCurrent && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-gray-600 border border-gray-900 flex items-center justify-center text-[10px] font-bold text-white leading-none">
                        ✓
                      </div>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* 범례 */}
        <div className="flex flex-wrap justify-center gap-3 text-[13px] text-gray-300 mb-6">
          <span>⚔️ 전투</span>
          <span>🍵 객잔</span>
          <span>⛩️ 연무장</span>
          <span>🏯 도시</span>
          <span>👹 보스</span>
          <span className="text-amber-400">● 현재 위치</span>
        </div>

        {/* 루트 클리어 */}
        {isRouteComplete && (
          <div className="text-center mb-6 p-4 bg-amber-950/40 border border-amber-700 rounded-lg">
            <p className="text-amber-300 font-bold">녹림 루트를 정복했다!</p>
            <button onClick={() => dispatch({ type: "GO_MENU" })}
              className="mt-3 px-6 py-2 bg-amber-800 hover:bg-amber-700 rounded-lg font-bold transition-colors">
              강호 대지로 돌아가다
            </button>
          </div>
        )}

        {/* 플레이어 정보 */}
        <div className="flex justify-center mb-4">
          <PlayerPanel player={player} />
        </div>

        {/* 하단 버튼 */}
        <button onClick={() => dispatch({ type: "GO_MENU" })}
          className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-gray-300 transition-colors">
          강호 대지로 돌아가다
        </button>
      </div>
    </div>
  );
}
