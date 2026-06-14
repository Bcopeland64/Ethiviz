import React, { useState } from 'react';
import axios from 'axios';

interface TraditionComparison {
  spd_before: number | null;
  spd_after: number | null;
  improvement: number | null;
  severity_before: string | null;
  severity_after: string | null;
}

interface CompareResult {
  per_tradition_comparison: Record<string, TraditionComparison>;
  summary: string;
}

interface CompareModeProps {
  apiBaseUrl: string;
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

const SEVERITY_COLOR: Record<string, string> = {
  low: 'text-green-600',
  moderate: 'text-yellow-600',
  high: 'text-orange-600',
  critical: 'text-red-700',
};

export const CompareMode: React.FC<CompareModeProps> = ({ apiBaseUrl }) => {
  const [jobIdA, setJobIdA] = useState('');
  const [jobIdB, setJobIdB] = useState('');
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!jobIdA.trim() || !jobIdB.trim()) {
      setError('Please enter both Job ID A and Job ID B.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await axios.post(`${apiBaseUrl}/api/compare`, {
        job_id_a: jobIdA.trim(),
        job_id_b: jobIdB.trim(),
      });
      setResult(resp.data);
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Comparison failed. Please check the job IDs.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <h3 className="text-lg font-semibold">Dataset Comparison Mode</h3>
      <p className="text-sm text-gray-600">
        Compare two completed analysis jobs side-by-side across all cultural ethical traditions.
        Enter the Job IDs from previous analyses.
      </p>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dataset A — Job ID
          </label>
          <input
            type="text"
            value={jobIdA}
            onChange={(e) => setJobIdA(e.target.value)}
            placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dataset B — Job ID
          </label>
          <input
            type="text"
            value={jobIdB}
            onChange={(e) => setJobIdB(e.target.value)}
            placeholder="e.g. 7c9e6679-7425-40de-944b-e07fc1f90ae7"
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <button
        onClick={handleCompare}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Comparing...' : 'Compare Datasets'}
      </button>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
            {result.summary}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="text-left px-3 py-2 border border-gray-200 font-medium">Tradition</th>
                  <th className="text-center px-3 py-2 border border-gray-200 font-medium">
                    Dataset A — SPD
                  </th>
                  <th className="text-center px-3 py-2 border border-gray-200 font-medium">
                    Dataset A — Severity
                  </th>
                  <th className="text-center px-3 py-2 border border-gray-200 font-medium">
                    Dataset B — SPD
                  </th>
                  <th className="text-center px-3 py-2 border border-gray-200 font-medium">
                    Dataset B — Severity
                  </th>
                  <th className="text-center px-3 py-2 border border-gray-200 font-medium">
                    Improvement
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.per_tradition_comparison).map(([tid, comp]) => {
                  const improvement = comp.improvement;
                  const improved = improvement !== null && improvement > 0;
                  const worsened = improvement !== null && improvement < 0;
                  return (
                    <tr key={tid} className="hover:bg-gray-50">
                      <td className="px-3 py-2 border border-gray-200 font-medium">
                        {TRADITION_LABELS[tid] || tid}
                      </td>
                      <td className="px-3 py-2 border border-gray-200 text-center font-mono">
                        {comp.spd_before !== null ? comp.spd_before.toFixed(3) : 'N/A'}
                      </td>
                      <td className={`px-3 py-2 border border-gray-200 text-center font-medium ${SEVERITY_COLOR[comp.severity_before || ''] || 'text-gray-600'}`}>
                        {comp.severity_before || 'N/A'}
                      </td>
                      <td className="px-3 py-2 border border-gray-200 text-center font-mono">
                        {comp.spd_after !== null ? comp.spd_after.toFixed(3) : 'N/A'}
                      </td>
                      <td className={`px-3 py-2 border border-gray-200 text-center font-medium ${SEVERITY_COLOR[comp.severity_after || ''] || 'text-gray-600'}`}>
                        {comp.severity_after || 'N/A'}
                      </td>
                      <td className={`px-3 py-2 border border-gray-200 text-center font-mono font-semibold ${improved ? 'text-green-600' : worsened ? 'text-red-600' : 'text-gray-600'}`}>
                        {improvement !== null
                          ? `${improved ? '+' : ''}${improvement.toFixed(3)}`
                          : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="text-xs text-gray-500">
            SPD = Statistical Parity Difference. Positive improvement = reduced bias gap between groups.
          </p>
        </div>
      )}
    </div>
  );
};

export default CompareMode;
