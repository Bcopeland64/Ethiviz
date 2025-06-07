import React from 'react';
import WelcomeMessage from './WelcomeMessage';
import { Loader2, AlertTriangle } from 'lucide-react';
import TextAnalysisVisuals from './visualizations/TextAnalysisVisuals';
import ImageAnalysisVisuals from './visualizations/ImageAnalysisVisuals';
import CombinedAnalysisVisuals from './visualizations/CombinedAnalysisVisuals';
import { AnalysisResults, TextAnalysisItem, ImageAnalysisItem } from '../utils/types';

interface MainContentProps {
  sidebarOpen: boolean;
  analysisResults: AnalysisResults | null;
  isLoading: boolean;
  error: string | null;
}

function MainContent({ sidebarOpen, analysisResults, isLoading, error }: MainContentProps) {
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <Loader2 className="w-16 h-16 animate-spin text-blue-500 mb-4" />
          <p className="text-xl font-medium">Analysis in progress...</p>
          <p className="text-sm">Please wait while we process your data.</p>
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

      return (
        <div className="space-y-8">
          <h1 className="text-3xl font-bold text-gray-800 border-b pb-3 mb-6">
            Analysis Dashboard
          </h1>
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
      <div className="max-w-5xl mx-auto"> 
        {renderContent()}
      </div>
    </main>
  );
}

export default MainContent;