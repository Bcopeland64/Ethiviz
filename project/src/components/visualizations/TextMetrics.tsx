// Timestamp: 2024-05-22 15:13:09 UTC (This will be replaced by actual execution time)
// Ensuring all imports are at the top and file structure is correct.
import React from 'react';
import { TrendingUp, Zap, Scale, ShieldCheck, Users, BookOpen, Globe } from 'lucide-react'; // Example icons
import { calculateAverageScore } from '../../utils/visualizationUtils';

interface TextMetricProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
}

const MetricCard: React.FC<TextMetricProps> = ({ title, value, description, icon }) => (
  <div className="bg-white p-4 shadow rounded-lg flex items-start space-x-3">
    {icon && <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white">{icon}</div>}
    <div>
      <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
      {description && <p className="text-xs text-gray-400">{description}</p>}
    </div>
  </div>
);

interface TextMetricsProps {
  // Assuming textResults is an array of objects, each representing an analyzed text item
  // If it can be a single object, the component should handle that too.
  textResults: any | any[]; 
}

const TextMetrics: React.FC<TextMetricsProps> = ({ textResults }) => {
  const resultsArray = Array.isArray(textResults) ? textResults : (textResults ? [textResults] : []);

  const formatScore = (score: number | null) => score !== null ? score.toFixed(2) : "N/A";

  const avgBiasScore = formatScore(calculateAverageScore(resultsArray, 'bias_score'));
  const avgDiversityIndex = formatScore(calculateAverageScore(resultsArray, 'diversity_index'));
  const avgWesternScore = formatScore(calculateAverageScore(resultsArray, 'western_ethics_score'));
  const avgUbuntuScore = formatScore(calculateAverageScore(resultsArray, 'ubuntu_ethics_score'));
  const avgConfucianScore = formatScore(calculateAverageScore(resultsArray, 'confucian_ethics_score'));
  const avgIslamicScore = formatScore(calculateAverageScore(resultsArray, 'islamic_ethics_score'));

  const metrics = [
    { title: "Avg. Bias Score", value: avgBiasScore, icon: <Scale size={20}/>, description: "Overall bias level" },
    { title: "Avg. Diversity Index", value: avgDiversityIndex, icon: <Users size={20}/>, description: "Content diversity" },
    { title: "Avg. Western Ethics", value: avgWesternScore, icon: <Globe size={20}/>, description: "Alignment with Western traditions" },
    { title: "Avg. Ubuntu Ethics", value: avgUbuntuScore, icon: <Zap size={20}/>, description: "Alignment with Ubuntu traditions" },
    { title: "Avg. Confucian Ethics", value: avgConfucianScore, icon: <BookOpen size={20}/>, description: "Alignment with Confucian traditions" },
    { title: "Avg. Islamic Ethics", value: avgIslamicScore, icon: <ShieldCheck size={20}/>, description: "Alignment with Islamic traditions" },
  ];

  if (resultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No text data to calculate metrics.</p>;
  }

  return (
    <div>
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Key Text Metrics</h3>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map(metric => (
          <MetricCard key={metric.title} title={metric.title} value={metric.value} icon={metric.icon} description={metric.description} />
        ))}
      </div>
    </div>
  );
};

export default TextMetrics;
