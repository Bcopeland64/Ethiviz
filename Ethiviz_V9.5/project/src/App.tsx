import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Menu, X, Settings, Search, Sparkles, AlertTriangle, PowerOff } from 'lucide-react';
import ConfigPanel from './components/ConfigPanel';
import MainContent from './components/MainContent';
import { AnalysisResults, AnalysisProgress } from './utils/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5001';
const INITIAL_POLLING_INTERVAL = 1500;
const MAX_POLLING_INTERVAL = 10000;
const MAX_ANALYSIS_WAIT_MS = 30 * 60 * 1000;

const getAuthHeaders = () => {
  const apiKey = window.sessionStorage.getItem('ethiviz_api_key');
  return apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Lifted state
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusUrl, setStatusUrl] = useState<string | null>(null); // Store the full status URL from API response
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [e2eMode, setE2eMode] = useState(false);
  const [lastCompletedJobId, setLastCompletedJobId] = useState<string | null>(null);
  const [stopped, setStopped] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [cancelNotice, setCancelNotice] = useState<string | null>(null);
  const [cancelDisabled, setCancelDisabled] = useState(false);

  // E2E_TEST_MODE is controlled by the checkbox toggle only — never hardcoded true
  const E2E_TEST_MODE = false;


  const resetAnalysisState = () => {
    if (E2E_TEST_MODE) return; // Prevent reset in test mode
    setJobId(null);
    setStatusUrl(null);
    setAnalysisResults(null);
    setIsLoading(false);
    setProgress(null);
    setError(null);
    setCancelled(false);
    setCancelNotice(null);
    setCancelDisabled(false);
  };

  const handleAnalysisStart = () => {
    if (e2eMode) return; // No-op in test mode (no real data to load)
    resetAnalysisState();
    setIsLoading(true);
    setCancelled(false);
    setCancelNotice(null);
    setCancelDisabled(false);
    setProgress({ percent: 0, message: 'Queued' });
    // JobId and StatusUrl will be set by ConfigPanel through props
  };

  const handleAnalysisComplete = useCallback((results: AnalysisResults) => {
    if (e2eMode) return;
    setAnalysisResults(results);
    setIsLoading(false);
    setCancelled(false);
    setProgress(null);
    setLastCompletedJobId(jobId); // Preserve for ExportButton — jobId itself is about to be cleared
    setJobId(null); // Clear job ID once completed and results fetched
    setStatusUrl(null);
  }, [e2eMode, jobId]);

  const handleStop = async () => {
    const confirmed = window.confirm(
      'Stop the EthiViz backend and frontend dev server? ' +
      'You will need to restart them from your terminal (e.g. bash start_ethiviz.sh) to use the app again.'
    );
    if (!confirmed) return;
    try {
      await axios.post(`${API_BASE_URL}/api/stop`);
    } catch {
      // A network error here is expected once the backend actually terminates
      // mid-response — treat it as a successful stop, not a failure.
    }
    setStopped(true);
  };

  const handleAnalysisError = useCallback((errorMessage: string) => {
    if (e2eMode) return;
    setError(errorMessage);
    setIsLoading(false);
    setCancelled(false);
    setProgress(null);
    setJobId(null); // Clear job ID on error
    setStatusUrl(null);
  }, [e2eMode]);

  const handleCancelAnalysis = async () => {
    if (!jobId || cancelDisabled) return;
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/jobs/${encodeURIComponent(jobId)}/cancel`,
        undefined,
        { headers: getAuthHeaders() },
      );
      if (response.data.cancelled) {
        setCancelNotice('Cancellation accepted. Waiting for the job status to update.');
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setCancelNotice('This job is already running and cannot be interrupted; it will continue.');
        setCancelDisabled(true);
        return;
      }
      const message = axios.isAxiosError(err)
        ? err.response?.data?.error || err.message
        : 'Unable to request cancellation.';
      setCancelNotice(message);
    }
  };

  // Callback for ConfigPanel to set JobId and StatusUrl
  const setJobDetails = useCallback((newJobId: string | null, newStatusUrl?: string | null) => {
    if (E2E_TEST_MODE) return;
    setJobId(newJobId);
    if (newStatusUrl) setStatusUrl(newStatusUrl);
    if (!newJobId) {
      setStatusUrl(null);
    }
  }, [E2E_TEST_MODE]);


  // useEffect for polling - disabled in E2E_TEST_MODE
  useEffect(() => {
    if (E2E_TEST_MODE) return;

    if (!jobId || !statusUrl) return;
    let active = true;
    let timerId: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    const startedAt = Date.now();
    let lastProgress: AnalysisProgress | null = null;
    const scheduleNextPoll = () => {
      const delay = Math.min(
        INITIAL_POLLING_INTERVAL * Math.pow(1.5, attempts),
        MAX_POLLING_INTERVAL,
      );
      timerId = setTimeout(checkJobStatus, delay);
    };
    const checkJobStatus = async () => {
      if (!active) return;
      if (Date.now() - startedAt >= MAX_ANALYSIS_WAIT_MS) {
        handleAnalysisError('Analysis exceeded the 30-minute wait limit. Check recent jobs before retrying.');
        return;
      }
      try {
        const response = await axios.get(statusUrl, { headers: getAuthHeaders() });
        if (!active) return;
        const data = response.data;
        if (data.progress) {
          lastProgress = data.progress;
          setProgress(data.progress);
        }
        if (data.status === 'completed') {
          if (data.results_url) {
            const resultsResponse = await axios.get(data.results_url, { headers: getAuthHeaders() });
            if (active) handleAnalysisComplete(resultsResponse.data.results);
          } else {
            handleAnalysisError('Job completed but no results URL was returned.');
          }
        } else if (data.status === 'failed') {
          handleAnalysisError(data.error_message || 'Analysis job failed.');
        } else if (data.status === 'cancelled') {
          setIsLoading(false);
          setProgress(null);
          setCancelled(true);
          setJobId(null);
          setStatusUrl(null);
        } else if (data.status === 'processing' || data.status === 'pending') {
          attempts += 1;
          scheduleNextPoll();
        } else {
          handleAnalysisError('Unknown job status from API.');
        }
      } catch (err: unknown) {
        if (!active) return;
        console.error('Error during polling:', err);
        if (axios.isAxiosError(err) && err.response && err.response.status < 500
          && err.response.status !== 429) {
          const message = err.response.data?.error || err.message;
          handleAnalysisError(`Could not check analysis status: ${message}`);
          return;
        }
        attempts += 1;
        setProgress({
          percent: lastProgress?.percent ?? 0,
          message: 'Unable to check job status; retrying.',
        });
        scheduleNextPoll();
      }
    };

    void checkJobStatus();
    
    return () => {
      active = false;
      if (timerId !== undefined) clearTimeout(timerId);
    };
  }, [jobId, statusUrl, E2E_TEST_MODE, handleAnalysisComplete, handleAnalysisError]);


  return (
    <div className="min-h-screen bg-gray-50">
      {/* E2E Mode Banner & Toggle */}
      <div className="w-full bg-yellow-100 text-yellow-800 px-4 py-2 flex items-center gap-4 border-b border-yellow-300" style={{display: 'flex', alignItems: 'center'}}>
        <input type="checkbox" id="e2e-toggle" checked={e2eMode} onChange={() => setE2eMode(v => !v)} className="mr-2" />
        <label htmlFor="e2e-toggle" className="font-semibold cursor-pointer">E2E Test Mode</label>
        {e2eMode && <span className="ml-4 text-sm">E2E mode is enabled. No real API calls will be made.</span>}
        {e2eMode && <AlertTriangle className="ml-2 text-yellow-500" size={18} />}
      </div>
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-lg bg-white/80">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative group"
            >
              <div className="absolute inset-0 bg-blue-500/10 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                <Sparkles className="text-white" size={20} />
              </div>
              <h1 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                EthiViz Dashboard
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative group">
              <div className="absolute inset-0 bg-blue-500/5 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="search"
                placeholder="Search analysis..."
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-transparent relative transition-all duration-300 w-48 focus:w-64"
              />
            </div>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all duration-300 relative group">
              <div className="absolute inset-0 bg-blue-500/10 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              <Settings size={20} className="text-gray-600 transition-transform duration-300 group-hover:rotate-90" />
            </button>
            {isLoading && jobId && (
              <button
                type="button"
                onClick={handleCancelAnalysis}
                disabled={cancelDisabled}
                aria-label="Cancel analysis"
                className="rounded border border-amber-300 px-3 py-2 text-sm text-amber-800 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Cancel analysis
              </button>
            )}
            <button
              onClick={handleStop}
              title="Stop EthiViz (shuts down backend and frontend)"
              className="p-2 hover:bg-red-100 rounded-lg transition-all duration-300 relative group"
            >
              <div className="absolute inset-0 bg-red-500/10 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              <PowerOff size={20} className="text-red-600" />
            </button>
          </div>
        </div>
      </header>
      {cancelNotice && (
        <p className="sr-only" role="status" aria-live="polite">{cancelNotice}</p>
      )}

      {stopped ? (
        <div className="flex flex-col items-center justify-center text-center p-16 text-gray-600">
          <PowerOff className="w-16 h-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-semibold mb-2">EthiViz has been stopped</h2>
          <p>Restart it from your terminal (e.g. <code>bash start_ethiviz.sh</code>) to continue.</p>
        </div>
      ) : (
      <div className="flex">
        {/* Sidebar */}
        <ConfigPanel
          isOpen={sidebarOpen}
          onAnalysisStart={handleAnalysisStart}
          onAnalysisComplete={handleAnalysisComplete} // This might not be directly called by ConfigPanel anymore
          onAnalysisError={handleAnalysisError}     // This might not be directly called by ConfigPanel anymore
          setIsLoadingGlobal={setIsLoading}         // ConfigPanel sets global loading
          setJobIdGlobal={setJobDetails}            // ConfigPanel sets job ID and status URL
          e2eMode={e2eMode}
          isLoading={isLoading}
        />

        {/* Main Content */}
        <MainContent
          sidebarOpen={sidebarOpen}
          analysisResults={analysisResults}
          isLoading={isLoading}
          progress={progress}
          error={error}
          cancelled={cancelled}
          apiBaseUrl={API_BASE_URL}
          lastCompletedJobId={lastCompletedJobId}
        />
      </div>
      )}
    </div>
  );
}

export default App;