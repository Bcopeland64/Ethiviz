import React, { useEffect, useMemo, useState } from 'react';
import type { FrameworkCoverageReport } from '../utils/types';

const API_BASE_URL = 'http://localhost:5001';

interface TraditionScore {
  tradition: string;
  score: number;
  severity: string;
  translation_reviewed?: boolean | null;
  warnings?: string[];
}

interface CrossCulturalEquityDashboardProps {
  scores: TraditionScore[];
  synergies?: string[];
  conflicts?: string[];
}

const TRADITION_LABELS: Record<string, string> = {
  western_v1: 'Western',
  ubuntu_v1: 'Ubuntu',
  confucian_v2: 'Confucian',
  islamic_v1: 'Islamic',
  indigenous_v1: 'Indigenous',
  buddhist_v1: 'Buddhist',
  hindu_v1: 'Hindu / Dharmic',
};

function computeCREI(scores: TraditionScore[]): number {
  if (scores.length === 0) return 1.0;
  const mean = scores.reduce((s, t) => s + t.score, 0) / scores.length;
  if (mean === 0) return 1.0;
  const variance = scores.reduce((s, t) => s + Math.pow(t.score - mean, 2), 0) / scores.length;
  const cv = Math.sqrt(variance) / (mean + 1e-9);
  return Math.max(0, 1 - cv);
}

function getDominantTradition(scores: TraditionScore[]): TraditionScore | null {
  if (scores.length === 0) return null;
  return scores.reduce((max, t) => (t.score > max.score ? t : max), scores[0]);
}

export const CrossCulturalEquityDashboard: React.FC<CrossCulturalEquityDashboardProps> = ({
  scores,
  synergies = [],
  conflicts = [],
}) => {
  const crei = useMemo(() => computeCREI(scores), [scores]);
  const dominant = useMemo(() => getDominantTradition(scores), [scores]);
  const maxScore = useMemo(() => Math.max(...scores.map((s) => s.score), 0), [scores]);
  const isDominant = dominant && dominant.score > 0.6 && dominant.score > maxScore * 0.7;

  const creiColor = crei > 0.75 ? '#22c55e' : crei > 0.5 ? '#f59e0b' : '#ef4444';

  // Framework self-audit (Upgrade 36): whether EthiViz's own prototype
  // corpus is balanced across traditions, independent of this run's content.
  const [coverage, setCoverage] = useState<FrameworkCoverageReport | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/api/framework-coverage`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (!cancelled) setCoverage(data); })
      .catch(() => { if (!cancelled) setCoverage(null); });
    return () => { cancelled = true; };
  }, []);
  const fciColor = (fci: number) => (fci > 0.75 ? '#22c55e' : fci > 0.5 ? '#f59e0b' : '#ef4444');

  const traditionsWithTranslationCaveats = scores.filter(
    (s) => s.translation_reviewed === false || s.translation_reviewed === null
  );

  if (!scores || scores.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-sm">
        No cultural lens data available for equity dashboard.
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      <h3 className="text-lg font-semibold">Cross-Cultural Equity Dashboard</h3>

      {/* CREI */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-gray-700">Cultural Representation Equity Index (CREI)</span>
          <span className="text-2xl font-bold" style={{ color: creiColor }}>
            {(crei * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all"
            style={{ width: `${crei * 100}%`, backgroundColor: creiColor }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Measures whether all traditions are proportionately represented.
          High CREI = balanced signal across lenses.
        </p>
      </div>

      {/* Translation review caveats (Upgrade 37) */}
      {traditionsWithTranslationCaveats.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-amber-800">
          <strong>Translation caveat:</strong> scores for{' '}
          {traditionsWithTranslationCaveats
            .map((t) => TRADITION_LABELS[t.tradition] || t.tradition)
            .join(', ')}{' '}
          rely on a non-English translation that is{' '}
          {traditionsWithTranslationCaveats.some((t) => t.translation_reviewed === null)
            ? 'undeclared or unreviewed'
            : 'machine-generated and unreviewed'}
          . Treat these as provisional, not authoritative.
        </div>
      )}

      {/* Lens Balance */}
      <div>
        <h4 className="font-medium text-gray-700 mb-3">Lens Balance Indicator</h4>
        {isDominant && (
          <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-3 text-sm text-amber-800">
            Warning: <strong>{TRADITION_LABELS[dominant.tradition] || dominant.tradition}</strong> dominates the signal ({(dominant.score * 100).toFixed(1)}%). Check for potential analysis bias.
          </div>
        )}
        <div className="space-y-2">
          {scores.map((t) => (
            <div key={t.tradition} className="flex items-center gap-3">
              <div className="w-36 text-sm text-gray-600 shrink-0">
                {TRADITION_LABELS[t.tradition] || t.tradition}
              </div>
              <div className="flex-1 bg-gray-100 rounded-full h-4">
                <div
                  className="h-4 rounded-full"
                  style={{
                    width: `${maxScore > 0 ? (t.score / maxScore) * 100 : 0}%`,
                    backgroundColor: t.score > 0.6 ? '#ef4444' : t.score > 0.3 ? '#f59e0b' : '#22c55e',
                  }}
                />
              </div>
              <div className="w-12 text-right text-sm text-gray-600">
                {(t.score * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Synergy / Conflict */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-50 rounded-lg p-3">
          <div className="font-medium text-green-800 mb-2">Synergies</div>
          {synergies.length === 0 ? (
            <p className="text-sm text-green-600">No synergistic signals detected.</p>
          ) : (
            <ul className="text-sm text-green-700 space-y-1">
              {synergies.map((s, i) => <li key={i}>&#10003; {s}</li>)}
            </ul>
          )}
        </div>
        <div className="bg-red-50 rounded-lg p-3">
          <div className="font-medium text-red-800 mb-2">Conflicts</div>
          {conflicts.length === 0 ? (
            <p className="text-sm text-red-600">No framework conflicts detected.</p>
          ) : (
            <ul className="text-sm text-red-700 space-y-1">
              {conflicts.map((c, i) => <li key={i}>&#9889; {c}</li>)}
            </ul>
          )}
        </div>
      </div>

      {/* Framework Self-Audit (Upgrade 36) */}
      {coverage && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-gray-700">Framework Coverage Index (self-audit)</span>
            <span className="text-2xl font-bold" style={{ color: fciColor(coverage.framework_coverage_index) }}>
              {(coverage.framework_coverage_index * 100).toFixed(1)}%
            </span>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Unlike CREI above (which measures the content being analyzed), this measures
            whether EthiViz's own prototype corpus is equally sized across all 7 traditions.
          </p>
          <div className="space-y-1">
            {coverage.traditions.map((t) => (
              <div key={t.framework_id} className="flex items-center gap-3 text-sm">
                <div className="w-36 text-gray-600 shrink-0">{t.label}</div>
                <div className="w-24 text-gray-500">{t.prototype_count} prototypes</div>
                <div className="text-xs text-gray-400">
                  {t.translations_undeclared
                    ? 'translation review: undeclared'
                    : `translations reviewed: ${t.translations_reviewed}, machine-generated: ${t.translations_machine_generated}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CrossCulturalEquityDashboard;
