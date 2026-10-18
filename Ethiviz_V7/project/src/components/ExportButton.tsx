import React, { useState } from 'react';
import axios from 'axios';

interface ExportButtonProps {
  jobId: string;
  apiBaseUrl: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ jobId, apiBaseUrl }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: 'html' | 'json' | 'pdf') => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.get(
        `${apiBaseUrl}/api/analyze/results/${jobId}/export`,
        {
          params: { format },
          responseType: 'blob',
          headers: (() => {
            const apiKey = window.localStorage.getItem('ethiviz_api_key');
            return apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
          })(),
        }
      );
      const contentType = format === 'html'
        ? 'text/html'
        : format === 'pdf'
          ? 'application/pdf'
          : 'application/json';
      const blob = new Blob([resp.data], { type: contentType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ethiviz_report_${jobId}.${format}`;
      link.setAttribute('aria-label', `Download ${format.toUpperCase()} export for ${jobId}`);
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Export failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <button
        type="button"
        onClick={() => handleExport('html')}
        disabled={loading || !jobId}
        aria-label="Export HTML report"
        className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Exporting...' : 'Export HTML'}
      </button>
      <button
        type="button"
        onClick={() => handleExport('json')}
        disabled={loading || !jobId}
        aria-label="Export JSON report"
        className="px-3 py-1.5 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 disabled:opacity-50"
      >
        Export JSON
      </button>
      <button
        type="button"
        onClick={() => handleExport('pdf')}
        disabled={loading || !jobId}
        aria-label="Export PDF report"
        className="px-3 py-1.5 bg-emerald-600 text-white rounded text-sm hover:bg-emerald-700 disabled:opacity-50"
      >
        Export PDF
      </button>
      {error && <span className="text-red-500 text-sm" role="alert">{error}</span>}
    </div>
  );
};

export default ExportButton;
