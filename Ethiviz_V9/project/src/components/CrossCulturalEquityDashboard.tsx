import React, { useEffect, useState } from 'react';
import type { FrameworkCoverageReport } from '../utils/types';

// See ConfigPanel.tsx's API_BASE_URL comment — same VITE_API_BASE_URL
// override, kept in sync so both talk to the same origin.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5001';

interface TraditionScore {
  tradition: string;
  score: number;
  severity: string;
  confidence?: number;
  analysis_coverage?: number;
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

export const CrossCulturalEquityDashboard: React.FC<CrossCulturalEquityDashboardProps> = ({
  scores,
  synergies = [],
  conflicts = [],
}) => {
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

      <div className="bg-gray-50 rounded-lg p-4">
        <p className="font-medium text-gray-700">Job-level lens scores (descriptive)</p>
        <p className="text-xs text-gray-500 mt-1">
          Scores are not percentages or directly comparable measures of cultural
          representation. Each lens encodes different constructs; review its evidence,
          severity, confidence, and coverage rather than expecting scores to match.
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

      <div>
        <h4 className="font-medium text-gray-700 mb-3">Per-lens score and severity</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2 pr-4 font-medium">Tradition</th>
                <th className="py-2 pr-4 font-medium">Score</th>
                <th className="py-2 pr-4 font-medium">Severity</th>
                <th className="py-2 pr-4 font-medium">Confidence</th>
                <th className="py-2 font-medium">Coverage</th>
              </tr>
            </thead>
            <tbody>
          {scores.map((t) => (
            <tr key={t.tradition} className="border-b last:border-0">
              <td className="py-2 pr-4">{TRADITION_LABELS[t.tradition] || t.tradition}</td>
              <td className="py-2 pr-4 font-mono">{t.score.toFixed(4)}</td>
              <td className="py-2 pr-4 capitalize">{t.severity}</td>
              <td className="py-2 pr-4">{t.confidence?.toFixed(3) ?? '—'}</td>
              <td className="py-2">{t.analysis_coverage?.toFixed(3) ?? '1.000'}</td>
            </tr>
          ))}
            </tbody>
          </table>
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
            This measures
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
