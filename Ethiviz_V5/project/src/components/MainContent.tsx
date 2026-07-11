import React from 'react';
import WelcomeMessage from './WelcomeMessage';
import { Loader2, AlertTriangle } from 'lucide-react';
import TextAnalysisVisuals from './visualizations/TextAnalysisVisuals';
import ImageAnalysisVisuals from './visualizations/ImageAnalysisVisuals';
import CombinedAnalysisVisuals from './visualizations/CombinedAnalysisVisuals';
import CulturalFairnessHeatmap from './visualizations/CulturalFairnessHeatmap';
import CrossCulturalEquityDashboard from './CrossCulturalEquityDashboard';
import ExportButton from './ExportButton';
import CompareMode from './CompareMode';
import { AnalysisResults, AnalysisProgress, TextAnalysisItem, ImageAnalysisItem } from '../utils/types';

interface MainContentProps {
  sidebarOpen: boolean;
  analysisResults: AnalysisResults | null;
  isLoading: boolean;
  progress?: AnalysisProgress | null;
  error: string | null;
  apiBaseUrl: string;
  lastCompletedJobId: string | null;
}

function MainContent({ sidebarOpen, analysisResults, isLoading, progress, error, apiBaseUrl, lastCompletedJobId }: MainContentProps) {
  const renderContent = () => {
    if (isLoading) {
      const percent = Math.max(0, Math.min(100, progress?.percent ?? 0));
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <Loader2 className="w-16 h-16 animate-spin text-blue-500 mb-4" />
          <p className="text-xl font-medium">Analysis in progress...</p>
          <div className="w-full max-w-md mt-4">
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${percent}%` }}
                role="progressbar"
                aria-valuenow={percent}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <div className="flex justify-between mt-2 text-sm">
              <span>{progress?.message || 'Please wait while we process your data.'}</span>
              <span className="font-medium text-gray-600">{Math.round(percent)}%</span>
            </div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-red-600 bg-red-50 p-8 rounded-lg shadow-md">
          <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Analysis Failed</h2>
          <p className="text-center mb-4">We encountered an error trying to process your request:</p>
          <p className="text-sm bg-red-100 p-3 rounded-md text-red-700 italic">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-6 px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }

    if (analysisResults) {
      const hasTextResults = Array.isArray(analysisResults.text_analysis) && analysisResults.text_analysis.length > 0;
      const hasImageResults = analysisResults.image_analysis && Object.keys(analysisResults.image_analysis).length > 0;
      const hasTraditionScores = Array.isArray(analysisResults.tradition_scores) && analysisResults.tradition_scores.length > 0;

      return (
        <div className="space-y-8">
          <div className="flex items-center justify-between border-b pb-3 mb-6">
            <h1 className="text-3xl font-bold text-gray-800">
              Analysis Dashboard
            </h1>
            {lastCompletedJobId && (
              <ExportButton jobId={lastCompletedJobId} apiBaseUrl={apiBaseUrl} />
            )}
          </div>
          {analysisResults._partial && (
            <div className="p-4 my-4 text-sm text-orange-700 bg-orange-100 border border-orange-300 rounded-lg shadow">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-orange-600" />
                <h3 className="font-medium">Partial results</h3>
              </div>
              <p className="mt-1">{analysisResults._note || 'Only aggregate scores could be recovered for this job.'}</p>
            </div>
          )}
          {(!hasTextResults && !hasImageResults) && (
            <div className="p-4 my-4 text-sm text-yellow-700 bg-yellow-100 border border-yellow-300 rounded-lg shadow">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-yellow-600" />
                <h3 className="font-medium">No Analysis Data Found</h3>
              </div>
              <p className="mt-1">The analysis job completed, but no specific text or image results were returned. You can check the raw output below if available.</p>
            </div>
          )}
          {hasTextResults && (
            <section id="text-analysis-section">
              <TextAnalysisVisuals textResults={analysisResults.text_analysis as TextAnalysisItem[]} />
            </section>
          )}
          {hasImageResults && (
            <section id="image-analysis-section" className="mt-8 pt-8 border-t border-gray-200">
              <ImageAnalysisVisuals imageResults={analysisResults.image_analysis as { [imageName: string]: ImageAnalysisItem }} />
            </section>
          )}
          {hasTextResults && hasImageResults && (
            <section id="combined-analysis-section" className="mt-8 pt-8 border-t border-gray-200">
              <CombinedAnalysisVisuals
                textResults={analysisResults.text_analysis as TextAnalysisItem[]}
                imageResults={analysisResults.image_analysis as { [imageName: string]: ImageAnalysisItem }}
              />
            </section>
          )}
          {hasTraditionScores && (
            <section id="cultural-fairness-section" className="mt-8 pt-8 border-t border-gray-200 space-y-8">
              <CulturalFairnessHeatmap data={analysisResults.tradition_scores!} />
              <CrossCulturalEquityDashboard scores={analysisResults.tradition_scores!} />
            </section>
          )}
          <details className="mt-10 pt-6 border-t border-gray-300">
            <summary className="text-md font-medium text-gray-700 cursor-pointer hover:text-gray-900 transition-colors">
              View Raw JSON Output
            </summary>
            <div className="bg-gray-800 text-gray-100 p-4 rounded-lg shadow-inner overflow-x-auto mt-3">
              <pre className="text-xs whitespace-pre-wrap break-all">
                {JSON.stringify(analysisResults, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      );
    }

    return <WelcomeMessage />;
  };

  return (
    <main className={`flex-1 p-6 sm:p-8 bg-gray-100 transition-all duration-300 min-h-screen`}>
      <div className="max-w-5xl mx-auto space-y-8">
        {renderContent()}
        <details className="pt-6 border-t border-gray-300">
          <summary className="text-md font-medium text-gray-700 cursor-pointer hover:text-gray-900 transition-colors">
            Compare Two Jobs
          </summary>
          <div className="mt-4">
            <CompareMode apiBaseUrl={apiBaseUrl} />
          </div>
        </details>
      </div>
    </main>
  );
}

export default MainContent;