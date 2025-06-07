import React from 'react';
import CombinedEthicsChart from './CombinedEthicsChart';
import CombinedDiversityBiasChart from './CombinedDiversityBiasChart';
import { TextAnalysisItem, ImageAnalysisItem } from '../../utils/types';

interface CombinedAnalysisVisualsProps {
  textResults: TextAnalysisItem[];
  imageResults: { [imageName: string]: ImageAnalysisItem };
}

const CombinedAnalysisVisuals: React.FC<CombinedAnalysisVisualsProps> = ({ textResults, imageResults }) => {
  const hasTextData = textResults && textResults.length > 0;
  const hasImageData = imageResults && Object.keys(imageResults).length > 0;

  if (!hasTextData && !hasImageData) {
    return <p className="text-gray-500">No Text or Image analysis data available for combined visualizations.</p>;
  }
  // Individual components will handle cases where one type of data might be missing.

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold text-purple-700 mb-6">Combined Analysis Visualizations</h2>
      
      <CombinedEthicsChart 
        textResults={textResults || []}
        imageResults={imageResults || {}}
      />
      
      <hr className="my-8 border-gray-300" />
      
      <CombinedDiversityBiasChart 
        textResults={textResults || []} 
        imageResults={imageResults || {}} 
      />
      
      {/* Optional: Display raw data for debugging or detailed view 
      { (hasTextData || hasImageData) && (
        <details className="mt-6">
          <summary className="text-sm font-medium text-gray-600 cursor-pointer hover:text-gray-800">
            View Raw JSON Data (Combined)
          </summary>
          <div className="flex space-x-4">
            {hasTextData && (
              <pre className="mt-2 text-xs w-1/2 bg-gray-50 p-4 rounded-md overflow-x-auto shadow">
                <strong>Text Results:</strong><br/>
                {JSON.stringify(textResults, null, 2)}
              </pre>
            )}
            {hasImageData && (
              <pre className="mt-2 text-xs w-1/2 bg-gray-50 p-4 rounded-md overflow-x-auto shadow">
                <strong>Image Results:</strong><br/>
                {JSON.stringify(imageResults, null, 2)}
              </pre>
            )}
          </div>
        </details>
      )}
      */}
    </div>
  );
};

export default CombinedAnalysisVisuals;
