import React from 'react';
import { TextAnalysisItem } from '../../utils/types';

interface TextRawDataViewProps {
  textResults: TextAnalysisItem[];
}

const TextRawDataView: React.FC<TextRawDataViewProps> = ({ textResults }) => {
  if (!textResults || textResults.length === 0) return <p>No raw text data to display.</p>;

  // Define columns to display - adjust as needed
  const columns = [
    { key: 'text_id', name: 'ID' },
    { key: 'original_text', name: 'Original Text' },
    { key: 'bias_score', name: 'Bias Score' },
    { key: 'diversity_index', name: 'Diversity Index' },
    { key: 'western_ethics_score', name: 'Western Score' },
    { key: 'ubuntu_ethics_score', name: 'Ubuntu Score' },
    { key: 'confucian_ethics_score', name: 'Confucian Score' },
    { key: 'islamic_ethics_score', name: 'Islamic Score' },
  ];

  const availableColumns = columns;

  const getTextContent = (item: TextAnalysisItem) => {
    if(item.text && typeof item.text === 'string') return item.text;
    if(item.original_text && typeof item.original_text === 'string') return item.original_text;
    if(item.text_id && typeof item.text_id === 'string') return item.text_id;
    return "N/A";
  }

  return (
    <div className="bg-white p-4 shadow rounded-lg mt-6">
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Raw Text Analysis Data</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {availableColumns.map(col => (
                <th key={col.key} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {col.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {textResults.map((item, index) => (
              <tr key={item.text_id || index}>
                {availableColumns.map(col => {
                  let cellValue = item[col.key as keyof TextAnalysisItem];
                  if (typeof cellValue === 'number') {
                    cellValue = parseFloat(cellValue.toFixed(3));
                  } else if (cellValue === null || cellValue === undefined) {
                    cellValue = "N/A";
                  }
                  if (col.key === 'original_text') {
                     const textPreview = getTextContent(item);
                     cellValue = textPreview.substring(0,100) + (textPreview.length > 100 ? "..." : "");
                  }
                  if (col.key === 'text_id') {
                    cellValue = item.text_id || `Item ${index + 1}`;
                  }
                  return (
                    <td key={col.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {String(cellValue)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TextRawDataView;
