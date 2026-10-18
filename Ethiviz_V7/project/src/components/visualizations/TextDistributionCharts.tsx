import React from 'react';
import Plot from 'react-plotly.js';

interface TextDistributionChartsProps {
  textResults: any[]; // Assuming textResults is an array of analysis objects
}

const TextDistributionCharts: React.FC<TextDistributionChartsProps> = ({ textResults }) => {
  if (!textResults || textResults.length === 0) {
    return <p className="text-sm text-gray-500">No data available for distribution charts.</p>;
  }

  const unpack = (rows: any[], key: string) => rows.map(row => row ? row[key] : null).filter(val => val !== null && !isNaN(parseFloat(val)));

  const biasScores = unpack(textResults, 'bias_score');
  const diversityIndices = unpack(textResults, 'diversity_index');

  const commonLayoutSettings = {
    height: 400,
    margin: { l: 60, r: 30, b: 70, t: 70 },
    paper_bgcolor: 'rgba(255,255,255,0)',
    plot_bgcolor: 'rgba(255,255,255,0)',
    font: { color: '#374151' }, // Tailwind gray-700
    xaxis: {
      titlefont: { color: '#4b5563' }, // Tailwind gray-600
      gridcolor: '#e5e7eb', // Tailwind gray-200
      linecolor: '#d1d5db', // Tailwind gray-300
      zerolinecolor: '#d1d5db',
    },
    yaxis: {
      titlefont: { color: '#4b5563' },
      gridcolor: '#e5e7eb',
      linecolor: '#d1d5db',
      zerolinecolor: '#d1d5db',
    },
    bargap: 0.1, // Slightly larger gap for histograms
    legend: {
      bgcolor: 'rgba(255,255,255,0.8)',
      bordercolor: '#e5e7eb',
    }
  };

  return (
    <div className="space-y-6">
      {/* Removed the overall h3 title, titles are now per-plot */}
      
      {biasScores.length > 0 ? (
        <div className="bg-white p-4 shadow rounded-lg">
          <Plot
            data={[
              {
                x: biasScores,
                type: 'histogram',
                name: 'Bias Scores',
                marker: { color: '#60A5FA' }, // Tailwind blue-400
                // xbins: { size: 0.1 } // Example bin size, customize as needed
              },
            ]}
            layout={{
              ...commonLayoutSettings,
              title: 'Distribution of Bias Scores (Text)',
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Bias Score' },
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Frequency' },
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      ) : <p className="text-sm text-gray-500">Not enough valid data points for Bias Score distribution.</p>}

      {diversityIndices.length > 0 ? (
        <div className="bg-white p-4 shadow rounded-lg">
          <Plot
            data={[
              {
                x: diversityIndices,
                type: 'histogram',
                name: 'Diversity Indices',
                marker: { color: '#34D399' }, // Tailwind emerald-400
                // xbins: { size: 0.05 } // Example bin size, customize as needed
              },
            ]}
            layout={{
              ...commonLayoutSettings,
              title: 'Distribution of Diversity Indices (Text)',
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Diversity Index' },
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Frequency' },
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      ) : <p className="text-sm text-gray-500">Not enough valid data points for Diversity Index distribution.</p>}
    </div>
  );
};

export default TextDistributionCharts;
