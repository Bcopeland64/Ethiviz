import React, { useState } from 'react';
import type { ConstructReading } from '../utils/types';

// Upgrade 51 (V7 Phase 3): surfaces ethiviz/frameworks/dimension_map.py's
// CrossCulturalDimensionMap output — computed by Analyzer.analyze() since
// V6, but discarded before it ever reached the API response. This is
// EthiViz's most distinctive output: which shared moral constructs a
// dataset triggers, and whether the 7 traditions converge on it
// (consensus) or only one flags a harm the others don't encode
// (tradition-specific) — the "5 of 7 traditions agree" vs. "only the
// Indigenous lens flagged this" differentiator the dimension map was built
// to expose.

const TRADITION_LABELS: Record<string, string> = {
  western_v1: 'Western',
  ubuntu_v1: 'Ubuntu',
  confucian_v2: 'Confucian',
  islamic_v1: 'Islamic',
  indigenous_v1: 'Indigenous',
  buddhist_v1: 'Buddhist',
  hindu_v1: 'Hindu / Dharmic',
};

function lensLabel(lensId: string): string {
  return TRADITION_LABELS[lensId] || lensId;
}

interface DimensionFindingsPanelProps {
  consensusFindings: ConstructReading[];
  traditionSpecificFindings: ConstructReading[];
}

const ReadingCard: React.FC<{ reading: ConstructReading; accent: 'blue' | 'amber' }> = ({ reading, accent }) => {
  const [expanded, setExpanded] = useState(false);
  const accentClasses =
    accent === 'blue'
      ? 'bg-blue-50 border-blue-200 text-blue-800'
      : 'bg-amber-50 border-amber-200 text-amber-800';

  return (
    <div className={`rounded-lg border p-3 ${accentClasses}`}>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full text-left"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="font-medium">{reading.description}</span>
          <span className="text-xs shrink-0">
            {accent === 'blue'
              ? `${reading.flagged_lenses.length} of ${reading.contributing_lenses.length} lenses`
              : lensLabel(reading.distinctive_lens || '')}
          </span>
        </div>
      </button>
      {expanded && (
        <div className="mt-2 space-y-2 text-sm">
          <p>{reading.interpretation}</p>
          <div className="flex flex-wrap gap-2">
            {reading.contributing_lenses.map((lensId) => (
              <span
                key={lensId}
                className={`px-2 py-0.5 rounded-full text-xs ${
                  reading.flagged_lenses.includes(lensId)
                    ? 'bg-white/70 font-medium'
                    : 'bg-white/30 text-opacity-60'
                }`}
              >
                {lensLabel(lensId)}: {(reading.scores[lensId] ?? 0).toFixed(2)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export const DimensionFindingsPanel: React.FC<DimensionFindingsPanelProps> = ({
  consensusFindings,
  traditionSpecificFindings,
}) => {
  if (consensusFindings.length === 0 && traditionSpecificFindings.length === 0) {
    return null;
  }

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Cross-Cultural Dimension Findings</h3>
        <p className="text-sm text-gray-500 mt-1">
          Shared moral constructs read at the dimension level across all 7 lenses, not just
          each tradition's single overall score.
        </p>
      </div>

      <div>
        <h4 className="font-medium text-gray-700 mb-2">
          Consensus findings ({consensusFindings.length})
        </h4>
        {consensusFindings.length === 0 ? (
          <p className="text-sm text-gray-500">No construct was flagged by multiple traditions.</p>
        ) : (
          <div className="space-y-2">
            {consensusFindings.map((r) => (
              <ReadingCard key={r.construct_id} reading={r} accent="blue" />
            ))}
          </div>
        )}
      </div>

      <div>
        <h4 className="font-medium text-gray-700 mb-2">
          Tradition-specific findings ({traditionSpecificFindings.length})
        </h4>
        {traditionSpecificFindings.length === 0 ? (
          <p className="text-sm text-gray-500">
            No construct was flagged by only a single tradition.
          </p>
        ) : (
          <div className="space-y-2">
            {traditionSpecificFindings.map((r) => (
              <ReadingCard key={r.construct_id} reading={r} accent="amber" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DimensionFindingsPanel;
