import React from 'react';
import Plot from 'react-plotly.js';

interface TextScatterPlotsProps {
  textResults: any[]; // Assuming textResults is an array of analysis objects
}

const TextScatterPlots: React.FC<TextScatterPlotsProps> = ({ textResults }) => {
  if (!textResults || textResults.length < 2) { // Need at least 2 points for a meaningful scatter plot
    return <p className="text-sm text-gray-500">Insufficient data for scatter plots. At least two data points are required.</p>;
  }

  const unpack = (rows: any[], key: string) => rows.map(row => row ? row[key] : null).filter(val => val !== null && !isNaN(parseFloat(val)));
  const unpackText = (rows: any[], key: string, displayKey: string) => rows.map(row => row && row[key] ? `${displayKey}: ${row[key]}` : null).filter(val => val !== null);


  const biasScores = unpack(textResults, 'bias_score');
  const diversityIndices = unpack(textResults, 'diversity_index');
  const plot1Text = unpackText(textResults, 'id', 'Text ID');


  const westernEthicsScores = unpack(textResults, 'western_ethics_score');
  const ubuntuEthicsScores = unpack(textResults, 'ubuntu_ethics_score');
  const plot2Text = unpackText(textResults, 'id', 'Text ID');

  const commonLayoutSettings = {
    height: 400,
    margin: { l: 60, r: 30, b: 70, t: 70 }, // Adjusted margins
    paper_bgcolor: 'rgba(255,255,255,0)',
    plot_bgcolor: 'rgba(255,255,255,0)',
    font: { color: '#374151' }, // Tailwind gray-700
    xaxis: {
      gridcolor: '#e5e7eb', // Tailwind gray-200
      linecolor: '#d1d5db', // Tailwind gray-300
      zerolinecolor: '#d1d5db',
    },
    yaxis: {
      gridcolor: '#e5e7eb',
      linecolor: '#d1d5db',
      zerolinecolor: '#d1d5db',
    },
    legend: {
      bgcolor: 'rgba(255,255,255,0.8)',
      bordercolor: '#e5e7eb',
    }
  };

  return (
    <div className="space-y-6">
      {/* Removed the overall h3 title, titles are now per-plot */}
      
      {biasScores.length > 1 && diversityIndices.length > 1 && biasScores.length === diversityIndices.length ? (
        <div className="bg-white p-4 shadow rounded-lg">
          <Plot
            data={[
              {
                x: biasScores,
                y: diversityIndices,
                text: plot1Text.length === biasScores.length ? plot1Text : undefined,
                mode: 'markers',
                type: 'scatter',
                marker: { color: '#3B82F6' }, // Tailwind blue-500
                name: 'Bias vs. Diversity',
              },
            ]}
            layout={{
              ...commonLayoutSettings,
              title: 'Bias Score vs. Diversity Index (Text)',
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Bias Score' },
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Diversity Index' },
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '400px' }} // Explicit height
          />
        </div>
      ) : <p className="text-sm text-gray-500">Not enough valid data points for Bias vs. Diversity plot.</p>}

      {westernEthicsScores.length > 1 && ubuntuEthicsScores.length > 1 && westernEthicsScores.length === ubuntuEthicsScores.length ? (
        <div className="bg-white p-4 shadow rounded-lg">
          <Plot
            data={[
              {
                x: westernEthicsScores,
                y: ubuntuEthicsScores,
                text: plot2Text.length === westernEthicsScores.length ? plot2Text : undefined,
                mode: 'markers',
                type: 'scatter',
                marker: { color: '#10B981' }, // Tailwind emerald-500
                name: 'Western vs. Ubuntu Ethics',
              },
            ]}
            layout={{
              ...commonLayoutSettings,
              title: 'Western vs. Ubuntu Ethics Score (Text)',
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Western Ethics Score' },
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Ubuntu Ethics Score' },
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '400px' }} // Explicit height
          />
        </div>
      ) : <p className="text-sm text-gray-500">Not enough valid data points for Western vs. Ubuntu Ethics plot.</p>}
    </div>
  );
};

export default TextScatterPlots;
