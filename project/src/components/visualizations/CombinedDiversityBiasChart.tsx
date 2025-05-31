import React, { FC } from 'react';
// Assuming Plot, Data, and calculateAverageScore are imported elsewhere or available globally.
// For example, if Plot and Data are from plotly.js:
// import Plot, { Data } from 'plotly.js-react-dist';
// And calculateAverageScore might be from a utils file:
// import { calculateAverageScore } from '../../utils/yourUtilsFile';

// Define the props interface
interface CombinedDiversityBiasChartProps {
  textResults: any[]; // Consider using a more specific type if available
  imageResultsArray: any[]; // Consider using a more specific type if available
}

// Define the Functional Component
const CombinedDiversityBiasChart: FC<CombinedDiversityBiasChartProps> = ({ textResults, imageResultsArray }) => {
  // Original logic starts here
  if ((!textResults || textResults.length === 0) && (!imageResultsArray || imageResultsArray.length === 0)) {
    return <p className="text-sm text-gray-500">No data for combined diversity/bias chart.</p>;
  }

  const metrics = ['Diversity Index', 'Bias Score'];
  const textValues: (number | null)[] = [];
  const imageValues: (number | null)[] = [];

  // Assuming calculateAverageScore is defined and imported
  // For example: const calculateAverageScore = (results: any[], scoreType: string, isImage: boolean): number | null => { /* ... implementation ... */ return 0; };
  const textAvgDiversity = calculateAverageScore(textResults, 'diversity_index', false);
  const imageAvgDiversity = calculateAverageScore(imageResultsArray, 'diversity_index', true);
  const textAvgBias = calculateAverageScore(textResults, 'bias_score', false);
  const imageAvgBias = calculateAverageScore(imageResultsArray, 'bias_score', true);

  textValues.push(textAvgDiversity, textAvgBias);
  imageValues.push(imageAvgDiversity, imageAvgBias);
  
  if (textValues.every(v => v === null) && imageValues.every(v => v === null)) {
    return <p className="text-sm text-gray-500">Insufficient data to render combined diversity & bias scores.</p>;
  }

  // Assuming 'Data' type for plotData is defined and imported (e.g., from Plotly)
  // For example: interface Data { x: any[]; y: any[]; name: string; type: string; marker?: any; text?: any[]; textposition?: string; hoverinfo?: string; }
  const plotData: any[] = [ // Using any[] for Data if not explicitly imported
    {
      x: metrics,
      y: textValues.map(s => s === null ? 0 : s),
      name: 'Text Analysis',
      type: 'bar' as any, // Added 'as any' for type compatibility if 'bar' is not a recognized literal type
      marker: { color: '#FF6B6B' },
      text: textValues.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    },
    {
      x: metrics,
      y: imageValues.map(s => s === null ? 0 : s),
      name: 'Image Analysis',
      type: 'bar' as any, // Added 'as any' for type compatibility
      marker: { color: '#FFA07A' },
      text: imageValues.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    }
  ];
  
  const finalPlotData = plotData.filter(series => (series.y as number[]).some(val => val !== 0 || (series.text as string[]).includes('N/A') === false));

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      {/* Assuming Plot component is correctly imported */}
      <Plot
        data={finalPlotData}
        layout={{
          title: 'Average Diversity & Bias: Text vs. Image',
          barmode: 'group' as any, // Added 'as any'
          xaxis: { 
            title: 'Metric',
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
            titlefont: { color: '#4b5563' },
            tickfont: { color: '#4b5563' },
          },
          yaxis: { 
            title: 'Average Score', 
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
            titlefont: { color: '#4b5563' },
            tickfont: { color: '#4b5563' },
          },
          height: 400,
          margin: { l: 60, r: 30, b: 80, t: 70 },
          paper_bgcolor: 'rgba(255,255,255,0)',
          plot_bgcolor: 'rgba(255,255,255,0)',
          font: { color: '#374151' },
          legend: { 
            x: 0.5, y: 1.15, xanchor: 'center' as any, orientation: 'h' as any, // Added 'as any'
            bgcolor: 'rgba(255,255,255,0)', 
            bordercolor: '#e5e7eb',
            font: { color: '#374151' },
          }
        }}
        style={{ width: '100%', height: '400px' }}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default CombinedDiversityBiasChart;
