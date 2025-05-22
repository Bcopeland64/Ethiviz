import React from 'react';
import ImageMetrics from './ImageMetrics';
import DemographicsCharts from './DemographicsCharts';
import ImageEthicalScoresChart from './ImageEthicalScoresChart';
import ImageGalleryComponent from './ImageGalleryComponent';
import ImageTraditionRadarChart from './ImageTraditionRadarChart';
import ImageRawDataView from './ImageRawDataView';

interface ImageAnalysisVisualsProps {
  imageResults: { // More specific type based on expected structure
    [imageName: string]: {
      analysis: any; // Contains scores like bias_score, diversity_index, ethics scores
      image_url?: string;
      original_path?: string;
      skin_tone_distribution?: any;
      gender_representation?: any;
    }
  };
  // Add onSelectImage if ImageGalleryComponent needs to trigger a modal or detailed view in a parent
  // onSelectImage?: (imageName: string) => void; 
}

const ImageAnalysisVisuals: React.FC<ImageAnalysisVisualsProps> = ({ imageResults /*, onSelectImage */ }) => {
  if (!imageResults || Object.keys(imageResults).length === 0) {
    return <p className="text-gray-500">No image analysis data available to display visualizations.</p>;
  }

  const imageNames = Object.keys(imageResults);
  // For ImageTraditionRadarChart: Use the first image's data as a placeholder
  // TODO: Implement a selection mechanism (e.g., click on gallery image) to update selectedImageData
  const firstImageName = imageNames.length > 0 ? imageNames[0] : undefined;
  const selectedImageDataForRadar = firstImageName ? imageResults[firstImageName] : undefined;
  // The ImageTraditionRadarChart expects selectedImageData to be the analysis object directly, or an object containing analysis.
  // My ImageTraditionRadarChart component created earlier handles selectedImageData.analysis or selectedImageData.
  // The placeholder content for ImageTraditionRadarChart expected scores directly on selectedImageData.
  // The actual data structure is imageResults[imageName].analysis.
  // So, selectedImageDataForRadar passed to ImageTraditionRadarChart should be imageResults[firstImageName]
  // and the radar chart component will access selectedImageDataForRadar.analysis.
  // Let's adjust ImageTraditionRadarChart to always expect the .analysis structure for clarity if it's not already.
  // My version of ImageTraditionRadarChart already does: `const analysisObject = selectedImageData.analysis || selectedImageData;` which is robust.

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold text-green-700 mb-6">Image Analysis Visualizations</h2>
      
      <ImageMetrics imageResults={imageResults} />
      
      <hr className="my-8 border-gray-300" />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ImageEthicalScoresChart imageResults={imageResults} />
        {/* Placeholder for selected image radar chart */}
        {selectedImageDataForRadar ? (
          <ImageTraditionRadarChart 
            selectedImageData={selectedImageDataForRadar} // This is imageResults[firstImageName]
            imageName={selectedImageDataForRadar.original_path || firstImageName} 
          />
        ) : (
          <div className="bg-white p-4 shadow rounded-lg flex items-center justify-center h-full">
            <p className="text-sm text-gray-500">No image data available for radar chart display.</p>
          </div>
        )}
      </div>
      
      <hr className="my-8 border-gray-300" />

      <DemographicsCharts imageResults={imageResults} />
      
      <hr className="my-8 border-gray-300" />
      
      <ImageGalleryComponent 
        imageResults={imageResults} 
        // onSelectImage={onSelectImage} // TODO: Pass handler to update selected image for radar chart
      />
      
      <hr className="my-8 border-gray-300" />

      <ImageRawDataView imageResults={imageResults} />

      {/* Optional: Display raw data for debugging or detailed view */}
      {/* 
      <details className="mt-6">
        <summary className="text-sm font-medium text-gray-600 cursor-pointer hover:text-gray-800">
          View Raw JSON Data (Images)
        </summary>
        <pre className="mt-2 text-xs bg-gray-50 p-4 rounded-md overflow-x-auto shadow">
          {JSON.stringify(imageResults, null, 2)}
        </pre>
      </details>
      */}
    </div>
  );
};

export default ImageAnalysisVisuals;
