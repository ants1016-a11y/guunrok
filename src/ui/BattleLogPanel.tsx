"use client";

import { BattleLog } from "@/lib/types";
import { useEffect, useRef } from "react";

interface Props {
  logs: BattleLog[];
  fill?: boolean; // true 면 부모 높이 100% 사용 (sticky 레이아웃용)
}

export default function BattleLogPanel({ logs, fill }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const heightClass = fill ? "h-full" : "h-48";

  return (
    <div
      className={`w-full ${heightClass} overflow-y-auto bg-gray-950/80 rounded-lg border border-gray-700 p-3 text-[13px] font-mono`}
    >
      {logs.map((log, i) => (
        <div key={i} className={`${log.color} mb-1 leading-relaxed`}>
          {log.text}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
