"use client";

import { BattleLog } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

interface Props {
  logs: BattleLog[];
  fill?: boolean;
}

const AT_BOTTOM_THRESHOLD = 40; // px

export default function BattleLogPanel({ logs, fill }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const [pinned, setPinned] = useState(true); // 사용자가 하단에 있을 때만 true
  const [unreadCount, setUnreadCount] = useState(0);

  // 스크롤 이벤트: 하단 근처인지 감지
  const onScroll = () => {
    const c = containerRef.current;
    if (!c) return;
    const atBottom =
      c.scrollHeight - c.scrollTop - c.clientHeight < AT_BOTTOM_THRESHOLD;
    setPinned(atBottom);
    if (atBottom) setUnreadCount(0);
  };

  // 새 로그 들어올 때
  useEffect(() => {
    if (pinned) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
      setUnreadCount(0);
    } else {
      setUnreadCount((n) => n + 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [logs.length]);

  const jumpToBottom = () => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
    setUnreadCount(0);
    setPinned(true);
  };

  return (
    <div className="relative w-full h-full">
      <div
        ref={containerRef}
        onScroll={onScroll}
        className={`w-full ${fill ? "h-full" : "h-48"} overflow-y-auto bg-gray-950/80 rounded-lg border border-gray-700 p-3 text-[13px] font-mono`}
      >
        {logs.map((log, i) => (
          <div key={i} className={`${log.color} mb-1 leading-relaxed`}>
            {log.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* 스크롤 위로 올라가 있을 때만 표시 */}
      {!pinned && unreadCount > 0 && (
        <button
          type="button"
          onClick={jumpToBottom}
          className="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-amber-600 hover:bg-amber-500 text-white text-[12px] font-bold shadow-lg flex items-center gap-1 animate-bounce"
        >
          ↓ 새 로그 {unreadCount}
        </button>
      )}
    </div>
  );
}
