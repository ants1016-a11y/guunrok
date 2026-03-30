"use client";

import { BattleLog } from "@/lib/types";
import { useEffect, useRef } from "react";

interface Props {
  logs: BattleLog[];
}

export default function BattleLogPanel({ logs }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="w-full h-48 overflow-y-auto bg-gray-950/80 rounded-lg border border-gray-700 p-3 text-sm font-mono">
      {logs.map((log, i) => (
        <div key={i} className={`${log.color} mb-1 leading-relaxed`}>
          {log.text}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
