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
  const ratio = max > 0 ? current / max : 0;

  // HP 위험도 (label === "기혈" 일 때만 적용):
  //   >30%: 기본 color
  //   15~30%: 주황 + 느린 펄스 (경고)
  //   <15%:  빨강 + 빠른 펄스 (극위험)
  const isHp = label === "기혈";
  let barColor = color;
  let barPulse = "";
  let textPulse = "";
  if (isHp && ratio <= 0.3 && ratio > 0.15) {
    barColor = "bg-orange-500";
    barPulse = "animate-pulse";
    textPulse = "text-orange-300";
  } else if (isHp && ratio <= 0.15) {
    barColor = "bg-red-500";
    barPulse = "animate-[pulse_0.6s_ease-in-out_infinite]";
    textPulse = "text-red-300 font-bold";
  }

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-200">{label}</span>
        <span className={`text-white font-mono ${textPulse}`}>
          {current}/{max}
          {showDefense !== undefined && showDefense > 0 && (
            <span className="text-blue-300 ml-2">🛡️{showDefense}</span>
          )}
        </span>
      </div>
      <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden border border-gray-600">
        <div
          className={`h-full ${barColor} ${barPulse} transition-all duration-500 ease-out rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
