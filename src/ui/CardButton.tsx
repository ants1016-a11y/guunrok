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
}

export default function CardButton({ card, onClick, disabled, isBasic }: Props) {
  const colors = TYPE_COLORS[card.type] || TYPE_COLORS["공격"];
  const icon = TYPE_ICONS[card.type] || "🃏";
  const value = getCurrentValue(card);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        relative w-36 h-48 rounded-lg border-2 bg-gradient-to-b ${colors}
        flex flex-col items-center justify-between p-3
        transition-all duration-200 transform
        ${disabled ? "opacity-40 cursor-not-allowed scale-95" : "hover:scale-105 hover:-translate-y-1 cursor-pointer active:scale-95"}
        ${isBasic ? "w-28 h-36" : ""}
      `}
    >
      {/* 비용 */}
      <div className="absolute top-1 left-2 w-7 h-7 rounded-full bg-yellow-700 border border-yellow-500 flex items-center justify-center text-sm font-bold text-yellow-200">
        {card.cost}
      </div>

      {/* 숙련도 */}
      {!isBasic && card.mastery > 1 && (
        <div className="absolute top-1 right-2 text-xs text-yellow-400">
          {"★".repeat(card.mastery)}
        </div>
      )}

      {/* 아이콘 */}
      <div className="text-3xl mt-4">{icon}</div>

      {/* 이름 */}
      <div className="text-center">
        <div className="text-sm font-bold text-white">{card.name}</div>
        {value > 0 && (
          <div className="text-xs text-gray-300 mt-0.5">위력 {value}</div>
        )}
      </div>

      {/* 설명 */}
      <div className="text-[10px] text-gray-400 text-center leading-tight">
        {card.description}
      </div>
    </button>
  );
}
