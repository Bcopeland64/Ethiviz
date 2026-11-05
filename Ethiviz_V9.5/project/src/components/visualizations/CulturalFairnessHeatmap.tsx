import React from 'react';

interface HeatmapData {
  tradition: string;
  severity: 'low' | 'moderate' | 'high' | 'critical' | 'unknown';
  score: number;
}

interface CulturalFairnessHeatmapProps {
  data: HeatmapData[];
  title?: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  low: '#22c55e',
  moderate: '#f59e0b',
  high: '#ef4444',
  critical: '#7f1d1d',
  unknown: '#94a3b8',
};

const TRADITION_LABELS: Record<string, string> = {
  western_v1: 'Western',
  ubuntu_v1: 'Ubuntu',
  confucian_v2: 'Confucian',
  islamic_v1: 'Islamic',
  indigenous_v1: 'Indigenous',
  buddhist_v1: 'Buddhist',
  hindu_v1: 'Hindu / Dharmic',
};

export const CulturalFairnessHeatmap: React.FC<CulturalFairnessHeatmapProps> = ({
  data,
  title = 'Cultural Fairness Severity Heatmap',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-sm">
        No fairness data available for heatmap.
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-3">{title}</h3>
      <p className="text-sm text-gray-600 mb-4">
        Shows which ethical traditions flag the analysed content at each severity level.
        A dataset may pass Western thresholds but trigger critical severity under Ubuntu
        community-harm criteria.
      </p>
      <div className="grid grid-cols-1 gap-2">
        {data.map((item) => (
          <div key={item.tradition} className="flex items-center gap-3">
            <div className="w-40 text-sm font-medium text-gray-700 shrink-0">
              {TRADITION_LABELS[item.tradition] || item.tradition}
            </div>
            <div
              className="flex-1 h-8 rounded flex items-center justify-center text-white text-sm font-semibold"
              style={{ backgroundColor: SEVERITY_COLORS[item.severity] || SEVERITY_COLORS.unknown }}
            >
              {item.severity.toUpperCase()}
            </div>
            <div className="w-16 text-right text-sm text-gray-600">
              {(item.score * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-4 flex-wrap">
        {Object.entries(SEVERITY_COLORS).filter(([k]) => k !== 'unknown').map(([sev, color]) => (
          <div key={sev} className="flex items-center gap-1 text-xs text-gray-600">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
            {sev.charAt(0).toUpperCase() + sev.slice(1)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CulturalFairnessHeatmap;
