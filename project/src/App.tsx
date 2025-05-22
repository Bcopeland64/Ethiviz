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

  // --- START E2E Test Data Injection ---
  const E2E_TEST_MODE = true; // Set to true to use static data

  // Current data for E2E test (can be switched by changing currentTestData assignment)
  const comprehensiveData = { /* ... existing comprehensiveData ... */ }; 
  const textOnlyData = { /* ... existing textOnlyData ... */ };
  const imageOnlyData = { /* ... existing imageOnlyData ... */ };
  const emptyData = null;
  
  const missingFieldsData = {
    text_analysis: [
      { text_id: "txt_miss_001", original_text: "Text with missing bias.", diversity_index: 0.7, western_ethics_score: 7, /* ubuntu_ethics_score: null, */ confucian_ethics_score: 6, islamic_ethics_score: 5 }, // bias_score missing, ubuntu explicitly null (or remove key)
      { text_id: "txt_miss_002", original_text: "Complete text item.", bias_score: 0.4, diversity_index: 0.6, western_ethics_score: 5, ubuntu_ethics_score: 7, confucian_ethics_score: 5, islamic_ethics_score: 8 },
      { text_id: "txt_miss_003", original_text: "Text with no ethics scores.", bias_score: 0.1, diversity_index: 0.5 },
    ],
    image_analysis: {
      "img_miss_001.jpg": {
        analysis: { bias_score: 0.6, /* diversity_index: null, */ western_ethics_score: 7, object_count: 5 }, 
        image_url: "https://via.placeholder.com/150/FFC107/000000?Text=Image_X",
        original_path: "img_miss_001.jpg",
        skin_tone_distribution: { "light": 0.7, "medium": 0.2 }, 
        gender_representation: null,
      },
      "img_miss_002.png": {
        analysis: { bias_score: 0.3, diversity_index: 0.7, western_ethics_score: 4, ubuntu_ethics_score: 8, confucian_ethics_score: 6, islamic_ethics_score: 7, face_count: 1 },
        image_url: "https://via.placeholder.com/150/DC3545/FFFFFF?Text=Image_Y",
        original_path: "img_miss_002.png",
        gender_representation: { "man": 0.5, "woman": 0.4 },
      },
    }
  };

  const currentTestData = missingFieldsData; // <--- SWITCH TEST DATA HERE
  // --- END E2E Test Data Injection ---


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
    if (E2E_TEST_MODE) {
      // In E2E test mode, we might want to switch between different test data sets here
      // For now, it just prevents API calls.
      setAnalysisResults(comprehensiveData); // Default to comprehensive for initial view
      setIsLoading(false);
      setError(null);
      return;
    }
    resetAnalysisState();
    setIsLoading(true);
    // JobId and StatusUrl will be set by ConfigPanel through props
  };

  const handleAnalysisComplete = (results: any) => {
    if (E2E_TEST_MODE) return;
    setAnalysisResults(results);
    setIsLoading(false);
    setJobId(null); // Clear job ID once completed and results fetched
    setStatusUrl(null);
    setPollingAttempts(0);
  };

  const handleAnalysisError = (errorMessage: string) => {
    if (E2E_TEST_MODE) return;
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


  // Effect for initializing E2E test data
  useEffect(() => {
    if (E2E_TEST_MODE) {
      console.log("E2E TEST MODE: Initializing with data:", currentTestData);
      setAnalysisResults(currentTestData);
      setIsLoading(false);
      setError(null);
    }
  }, [E2E_TEST_MODE, currentTestData]); // Runs when currentTestData changes


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