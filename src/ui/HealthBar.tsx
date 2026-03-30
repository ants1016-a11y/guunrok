"use client";

interface Props {
  current: number;
  max: number;
  label: string;
  color?: string;
  showDefense?: number;
}

export default function HealthBar({
  current,
  max,
  label,
  color = "bg-red-600",
  showDefense,
}: Props) {
  const pct = Math.max(0, Math.min(100, (current / max) * 100));

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">{label}</span>
        <span className="text-white font-mono">
          {current}/{max}
          {showDefense !== undefined && showDefense > 0 && (
            <span className="text-blue-400 ml-2">🛡️{showDefense}</span>
          )}
        </span>
      </div>
      <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden border border-gray-600">
        <div
          className={`h-full ${color} transition-all duration-500 ease-out rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
