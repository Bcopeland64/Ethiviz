import React from 'react';
import Plot from 'react-plotly.js';
import { Data } from 'plotly.js';

interface TraditionRadarChartProps {
  textResults: any[];
}

const TraditionRadarChart: React.FC<TraditionRadarChartProps> = ({ textResults }) => {
  if (!textResults || textResults.length === 0) return <p>No data for radar chart.</p>;

  const traditions = ['western', 'ubuntu', 'confucian', 'islamic'];
  const averageScores: { [key: string]: number } = {};
  let validDataFound = false;

  traditions.forEach(tradition => {
    let sum = 0;
    let count = 0;
    textResults.forEach(item => {
      const score = parseFloat(item[`${tradition}_ethics_score`]);
      if (!isNaN(score)) {
        sum += score;
        count++;
      }
    });
    if (count > 0) {
      averageScores[tradition] = sum / count;
      validDataFound = true;
    } else {
      averageScores[tradition] = 0; // Default to 0 if no data, for consistent radar shape
    }
  });
  
  if (!validDataFound) {
    return <p>Could not calculate average scores for radar chart (no valid data).</p>;
  }

  const data: Data[] = [{
    type: 'scatterpolar',
    r: traditions.map(t => averageScores[t]),
    theta: traditions.map(t => t.charAt(0).toUpperCase() + t.slice(1)),
    fill: 'toself',
    name: 'Average Ethics Scores',
    line: { color: '#4D69FF' },
    fillcolor: 'rgba(77, 105, 255, 0.3)',
  }];

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Average Ethical Scores Radar</h3>
      <Plot
        data={data}
        layout={{
          title: 'Average Ethical Scores (Text Radar)', // Title can be part of layout
          polar: {
            radialaxis: { 
              visible: true, 
              range: [0, 10], 
              showline: false, 
              gridcolor: '#e5e7eb', // Tailwind gray-200
              linecolor: '#d1d5db', // Tailwind gray-300 for axis lines if shown
              tickfont: { color: '#4b5563' } // Tailwind gray-600 for ticks
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

export default TraditionRadarChart;
