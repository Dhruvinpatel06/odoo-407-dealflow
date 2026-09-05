import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: LucideIcon;
  badge?: string;
  borderAccent?: boolean;
  onClick?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  change,
  changeType = 'neutral',
  icon: Icon,
  badge,
  borderAccent,
  onClick
}) => {
  const isNegativeOrAlert = borderAccent || changeType === 'negative' || title.toLowerCase().includes('risk');

  return (
    <div 
      onClick={onClick}
      className={`bg-white p-5 rounded-xl border border-gray-100 shadow-sm transition-all duration-150 ${
        isNegativeOrAlert ? 'border-l-4 border-l-red-500' : ''
      } ${
        onClick ? 'cursor-pointer hover:border-gray-300 hover:shadow-md' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">{title}</p>
        <div className="w-8 h-8 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-500">
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-3 mt-1">
        <p className={`text-2xl font-bold tracking-tight ${isNegativeOrAlert ? 'text-red-600' : 'text-[#111827]'}`}>
          {value}
        </p>
        {badge && (
          <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] rounded-full font-bold uppercase">
            {badge}
          </span>
        )}
      </div>

      {(subtitle || change) && (
        <div className="mt-2 flex items-center gap-1.5 text-xs">
          {change && (
            <span
              className={`font-medium ${
                changeType === 'positive'
                  ? 'text-green-600'
                  : changeType === 'negative'
                  ? 'text-amber-600'
                  : 'text-gray-600'
              }`}
            >
              {change}
            </span>
          )}
          {subtitle && (
            <span className={isNegativeOrAlert ? 'text-[10px] text-gray-400' : 'text-gray-500'}>
              {change ? `• ${subtitle}` : subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
