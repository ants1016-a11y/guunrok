// ─── 노드 타입 ──────────────────────────────────────────────
export type NodeType = "combat" | "inn" | "training" | "city" | "boss";

export interface MapNode {
  id: number;
  type: NodeType;
  label: string;
  icon: string;
  connections: number[]; // 이동 가능한 다음 노드 ID
  tier: number;          // 1=졸개, 2=대장, 3=장로, 5=보스
  visited: boolean;
  col: number;           // 열 (0~5), 표시 위치용
  row: number;           // 행 (0~2), 표시 위치용
}

// ─── 녹림 루트 노드 그래프 ──────────────────────────────────
export function generateNorthRoute(): MapNode[] {
  return [
    // Col 0: 출발
    { id: 0, type: "city",     label: "청운성",       icon: "🏯", connections: [1, 2],  tier: 0, visited: true, col: 0, row: 1 },

    // Col 1: 첫 분기
    { id: 1, type: "combat",   label: "북산길",       icon: "⚔️", connections: [3, 4],  tier: 1, visited: false, col: 1, row: 0 },
    { id: 2, type: "combat",   label: "관도",         icon: "⚔️", connections: [4, 5],  tier: 1, visited: false, col: 1, row: 2 },

    // Col 2: 두 번째 분기
    { id: 3, type: "inn",      label: "주막",         icon: "🍵", connections: [6],     tier: 0, visited: false, col: 2, row: 0 },
    { id: 4, type: "combat",   label: "산채 입구",    icon: "⚔️", connections: [6, 7],  tier: 2, visited: false, col: 2, row: 1 },
    { id: 5, type: "combat",   label: "협곡",         icon: "⚔️", connections: [7],     tier: 2, visited: false, col: 2, row: 2 },

    // Col 3: 세 번째 분기
    { id: 6, type: "training", label: "무관",         icon: "⛩️", connections: [8],     tier: 0, visited: false, col: 3, row: 0 },
    { id: 7, type: "combat",   label: "녹림 거점",    icon: "⚔️", connections: [8],     tier: 3, visited: false, col: 3, row: 2 },

    // Col 4: 합류
    { id: 8, type: "combat",   label: "산채 심부",    icon: "⚔️", connections: [9],     tier: 3, visited: false, col: 4, row: 1 },

    // Col 5: 보스
    { id: 9, type: "boss",     label: "마천광의 산채", icon: "👹", connections: [],      tier: 5, visited: false, col: 5, row: 1 },
  ];
}

// ─── 노드 위치를 접근 가능한지 판정 ─────────────────────────
export function getReachableNodes(nodes: MapNode[], currentId: number): number[] {
  const current = nodes.find((n) => n.id === currentId);
  if (!current) return [];
  return current.connections.filter((cid) => {
    const target = nodes.find((n) => n.id === cid);
    return target && !target.visited;
  });
}

// ─── 노드 타입별 색상 ──────────────────────────────────────
export const NODE_COLORS: Record<NodeType, string> = {
  combat:   "border-red-600 bg-red-950/60",
  inn:      "border-emerald-600 bg-emerald-950/60",
  training: "border-indigo-600 bg-indigo-950/60",
  city:     "border-amber-600 bg-amber-950/60",
  boss:     "border-red-500 bg-red-900/80 ring-2 ring-red-500/50",
};
