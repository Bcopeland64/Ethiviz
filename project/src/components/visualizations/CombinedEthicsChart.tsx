  if ((!textResults || textResults.length === 0) && imageResultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No data for combined ethics chart.</p>;
  }

  const textScores: (number | null)[] = [];
  const imageScores: (number | null)[] = [];
  const validTraditions: string[] = [];

  traditions.forEach(trad => {
    const textAvg = calculateAverageScore(textResults, `${trad}_ethics_score`, false);
    const imageAvg = calculateAverageScore(imageResultsArray, `${trad}_ethics_score`, true);

    if (textAvg !== null || imageAvg !== null) {
      validTraditions.push(trad.charAt(0).toUpperCase() + trad.slice(1));
      textScores.push(textAvg);
      imageScores.push(imageAvg);
    }
  });
  
  if (validTraditions.length === 0) {
     return <p className="text-sm text-gray-500">Insufficient data to render combined ethics scores.</p>;
  }

  const plotData: Data[] = [
    {
      x: validTraditions,
      y: textScores.map(s => s === null ? 0 : s), // Plotly needs numerical values; nulls can break hover/layout
      name: 'Text Analysis',
      type: 'bar',
      marker: { color: '#4D69FF' },
      text: textScores.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    },
    {
      x: validTraditions,
      y: imageScores.map(s => s === null ? 0 : s),
      name: 'Image Analysis',
      type: 'bar',
      marker: { color: '#00CC96' },
      text: imageScores.map(s => s === null ? 'N/A' : s.toFixed(2)),
      textposition: 'auto',
      hoverinfo: 'x+y+name'
    }
  ];
  
  // Filter out data series if all its values are null
  const finalPlotData = plotData.filter(series => (series.y as number[]).some(val => val !== 0 || (series.text as string[]).includes('N/A') === false));


  return (
    <div className="bg-white p-4 shadow rounded-lg">
      {/* h3 title removed, using layout.title */}
      <Plot
        data={finalPlotData}
        layout={{
          title: 'Average Ethical Scores: Text vs. Image',
          barmode: 'group',
          xaxis: { 
            title: 'Ethical Tradition',
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
            titlefont: { color: '#4b5563' },
            tickfont: { color: '#4b5563' },
          },
          yaxis: { 
            title: 'Average Ethics Score', 
            range: [0, 10], // Assuming scores are 0-10
            gridcolor: '#e5e7eb',
            linecolor: '#d1d5db',
            zerolinecolor: '#d1d5db',
            titlefont: { color: '#4b5563' },
            tickfont: { color: '#4b5563' },
          },
          height: 400,
          margin: { l: 60, r: 30, b: 100, t: 70 }, // Adjusted top margin for title
          paper_bgcolor: 'rgba(255,255,255,0)',
          plot_bgcolor: 'rgba(255,255,255,0)',
          font: { color: '#374151' }, // Tailwind gray-700
          legend: { 
            x: 0.5, y: 1.15, xanchor: 'center', orientation: 'h',
            bgcolor: 'rgba(255,255,255,0)', // Transparent legend background
            bordercolor: '#e5e7eb', // Light border for legend
            font: { color: '#374151' },
          }
        }}
        style={{ width: '100%', height: '400px' }}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default CombinedEthicsChart;
