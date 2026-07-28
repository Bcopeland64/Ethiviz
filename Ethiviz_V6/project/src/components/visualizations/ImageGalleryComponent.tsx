import React from 'react';
import { Eye, AlertTriangle } from 'lucide-react';

interface ImageGalleryComponentProps {
  imageResults: { 
    [imageName: string]: { 
      analysis: any; 
      image_url?: string; 
      original_path?: string; // original filename or path
    } 
  };
  onSelectImage?: (imageName: string) => void; // Optional: callback for when an image is selected
}

const ImageGalleryComponent: React.FC<ImageGalleryComponentProps> = ({ imageResults, onSelectImage }) => {
  const imageEntries = imageResults ? Object.entries(imageResults) : [];

  if (imageEntries.length === 0) {
    return <p className="text-sm text-gray-500">No images to display in gallery.</p>;
  }

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Image Gallery & Quick Stats</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {imageEntries.map(([imageName, imageData]) => {
          const analysis = imageData.analysis || {}; // Ensure analysis object exists
          const imageUrl = imageData.image_url;
          const originalPath = imageData.original_path || imageName;

          return (
            <div key={imageName} className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200">
              <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                {imageUrl ? (
                  <img src={imageUrl} alt={originalPath} className="object-cover w-full h-full" />
                ) : (
                  <div className="text-gray-500 flex flex-col items-center">
                    <AlertTriangle size={32} />
                    <span>No Preview</span>
                  </div>
                )}
              </div>
              <div className="p-3">
                <h4 className="text-sm font-semibold truncate" title={originalPath}>{originalPath}</h4>
                <div className="text-xs text-gray-600 mt-1 space-y-0.5">
                  <p>Bias: <span className="font-medium">{analysis.bias_score !== undefined ? parseFloat(analysis.bias_score).toFixed(2) : 'N/A'}</span></p>
                  <p>Diversity: <span className="font-medium">{analysis.diversity_index !== undefined ? parseFloat(analysis.diversity_index).toFixed(2) : 'N/A'}</span></p>
                </div>
                {onSelectImage && (
                  <button 
                    onClick={() => onSelectImage(imageName)}
                    className="mt-2 w-full text-xs bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded flex items-center justify-center space-x-1"
                  >
                    <Eye size={14} />
                    <span>View Details</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ImageGalleryComponent;
