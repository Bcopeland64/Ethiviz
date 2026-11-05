import React, { FC } from 'react';
import Plot from 'react-plotly.js';
import { calculateAverageScore } from '../../utils/visualizationUtils';
import { TextAnalysisItem, ImageAnalysisItem } from '../../utils/types';

interface CombinedDiversityBiasChartProps {
  textResults: TextAnalysisItem[];
  imageResults: { [imageName: string]: ImageAnalysisItem };
}

const CombinedDiversityBiasChart: FC<CombinedDiversityBiasChartProps> = ({ textResults, imageResults }) => {
  const imageResultsArray = imageResults ? Object.values(imageResults) : [];

  if ((!textResults || textResults.length === 0) && (!imageResultsArray || imageResultsArray.length === 0)) {
    return <p className="text-sm text-gray-500">No data for combined diversity/bias chart.</p>;
  }

  const metrics = ['Diversity Index', 'Bias Score'];
  const textValues: (number | null)[] = [];
  const imageValues: (number | null)[] = [];

  const textAvgDiversity = calculateAverageScore(textResults, 'diversity_index', false);
  const imageAvgDiversity = calculateAverageScore(imageResultsArray, 'diversity_index', true);
  const textAvgBias = calculateAverageScore(textResults, 'bias_score', false);
  const imageAvgBias = calculateAverageScore(imageResultsArray, 'bias_score', true);

  textValues.push(textAvgDiversity, textAvgBias);
  imageValues.push(imageAvgDiversity, imageAvgBias);
  
  if (textValues.every(v => v === null) && imageValues.every(v => v === null)) {
    return <p className="text-sm text-gray-500">Insufficient data to render combined diversity & bias scores.</p>;
  }

  const plotData: any[] = [
    {
      x: metrics,
      y: textValues.map(s => s === null ? 0 : s),
      name: 'Text Analysis',
      type: 'bar' as any,
      marker: { color: '#FF6B6B' },
      text: textValues.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    },
    {
      x: metrics,
      y: imageValues.map(s => s === null ? 0 : s),
      name: 'Image Analysis',
      type: 'bar' as any,
      marker: { color: '#FFA07A' },
      text: imageValues.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    }
  ];
  
  const finalPlotData = plotData.filter(series => (series.y as number[]).some(val => val !== 0 || (series.text as string[]).includes('N/A') === false));

  return (
    <div className="bg-white p-4 shadow rounded-lg">
      <Plot
        data={finalPlotData}
        layout={{
          title: 'Average Diversity & Bias: Text vs. Image',
          barmode: 'group' as any,
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
            x: 0.5, y: 1.15, xanchor: 'center' as any, orientation: 'h' as any,
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
