import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Menu, X, Settings, Search, Sparkles, AlertTriangle } from 'lucide-react';
import ConfigPanel from './components/ConfigPanel';
import MainContent from './components/MainContent';
import { AnalysisResults } from './utils/types';

const API_BASE_URL = 'http://localhost:5001'; // Ensure this matches your API server
const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_POLLING_ATTEMPTS = 20; // Max attempts before timing out (e.g., 20 * 3s = 1 minute)


function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Lifted state
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusUrl, setStatusUrl] = useState<string | null>(null); // Store the full status URL from API response
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingAttempts, setPollingAttempts] = useState(0);
  const [e2eMode, setE2eMode] = useState(false);

  // E2E_TEST_MODE is controlled by the checkbox toggle only — never hardcoded true
  const E2E_TEST_MODE = false;


  const resetAnalysisState = () => {
    if (E2E_TEST_MODE) return; // Prevent reset in test mode
    setJobId(null);
    setStatusUrl(null);
    setAnalysisResults(null);
    setIsLoading(false);
    setError(null);
    setPollingAttempts(0);
  };

  const handleAnalysisStart = () => {
    if (e2eMode) return; // No-op in test mode (no real data to load)
    resetAnalysisState();
    setIsLoading(true);
    // JobId and StatusUrl will be set by ConfigPanel through props
  };

  const handleAnalysisComplete = (results: AnalysisResults) => {
    if (e2eMode) return;
    setAnalysisResults(results);
    setIsLoading(false);
    setJobId(null); // Clear job ID once completed and results fetched
    setStatusUrl(null);
    setPollingAttempts(0);
  };

  const handleAnalysisError = (errorMessage: string) => {
    if (e2eMode) return;
    setError(errorMessage);
    setIsLoading(false);
    setJobId(null); // Clear job ID on error
    setStatusUrl(null);
    setPollingAttempts(0);
  };

  // Callback for ConfigPanel to set JobId and StatusUrl
  const setJobDetails = useCallback((newJobId: string | null, newStatusUrl?: string | null) => {
    if (E2E_TEST_MODE) return;
    setJobId(newJobId);
    if (newStatusUrl) setStatusUrl(newStatusUrl);
    if (!newJobId) {
      setStatusUrl(null);
      setPollingAttempts(0);
    }
  }, [E2E_TEST_MODE]);


  // useEffect for polling - disabled in E2E_TEST_MODE
  useEffect(() => {
    if (E2E_TEST_MODE) return;

    let intervalId: NodeJS.Timeout | null = null;
    const checkJobStatus = async () => { // Defined inside useEffect or ensure it's stable
        if (!statusUrl || !jobId) return;
        if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
          handleAnalysisError(`Analysis timed out after ${MAX_POLLING_ATTEMPTS} attempts.`);
          return;
        }
        try {
          console.log(`Polling attempt ${pollingAttempts + 1} for job ${jobId}: ${statusUrl}`);
          const response = await axios.get(statusUrl);
          const data = response.data;
          if (data.status === 'completed') {
            setPollingAttempts(0);
            if (data.results_url) {
              const resultsResponse = await axios.get(data.results_url);
              handleAnalysisComplete(resultsResponse.data.results);
            } else { throw new Error("Job completed but no results URL."); }
          } else if (data.status === 'failed') {
            handleAnalysisError(data.error_message || 'Analysis job failed.');
          } else if (data.status === 'processing' || data.status === 'pending') {
            setPollingAttempts(prev => prev + 1);
          } else {
            handleAnalysisError('Unknown job status from API.');
          }
        } catch (err: any) {
          console.error("Error during polling:", err);
          if (pollingAttempts < MAX_POLLING_ATTEMPTS -1) {
            setPollingAttempts(prev => prev + 1);
          } else {
            handleAnalysisError(err.response?.data?.error || err.message || 'Failed to check job status.');
          }
        }
      };

    if (jobId && statusUrl && (isLoading || pollingAttempts > 0) && pollingAttempts < MAX_POLLING_ATTEMPTS) {
      intervalId = setInterval(checkJobStatus, POLLING_INTERVAL);
    } else if (!jobId || !statusUrl) {
      setPollingAttempts(0); 
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, statusUrl, isLoading, pollingAttempts, E2E_TEST_MODE]); // Added E2E_TEST_MODE and checkJobStatus dependencies


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
          </div>
        </div>
      </header>

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
        />

        {/* Main Content */}
        <MainContent 
          sidebarOpen={sidebarOpen}
          analysisResults={analysisResults}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}

export default App;