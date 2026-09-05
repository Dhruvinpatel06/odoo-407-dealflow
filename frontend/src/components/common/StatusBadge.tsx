import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const normalized = status.toUpperCase().replace(/\s+/g, '_');

  let textColor = 'text-gray-500';
  let dotColor = 'bg-gray-400';
  let label = status.replace(/_/g, ' ');

  switch (normalized) {
    case 'APPROVED':
    case 'CONFIRMED':
    case 'PAID':
    case 'FULFILLED':
    case 'ACCEPTED':
    case 'HEALTHY':
    case 'ACTIVE':
    case 'RESOLVED':
      textColor = 'text-green-600';
      dotColor = 'bg-green-600';
      break;

    case 'PENDING_APPROVAL':
    case 'PENDING':
    case 'SUGGESTED':
      textColor = 'text-blue-600';
      dotColor = 'bg-blue-600';
      break;

    case 'UNDER_NEGOTIATION':
    case 'UNDER_REV':
    case 'PARTIALLY_PAID':
    case 'PARTIALLY_FULFILLED':
    case 'MODERATE':
    case 'ACKNOWLEDGED':
    case 'ISSUED':
      textColor = 'text-amber-600';
      dotColor = 'bg-amber-600 animate-pulse';
      break;

    case 'REJECTED':
    case 'HIGH_RISK':
    case 'CRITICAL':
    case 'CANCELLED':
    case 'BACKORDERED':
      textColor = 'text-red-600';
      dotColor = 'bg-red-600';
      break;

    case 'RETURNED_FOR_REVISION':
    case 'REVISION_REQUIRED':
    case 'REVISION_REQUESTED':
      textColor = 'text-orange-600';
      dotColor = 'bg-orange-600';
      break;

    case 'SENT':
    case 'DRAFT':
    case 'MANUALLY_OVERRIDDEN':
    default:
      textColor = 'text-gray-500';
      dotColor = 'bg-gray-400';
      break;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${textColor} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />
      <span className="capitalize">{label.toLowerCase()}</span>
    </span>
  );
};
