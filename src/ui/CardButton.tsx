"use client";

import { Card, getCurrentValue } from "@/lib/types";

const TYPE_COLORS: Record<string, string> = {
  공격: "from-red-900/80 to-red-800/60 border-red-600 hover:border-red-400",
  방어: "from-blue-900/80 to-blue-800/60 border-blue-600 hover:border-blue-400",
  기술: "from-emerald-900/80 to-emerald-800/60 border-emerald-600 hover:border-emerald-400",
  약화: "from-purple-900/80 to-purple-800/60 border-purple-600 hover:border-purple-400",
};

const TYPE_ICONS: Record<string, string> = {
  공격: "⚔️",
  방어: "🛡️",
  기술: "✨",
  약화: "☠️",
};

interface Props {
  card: Card;
  onClick: () => void;
  disabled?: boolean;
  isBasic?: boolean;
  isSelected?: boolean; // 1차 탭(선택) 시각 표시 — battle 페이지에서 관리
}

export default function CardButton({ card, onClick, disabled, isBasic, isSelected }: Props) {
  const colors = TYPE_COLORS[card.type] || TYPE_COLORS["공격"];
  const icon = TYPE_ICONS[card.type] || "🃏";
  const value = getCurrentValue(card);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        relative rounded-lg border-2 bg-gradient-to-b ${colors}
        flex flex-col items-center justify-between p-2
        transition-all duration-200 transform
        ${isBasic ? "w-24 h-32 sm:w-28 sm:h-36" : "w-28 h-40 sm:w-36 sm:h-48"}
        ${disabled ? "opacity-40 cursor-not-allowed scale-95" : "hover:scale-105 hover:-translate-y-1 cursor-pointer active:scale-95"}
        ${isSelected ? "ring-4 ring-amber-300 ring-offset-2 ring-offset-gray-950 -translate-y-2 scale-105" : ""}
      `}
    >
      {/* 비용 */}
      <div className="absolute top-1 left-1 w-7 h-7 rounded-full bg-yellow-700 border border-yellow-500 flex items-center justify-center text-sm font-bold text-yellow-200">
        {card.cost}
      </div>

      {/* 숙련도 */}
      {!isBasic && card.mastery > 1 && (
        <div className="absolute top-1 right-1 text-[11px] text-yellow-400">
          {"★".repeat(card.mastery)}
        </div>
      )}

      {/* 선택됨 뱃지 */}
      {isSelected && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full bg-amber-400 text-[11px] font-bold text-gray-900 shadow">
          탭하여 사용
        </div>
      )}

      {/* 아이콘 */}
      <div className="text-3xl mt-4">{icon}</div>

      {/* 이름 */}
      <div className="text-center">
        <div className="text-sm font-bold text-white leading-tight">{card.name}</div>
        {value > 0 && (
          <div className="text-xs text-gray-200 mt-0.5">위력 {value}</div>
        )}
      </div>

      {/* 설명 */}
      <div className="text-[11px] text-gray-300 text-center leading-snug">
        {card.description}
      </div>
    </button>
  );
}
