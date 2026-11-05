import React from 'react';
import Plot from 'react-plotly.js';
import { PlotData } from 'plotly.js';

interface DemographicsChartsProps {
  imageResults: { [imageName: string]: any };
}

const DemographicsCharts: React.FC<DemographicsChartsProps> = ({ imageResults }) => {
  const resultsArray = imageResults ? Object.values(imageResults) : [];
  const imageNames = imageResults ? Object.keys(imageResults) : [];

  if (resultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No image data for demographic charts.</p>;
  }

  // 1. Average Skin Tone Distribution (Bar Chart)
  const aggregatedSkinTones: { [key: string]: { sum: number; count: number } } = {};
  resultsArray.forEach(item => {
    if (item && item.skin_tone_distribution && typeof item.skin_tone_distribution === 'object') {
      for (const [tone, value] of Object.entries(item.skin_tone_distribution)) {
        if (typeof value === 'number' && !isNaN(value)) {
          if (!aggregatedSkinTones[tone]) aggregatedSkinTones[tone] = { sum: 0, count: 0 };
          aggregatedSkinTones[tone].sum += value;
          aggregatedSkinTones[tone].count++;
        }
      }
    }
  });
  const avgSkinToneData: PlotData[] = resultsArray.length > 0 && Object.keys(aggregatedSkinTones).length > 0 ? [{
    x: Object.keys(aggregatedSkinTones),
    y: Object.values(aggregatedSkinTones).map(val => val.sum / val.count),
    type: 'bar',
    name: 'Avg. Skin Tone',
    marker: { color: '#2ECC71' }
  }] : [];

  // 2. Average Gender Representation (Pie Chart)
  const aggregatedGenders: { [key: string]: { sum: number; count: number } } = {};
  resultsArray.forEach(item => {
    if (item && item.gender_representation && typeof item.gender_representation === 'object') {
      for (const [gender, value] of Object.entries(item.gender_representation)) {
         if (typeof value === 'number' && !isNaN(value)) {
          if (!aggregatedGenders[gender]) aggregatedGenders[gender] = { sum: 0, count: 0 };
          aggregatedGenders[gender].sum += value;
          aggregatedGenders[gender].count++;
        }
      }
    }
  });
  const avgGenderData: PlotData[] = resultsArray.length > 0 && Object.keys(aggregatedGenders).length > 0 ? [{
    labels: Object.keys(aggregatedGenders),
    values: Object.values(aggregatedGenders).map(val => val.sum / val.count),
    type: 'pie',
    name: 'Avg. Gender Rep.',
    hole: 0.4,
    textinfo: 'label+percent',
    automargin: true,
  }] : [];
  
  // 3. Diversity Index by Image (Bar Chart)
  const diversityIndices = resultsArray.map((item, index) => ({
    name: imageNames[index] ? imageNames[index].substring(0, 20) + (imageNames[index].length > 20 ? "..." : "") : `Image ${index+1}`, // Truncate long names
    score: (item && typeof item.diversity_index === 'number') ? item.diversity_index : NaN
  })).filter(item => !isNaN(item.score));

  const diversityByImageData: PlotData[] = diversityIndices.length > 0 ? [{
    x: diversityIndices.map(item => item.name),
    y: diversityIndices.map(item => item.score),
    type: 'bar',
    name: 'Diversity Index',
    marker: { color: '#3498DB' }
  }] : [];

  const commonLayoutSettings = {
    height: 400, // Standard height, can be adjusted per chart
    margin: { l: 60, r: 30, b: 100, t: 70 }, // Standard margins
    paper_bgcolor: 'rgba(255,255,255,0)',
    plot_bgcolor: 'rgba(255,255,255,0)',
    font: { color: '#374151' }, // Tailwind gray-700
    xaxis: {
      gridcolor: '#e5e7eb', // Tailwind gray-200
      linecolor: '#d1d5db', // Tailwind gray-300
      zerolinecolor: '#d1d5db',
      titlefont: { color: '#4b5563' }, // Tailwind gray-600
      tickfont: { color: '#4b5563' },
    },
    yaxis: {
      gridcolor: '#e5e7eb',
      linecolor: '#d1d5db',
      zerolinecolor: '#d1d5db',
      titlefont: { color: '#4b5563' },
      tickfont: { color: '#4b5563' },
    },
    legend: {
      bgcolor: 'rgba(255,255,255,0.8)',
      bordercolor: '#e5e7eb',
      font: { color: '#374151' },
    }
  };

  return (
    <div className="space-y-8">
      {avgSkinToneData.length > 0 && (
        <div className="bg-white p-4 shadow rounded-lg">
          {/* h3 title removed, using layout.title */}
          <Plot 
            data={avgSkinToneData} 
            layout={{ 
              ...commonLayoutSettings,
              title: 'Average Skin Tone Distribution (Images)',
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Average Presence' }, 
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Skin Tone Category' },
              height: 350, // Custom height
            }} 
            style={{ width: '100%', height: '350px' }} 
            config={{ responsive: true }} />
        </div>
      )}
      {avgGenderData.length > 0 && (
        <div className="bg-white p-4 shadow rounded-lg">
          {/* h3 title removed, using layout.title */}
          <Plot 
            data={avgGenderData} 
            layout={{ 
              ...commonLayoutSettings,
              title: 'Average Gender Representation (Images)',
              height: 400, // Custom height for pie
              margin: { l: 40, r: 40, b: 40, t: 70 }, // Custom margin for pie
              legend: { ...commonLayoutSettings.legend, orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }
            }} 
            style={{ width: '100%', height: '400px' }} 
            config={{ responsive: true }} />
        </div>
      )}
      {diversityByImageData.length > 0 && (
        <div className="bg-white p-4 shadow rounded-lg">
          {/* h3 title removed, using layout.title */}
          <Plot 
            data={diversityByImageData} 
            layout={{ 
              ...commonLayoutSettings,
              title: 'Diversity Index by Image',
              yaxis: { ...commonLayoutSettings.yaxis, title: 'Diversity Index' }, 
              xaxis: { ...commonLayoutSettings.xaxis, title: 'Image', tickangle: -45 },
              height: 400, 
              margin: { ...commonLayoutSettings.margin, b: 150 } // Increased bottom margin for angled ticks
            }} 
            style={{ width: '100%', height: '400px' }} 
            config={{ responsive: true }} />
        </div>
      )}
      {(avgSkinToneData.length === 0 && avgGenderData.length === 0 && diversityByImageData.length === 0) && (
         <p className="text-sm text-gray-500">Insufficient data for demographics charts.</p>
      )}
    </div>
  );
};

export default DemographicsCharts;
