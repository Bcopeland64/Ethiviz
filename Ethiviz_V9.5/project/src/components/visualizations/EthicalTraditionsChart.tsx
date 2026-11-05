import React from 'react';
import Plot from 'react-plotly.js';
import { PlotData } from 'plotly.js';

interface EthicalTraditionsChartProps {
  textResults: any[];
}

const EthicalTraditionsChart: React.FC<EthicalTraditionsChartProps> = ({ textResults }) => {
  if (!textResults || textResults.length === 0) return <p>No data for ethical traditions chart.</p>;

  const traditions = ['western', 'ubuntu', 'confucian', 'islamic'];
  const plotData: Partial<PlotData>[] = [];

  traditions.forEach(tradition => {
    const scores = textResults
      .map(item => parseFloat(item[`${tradition}_ethics_score`]))
      .filter(score => !isNaN(score));
    
    if (scores.length > 0) {
      plotData.push({
        y: scores,
        type: 'box',
        name: tradition.charAt(0).toUpperCase() + tradition.slice(1),
        boxmean: true, // Show mean in the box plot
      });
    }
  });

  if (plotData.length === 0) {
    return <p>No valid ethical scores found in the results for the box plot.</p>;
  }

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Ethical Perspective Scores Distribution</h3>
      <Plot
        data={plotData}
        layout={{
          title: 'Ethical Perspective Scores Distribution', // Title can be part of layout
          yaxis: { 
            title: 'Ethics Score',
            gridcolor: '#e5e7eb', // Tailwind gray-200
            linecolor: '#d1d5db', // Tailwind gray-300
            zerolinecolor: '#d1d5db',
          },
          xaxis: { 
            title: 'Ethical Tradition',
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
          },
          height: 400,
          margin: { l: 60, r: 30, b: 100, t: 60 }, // Adjusted top margin for title
          paper_bgcolor: 'rgba(255,255,255,0)', 
          plot_bgcolor: 'rgba(255,255,255,0)',  
          font: { color: '#374151' }, // Tailwind gray-700
          legend: { 
            bgcolor: 'rgba(255,255,255,0.8)', 
            bordercolor: '#e5e7eb',
          }
        }}
        style={{ width: '100%', height: '400px' }}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default EthicalTraditionsChart;
