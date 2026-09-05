import React from 'react';

interface RiskBadgeProps {
  score: number;
  status?: 'HEALTHY' | 'MODERATE' | 'HIGH_RISK';
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score, status, showScore = true }) => {
  const calculatedStatus = status || (score >= 70 ? 'HIGH_RISK' : score >= 45 ? 'MODERATE' : 'HEALTHY');

  let badgeClasses = 'bg-green-50 text-green-700';
  let label = 'LOW';

  if (calculatedStatus === 'HIGH_RISK' || score >= 70) {
    badgeClasses = 'bg-red-50 text-red-700';
    label = 'CRITICAL';
  } else if (calculatedStatus === 'MODERATE' || score >= 45) {
    badgeClasses = 'bg-amber-50 text-amber-700';
    label = 'MED';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 text-[10px] font-bold rounded ${badgeClasses}`}>
      <span>{label}</span>
      {showScore && (
        <span className="font-mono text-[9px] opacity-85">
          ({score})
        </span>
      )}
    </span>
  );
};
