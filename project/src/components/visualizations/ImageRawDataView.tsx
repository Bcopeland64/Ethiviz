import React from 'react';

interface ImageRawDataViewProps {
  imageResults: { [imageName: string]: any }; // Expects imageName -> { analysis: {...}, ... }
}

const ImageRawDataView: React.FC<ImageRawDataViewProps> = ({ imageResults }) => {
  const resultsArray = imageResults ? Object.entries(imageResults) : [];

  if (resultsArray.length === 0) return <p className="text-sm text-gray-500">No raw image data to display.</p>;

  const columns = [
    { key: 'filename', name: 'Filename' },
    { key: 'bias_score', name: 'Bias Score' },
    { key: 'diversity_index', name: 'Diversity Index' },
    { key: 'western_ethics_score', name: 'Western Score' },
    { key: 'ubuntu_ethics_score', name: 'Ubuntu Score' },
    { key: 'confucian_ethics_score', name: 'Confucian Score' },
    { key: 'islamic_ethics_score', name: 'Islamic Score' },
    { key: 'face_count', name: 'Face Count'},
    { key: 'object_count', name: 'Object Count'}
  ];
  
  // Check the 'analysis' sub-object for keys, not the top-level image data object.
  const firstItemAnalysis = resultsArray.length > 0 && resultsArray[0][1] && resultsArray[0][1].analysis 
                            ? resultsArray[0][1].analysis 
                            : {};

  const availableColumns = columns.filter(col => 
    col.key === 'filename' || 
    (firstItemAnalysis && typeof firstItemAnalysis === 'object' && firstItemAnalysis.hasOwnProperty(col.key) && typeof firstItemAnalysis[col.key] !== 'object')
  );

  return (
    <div className="bg-white p-4 shadow rounded-lg mt-6">
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Raw Image Analysis Data</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {availableColumns.map(col => (
                <th key={col.key} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {col.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {resultsArray.map(([imageName, imageData], index) => {
              const analysisData = imageData.analysis || {}; // Ensure analysis object exists
              return (
                <tr key={imageName || index}>
                  {availableColumns.map(col => {
                    let cellValue;
                    if (col.key === 'filename') {
                      // Use original_path if available, otherwise imageName
                      const displayName = imageData.original_path || imageName;
                      cellValue = displayName.substring(0,50) + (displayName.length > 50 ? "..." : "");
                    } else {
                      cellValue = analysisData[col.key];
                    }
                    
                    if (typeof cellValue === 'number') {
                      cellValue = parseFloat(cellValue.toFixed(3));
                    } else if (cellValue === null || cellValue === undefined) {
                      cellValue = "N/A";
                    }
                    return (
                      <td key={col.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {String(cellValue)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ImageRawDataView;
