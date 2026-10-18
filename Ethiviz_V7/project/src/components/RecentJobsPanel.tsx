import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface JobSummary {
  job_id: string;
  status: string;
  created_at?: string;
  analysis_type?: string;
}

interface RecentJobsPanelProps {
  apiBaseUrl: string;
}

const getAuthHeaders = () => {
  const apiKey = window.localStorage.getItem('ethiviz_api_key');
  return apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
};

const RecentJobsPanel: React.FC<RecentJobsPanelProps> = ({ apiBaseUrl }) => {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchJobs = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`${apiBaseUrl}/api/jobs`, {
          headers: getAuthHeaders(),
          params: { limit: 5 },
        });
        if (!cancelled) {
          setJobs(response.data.jobs ?? []);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.response?.data?.error || 'Unable to load recent jobs.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchJobs();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-800">Recent Jobs</h3>
        <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">{jobs.length}</span>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading recent jobs…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!loading && !error && jobs.length === 0 && (
        <p className="text-sm text-slate-500">No recent jobs found for this API key.</p>
      )}

      {!loading && !error && jobs.length > 0 && (
        <ul className="space-y-2">
          {jobs.map((job) => (
            <li key={job.job_id} className="flex items-center justify-between gap-3 rounded border border-slate-200 bg-slate-50 px-3 py-2">
              <div>
                <div className="text-sm font-medium text-slate-700">{job.job_id}</div>
                <div className="text-xs text-slate-500">{job.analysis_type ?? 'analysis'} • {job.created_at ?? 'recent'}</div>
              </div>
              <span className="rounded-full bg-blue-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-blue-700">
                {job.status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RecentJobsPanel;
