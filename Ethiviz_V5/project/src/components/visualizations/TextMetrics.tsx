import React from 'react';
import { Scale, ShieldCheck, Users, BookOpen, Globe, Zap } from 'lucide-react';
import MetricCard from '../common/MetricCard';
import { calculateAverageScore } from '../../utils/visualizationUtils';
import { TextAnalysisItem } from '../../utils/types';

interface TextMetricsProps {
  textResults: TextAnalysisItem[];
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
