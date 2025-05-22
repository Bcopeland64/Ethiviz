import React from 'react';
import Plot from 'react-plotly.js';
import { PlotData } from 'plotly.js';

interface ImageEthicalScoresChartProps {
  imageResults: { [imageName: string]: any };
}

const ImageEthicalScoresChart: React.FC<ImageEthicalScoresChartProps> = ({ imageResults }) => {
  const resultsArray = imageResults ? Object.values(imageResults) : [];

  if (resultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No image data for ethical scores chart.</p>;
  }

  const traditions = ['western', 'ubuntu', 'confucian', 'islamic'];
  const averageScores: { [key: string]: number } = {};
  let validDataFound = false;

  traditions.forEach(tradition => {
    let sum = 0;
    let count = 0;
    resultsArray.forEach(item => {
      if (item && typeof item === 'object' && item.hasOwnProperty(`${tradition}_ethics_score`)) {
        const score = parseFloat(item[`${tradition}_ethics_score`]);
        if (!isNaN(score)) {
          sum += score;
          count++;
          validDataFound = true;
        }
      }
    });
    averageScores[tradition] = count > 0 ? sum / count : 0;
  });

  if (!validDataFound) {
    return <p className="text-sm text-gray-500">No valid ethical scores found in image results for the chart.</p>;
  }

  const plotData: PlotData[] = [{
    x: traditions.map(t => t.charAt(0).toUpperCase() + t.slice(1)), // Capitalized tradition names
    y: traditions.map(t => averageScores[t]),
    type: 'bar',
    name: 'Average Ethical Scores',
    marker: { 
      color: ['#3498DB', '#F1C40F', '#E74C3C', '#2ECC71'] // Example colors for each tradition
    }
  }];

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      {/* h3 title is removed as it's now part of the Plotly layout.title */}
      <Plot
        data={plotData}
        layout={{
          title: 'Average Ethical Scores (Images)',
          yaxis: { 
            title: 'Average Ethics Score',
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
          },
          xaxis: { 
            title: 'Ethical Tradition',
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
          },
          height: 350,
          margin: { l: 60, r: 30, b: 80, t: 70 }, // Adjusted margins
          paper_bgcolor: 'rgba(255,255,255,0)',
          plot_bgcolor: 'rgba(255,255,255,0)',
          font: { color: '#374151' },
          legend: { 
            bgcolor: 'rgba(255,255,255,0.8)', 
            bordercolor: '#e5e7eb',
          }
        }}
        style={{ width: '100%', height: '350px' }}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default ImageEthicalScoresChart;
