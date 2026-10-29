import React from 'react';
import type { TraditionScoreEntry } from '../utils/types';

// Upgrade 52 (V7 Phase 3): surfaces ethiviz/metrics/individual_fairness.py's
// "similar inputs should get similar scores" consistency check, run
// per-lens directly on the scores the engine already produced. Only
// present when the job was submitted with advanced_options
// .include_statistical_metrics = true (see ConfigPanel.tsx) and only for a
// lens with enough texts for a meaningful neighbor comparison.
//
// Deliberately does NOT include group fairness (SPD/DI/EOD/AOD from
// ethiviz/metrics/group_fairness.py) or any ethiviz/mitigation/ preview:
// both require protected-attribute group labels — which row belongs to a
// protected group — that nothing in this app collects. Shipping those here
// backed by no real group data would misrepresent what's actually being
// measured; see README.md's "Known limitations."

const TRADITION_LABELS: Record<string, string> = {
  western_v1: 'Western',
  ubuntu_v1: 'Ubuntu',
  confucian_v2: 'Confucian',
  islamic_v1: 'Islamic',
  indigenous_v1: 'Indigenous',
  buddhist_v1: 'Buddhist',
  hindu_v1: 'Hindu / Dharmic',
};

function consistencyColor(score: number): string {
  if (score > 0.75) return '#22c55e';
  if (score > 0.5) return '#f59e0b';
  return '#ef4444';
}

interface StatisticalFairnessPanelProps {
  scores: TraditionScoreEntry[];
}

export const StatisticalFairnessPanel: React.FC<StatisticalFairnessPanelProps> = ({ scores }) => {
  const withMetrics = scores.filter((s) => s.individual_fairness);

  if (withMetrics.length === 0) {
    return null;
  }

  return (
    <div className="p-4 space-y-3">
      <div>
        <h3 className="text-lg font-semibold">Statistical Fairness — Individual Consistency</h3>
        <p className="text-sm text-gray-500 mt-1">
          Do similar inputs receive similar scores from each lens? A low consistency score
          means the lens treated near-identical content inconsistently.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="py-2 pr-4 font-medium">Tradition</th>
              <th className="py-2 pr-4 font-medium">Consistency</th>
              <th className="py-2 pr-4 font-medium">Sample distortion</th>
              <th className="py-2 pr-4 font-medium">k</th>
              <th className="py-2 font-medium">Interpretation</th>
            </tr>
          </thead>
          <tbody>
            {withMetrics.map((s) => {
              const m = s.individual_fairness!;
              return (
                <tr key={s.tradition} className="border-b last:border-0">
                  <td className="py-2 pr-4 whitespace-nowrap">
                    {TRADITION_LABELS[s.tradition] || s.tradition}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className="font-medium"
                      style={{ color: consistencyColor(m.consistency_score) }}
                    >
                      {(m.consistency_score * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 pr-4">{(m.sample_distortion_score * 100).toFixed(1)}%</td>
                  <td className="py-2 pr-4">{m.k_neighbors}</td>
                  <td className="py-2 text-gray-600">{m.interpretation}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StatisticalFairnessPanel;
