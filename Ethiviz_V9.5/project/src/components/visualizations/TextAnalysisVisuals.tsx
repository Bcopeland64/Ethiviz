import React from 'react';
import TextMetrics from './TextMetrics';
import TextScatterPlots from './TextScatterPlots';
import TextDistributionCharts from './TextDistributionCharts';
import EthicalTraditionsChart from './EthicalTraditionsChart';
import TraditionRadarChart from './TraditionRadarChart';
import TextRawDataView from './TextRawDataView';

interface TextAnalysisVisualsProps {
  textResults: any | any[]; // Can be a single object or an array
}

const TextAnalysisVisuals: React.FC<TextAnalysisVisualsProps> = ({ textResults }) => {
  // Ensure textResults is always an array for child components that expect arrays
  const resultsArray = Array.isArray(textResults) ? textResults : (textResults ? [textResults] : []);

  if (!textResults || resultsArray.length === 0) {
    return <p className="text-gray-500">No text analysis data available to display visualizations.</p>;
  }

  return (
    <div className="space-y-8"> {/* Increased spacing for better separation */}
      <h2 className="text-2xl font-semibold text-blue-700 mb-6">Text Analysis Visualizations</h2>
      
      <TextMetrics textResults={resultsArray} />
      
      <hr className="my-8 border-gray-300" /> {/* Increased margin for hr */}
      
      {/* Ethical Traditions Charts Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <EthicalTraditionsChart textResults={resultsArray} />
        <TraditionRadarChart textResults={resultsArray} />
      </div>
      
      <hr className="my-8 border-gray-300" />
      
      <TextScatterPlots textResults={resultsArray} />
      
      <hr className="my-8 border-gray-300" />
      
      <TextDistributionCharts textResults={resultsArray} />
      
      <hr className="my-8 border-gray-300" />

      <TextRawDataView textResults={resultsArray} />

      {/* Optional: Display raw data for debugging or detailed view - kept for potential future use */}
      {/* 
      <details className="mt-6">
        <summary className="text-sm font-medium text-gray-600 cursor-pointer hover:text-gray-800">
          View Raw JSON Data
        </summary>
        <pre className="mt-2 text-xs bg-gray-50 p-4 rounded-md overflow-x-auto shadow">
          {JSON.stringify(textResults, null, 2)}
        </pre>
      </details>
      */}
    </div>
  );
};

export default TextAnalysisVisuals;
