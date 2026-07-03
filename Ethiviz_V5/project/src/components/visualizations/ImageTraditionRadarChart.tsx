import React from 'react';
import Plot from 'react-plotly.js';
import { Data } from 'plotly.js';

interface ImageTraditionRadarChartProps {
  selectedImageData: any; // Analysis result for a single image
  imageName?: string; // Optional image name for title
}

const ImageTraditionRadarChart: React.FC<ImageTraditionRadarChartProps> = ({ selectedImageData, imageName }) => {
  if (!selectedImageData) return <p className="text-sm text-gray-500">No image data selected for radar chart.</p>;

  const traditions = ['western', 'ubuntu', 'confucian', 'islamic'];
  const scores: number[] = [];
  let validDataFound = false;

  traditions.forEach(tradition => {
    // Ensure selectedImageData.analysis exists, as per the structure in ImageAnalysisVisuals.tsx
    const analysisObject = selectedImageData.analysis || selectedImageData;
    const score = parseFloat(analysisObject[`${tradition}_ethics_score`]);
    if (!isNaN(score)) {
      scores.push(score);
      validDataFound = true;
    } else {
      scores.push(0); // Default to 0 if no data, for consistent radar shape
    }
  });
  
  // Check if all scores are default 0 due to genuinely missing data or all scores being zero
  if (!validDataFound && scores.every(s => s === 0)) { 
    return <p className="text-sm text-gray-500">No valid ethical scores found for this image.</p>;
  }

  const data: Data[] = [{
    type: 'scatterpolar',
    r: scores,
    theta: traditions.map(t => t.charAt(0).toUpperCase() + t.slice(1)),
    fill: 'toself',
    name: 'Ethics Scores',
    line: { color: '#00ACC1' }, // Different color for image radar
    fillcolor: 'rgba(0, 172, 193, 0.3)',
  }];

  const chartTitle = imageName 
    ? `Ethical Scores: ${imageName.substring(0,30) + (imageName.length > 30 ? "..." : "")}` 
    : "Ethical Scores for Selected Image";

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      {/* h3 title is removed as it's now part of the Plotly layout.title */}
      <Plot
        data={data}
        layout={{
          title: chartTitle,
          polar: {
            radialaxis: { 
              visible: true, 
              range: [0, 10], 
              showline: false, 
              gridcolor: '#e5e7eb', // Tailwind gray-200
              linecolor: '#d1d5db', // Tailwind gray-300
              tickfont: { color: '#4b5563' } // Tailwind gray-600
            },
            angularaxis: { 
              gridcolor: '#e5e7eb',
              linecolor: '#d1d5db',
              tickfont: { color: '#4b5563' }
            }
          },
          showlegend: false,
          height: 350,
          margin: { l: 50, r: 50, t: 70, b: 50 }, // Adjusted margins
          paper_bgcolor: 'rgba(255,255,255,0)',
          plot_bgcolor: 'rgba(255,255,255,0)',
          font: { color: '#374151' } // Tailwind gray-700
        }}
        style={{ width: '100%', height: '350px' }}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default ImageTraditionRadarChart;
