import React from 'react';

export interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  colorClass?: string; // Optional for custom color
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, description, icon, colorClass }) => (
  <div className="bg-white p-4 shadow rounded-lg flex items-start space-x-3">
    {icon && <div className={`flex-shrink-0 h-10 w-10 rounded-full ${colorClass || 'bg-blue-500'} flex items-center justify-center text-white`}>{icon}</div>}
    <div>
      <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
      {description && <p className="text-xs text-gray-400">{description}</p>}
    </div>
  </div>
);

export default MetricCard; 