import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Menu, X, Settings, Search, Sparkles } from 'lucide-react';
import ConfigPanel from './components/ConfigPanel';
import MainContent from './components/MainContent';

const API_BASE_URL = 'http://localhost:5001'; // Ensure this matches your API server
const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_POLLING_ATTEMPTS = 20; // Max attempts before timing out (e.g., 20 * 3s = 1 minute)


function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Lifted state
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusUrl, setStatusUrl] = useState<string | null>(null); // Store the full status URL from API response
  const [analysisResults, setAnalysisResults] = useState<any | null>(null); // 'any' for now
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingAttempts, setPollingAttempts] = useState(0);

  const resetAnalysisState = () => {
    setJobId(null);
    setStatusUrl(null);
    setAnalysisResults(null);
    setIsLoading(false);
    setError(null);
    setPollingAttempts(0);
  };

  const handleAnalysisStart = () => {
    resetAnalysisState();
    setIsLoading(true);
    // JobId and StatusUrl will be set by ConfigPanel through props
  };

  const handleAnalysisComplete = (results: any) => {
    setAnalysisResults(results);
    setIsLoading(false);
    setJobId(null); // Clear job ID once completed and results fetched
    setStatusUrl(null);
    setPollingAttempts(0);
  };

  const handleAnalysisError = (errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
    setJobId(null); // Clear job ID on error
    setStatusUrl(null);
    setPollingAttempts(0);
  };

  // Callback for ConfigPanel to set JobId and StatusUrl
  const setJobDetails = useCallback((newJobId: string | null, newStatusUrl?: string | null) => {
    setJobId(newJobId);
    if (newStatusUrl) setStatusUrl(newStatusUrl);
    // If newJobId is set, polling will start/restart due to useEffect below
    // If newJobId is null (e.g. from ConfigPanel error before submission), reset polling
    if (!newJobId) {
      setStatusUrl(null);
      setPollingAttempts(0);
    }
  }, []);


  const checkJobStatus = useCallback(async () => {
    if (!statusUrl || !jobId) return;

    if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
      handleAnalysisError(`Analysis timed out after ${MAX_POLLING_ATTEMPTS} attempts. Please check the job status later or try again.`);
      return;
    }

    try {
      console.log(`Polling attempt ${pollingAttempts + 1} for job ${jobId}: ${statusUrl}`);
      const response = await axios.get(statusUrl);
      const data = response.data;

      if (data.status === 'completed') {
        setPollingAttempts(0); // Reset attempts
        // Fetch results from results_url
        if (data.results_url) {
          console.log(`Job ${jobId} completed. Fetching results from: ${data.results_url}`);
          const resultsResponse = await axios.get(data.results_url);
          handleAnalysisComplete(resultsResponse.data.results); // Assuming results are in data.results
        } else {
          throw new Error("Job completed but no results URL provided.");
        }
      } else if (data.status === 'failed') {
        handleAnalysisError(data.error_message || 'Analysis job failed.');
      } else if (data.status === 'processing' || data.status === 'pending') {
        // Continue polling
        setPollingAttempts(prev => prev + 1);
        // Next poll will be triggered by interval in useEffect
      }
    } catch (err: any) {
      console.error("Error during polling:", err);
      // Potentially keep polling for a few more attempts on network errors
      if (pollingAttempts < MAX_POLLING_ATTEMPTS -1) { // Try a few more times
        setPollingAttempts(prev => prev + 1);
      } else {
        handleAnalysisError(err.response?.data?.error || err.message || 'Failed to check job status.');
      }
    }
  }, [statusUrl, jobId, pollingAttempts]);


  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (jobId && statusUrl && (isLoading || pollingAttempts > 0) && pollingAttempts < MAX_POLLING_ATTEMPTS) {
      // Start or continue polling if we have a job ID, status URL, and are still loading/polling
      intervalId = setInterval(checkJobStatus, POLLING_INTERVAL);
    } else if (!jobId || !statusUrl) {
      // If jobId or statusUrl is cleared, ensure polling stops
      setPollingAttempts(0); 
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, statusUrl, isLoading, pollingAttempts, checkJobStatus]);


  return (
    <div className="min-h-screen bg-gray-50">
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