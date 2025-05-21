import React from 'react';
import WelcomeMessage from './WelcomeMessage';
import { Loader2, AlertTriangle, ServerCrash } from 'lucide-react'; // Added icons

interface MainContentProps {
  sidebarOpen: boolean;
  analysisResults: any | null;
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
            onClick={() => window.location.reload()} // Simple refresh, or pass a reset function
            className="mt-6 px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }

    if (analysisResults) {
      // For now, display raw JSON. Later, this will be replaced with proper components.
      return (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">Analysis Results</h2>
          
          {(!analysisResults.text_analysis && !analysisResults.image_analysis) && (
            <div className="p-4 my-4 text-sm text-yellow-700 bg-yellow-50 border border-yellow-300 rounded-lg">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-yellow-600" />
                <h3 className="font-medium">Partial or No Results</h3>
              </div>
              <p className="mt-1">The analysis job completed, but no specific text or image results were found. The raw output is displayed below.</p>
            </div>
          )}

          {/* Text Analysis Section */}
          {analysisResults.text_analysis && (
            <div className="p-4 my-4 border rounded-lg bg-white shadow">
              <h3 className="text-xl font-semibold text-blue-700 mb-3">Text Analysis</h3>
              {Array.isArray(analysisResults.text_analysis) ? (
                analysisResults.text_analysis.map((item: any, index: number) => (
                  <div key={index} className="mb-3 p-3 border-b last:border-b-0">
                    <p className="text-sm text-gray-700"><span className="font-semibold">Item {index + 1}:</span></p>
                    <p className="text-xs text-gray-600">Bias Score: {item.bias_score ?? 'N/A'}</p>
                    <p className="text-xs text-gray-600">Diversity Index: {item.diversity_index ?? 'N/A'}</p>
                    {/* Add more fields as necessary */}
                  </div>
                ))
              ) : (
                <div>
                  <p className="text-sm text-gray-600">Bias Score: {analysisResults.text_analysis.bias_score ?? 'N/A'}</p>
                  <p className="text-sm text-gray-600">Diversity Index: {analysisResults.text_analysis.diversity_index ?? 'N/A'}</p>
                  {/* Add more fields as necessary */}
                </div>
              )}
            </div>
          )}

          {/* Image Analysis Section */}
          {analysisResults.image_analysis && Object.keys(analysisResults.image_analysis).length > 0 && (
             <div className="p-4 my-4 border rounded-lg bg-white shadow">
              <h3 className="text-xl font-semibold text-green-700 mb-3">Image Analysis</h3>
              <p className="text-sm text-gray-600 mb-2">Number of images processed: {Object.keys(analysisResults.image_analysis).length}</p>
              {/* Display summary for first few images or aggregated data if available */}
              {Object.entries(analysisResults.image_analysis).slice(0, 3).map(([imageName, details]: [string, any]) => (
                <div key={imageName} className="mb-2 p-2 border rounded bg-green-50">
                  <p className="text-xs font-semibold text-green-800">{imageName}:</p>
                  <p className="text-xs text-gray-600">Diversity Index: {details.diversity_index ?? 'N/A'}</p>
                  {/* Potentially list a few key cultural elements or skin tone distributions if simple */}
                </div>
              ))}
              {Object.keys(analysisResults.image_analysis).length > 3 && <p className="text-xs text-gray-500 mt-2">More image details in raw JSON below...</p>}
            </div>
          )}
          
          <div className="bg-gray-800 text-gray-100 p-4 rounded-lg shadow-inner overflow-x-auto mt-6">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Raw JSON Output:</h4>
            <pre className="text-xs whitespace-pre-wrap break-all">
              {JSON.stringify(analysisResults, null, 2)}
            </pre>
          </div>
        </div>
      );
    }

    return <WelcomeMessage />;
  };

  return (
    <main className={`flex-1 p-8 bg-gray-100 transition-all duration-300 ${sidebarOpen ? 'ml-0' : 'ml-0'} min-h-screen`}>
      {/* Added min-h-screen and bg-gray-100 for better visual separation */}
      <div className="max-w-4xl mx-auto"> {/* Optional: constrain width for readability */}
        {renderContent()}
      </div>
    </main>
  );
}

export default MainContent;