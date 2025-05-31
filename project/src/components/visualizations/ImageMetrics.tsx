import React from 'react';
import { TrendingUp, Zap, Scale, ShieldCheck, Users, BookOpen, Globe, Image as ImageIcon } from 'lucide-react'; // Example icons

// Re-using MetricCard structure (or define globally if used in many places)
interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, description, icon }) => (
  <div className="bg-white p-4 shadow rounded-lg flex items-start space-x-3">
    {icon && <div className="flex-shrink-0 h-10 w-10 rounded-full bg-green-500 flex items-center justify-center text-white">{icon}</div>}
    <div>
      <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
      {description && <p className="text-xs text-gray-400">{description}</p>}
    </div>
  </div>
);

import { calculateAverageScore } from '../../utils/visualizationUtils';

interface ImageMetricsProps {
  // imageResults is a dictionary: { [imageName: string]: analysisObject }
  imageResults: { [imageName: string]: any };
}

const ImageMetrics: React.FC<ImageMetricsProps> = ({ imageResults }) => {
  const resultsArray = imageResults ? Object.values(imageResults) : [];
  
  const formatScore = (score: number | null) => score !== null ? score.toFixed(2) : "N/A";

  // Note: For imageResults, the actual analysis data might be nested under an 'analysis' key in each item.
  // The calculateAverageScore function's isImageArray=true flag handles this.
  const totalImages = resultsArray.length;
  const avgDiversityIndex = formatScore(calculateAverageScore(resultsArray, 'diversity_index', true));
  const avgBiasScore = formatScore(calculateAverageScore(resultsArray, 'bias_score', true));
  const avgWesternScore = formatScore(calculateAverageScore(resultsArray, 'western_ethics_score', true));
  const avgUbuntuScore = formatScore(calculateAverageScore(resultsArray, 'ubuntu_ethics_score', true));
  const avgConfucianScore = formatScore(calculateAverageScore(resultsArray, 'confucian_ethics_score', true));
  const avgIslamicScore = formatScore(calculateAverageScore(resultsArray, 'islamic_ethics_score', true));

  const metrics = [
    { title: "Total Images Processed", value: totalImages, icon: <ImageIcon size={20}/>, description: "Number of images analyzed" },
    { title: "Avg. Diversity Index", value: avgDiversityIndex, icon: <Users size={20}/>, description: "Visual diversity" },
    { title: "Avg. Bias Score", value: avgBiasScore, icon: <Scale size={20}/>, description: "Overall visual bias" },
    { title: "Avg. Western Ethics", value: avgWesternScore, icon: <Globe size={20}/>, description: "Alignment with Western traditions" },
    { title: "Avg. Ubuntu Ethics", value: avgUbuntuScore, icon: <Zap size={20}/>, description: "Alignment with Ubuntu traditions" },
    { title: "Avg. Confucian Ethics", value: avgConfucianScore, icon: <BookOpen size={20}/>, description: "Alignment with Confucian traditions" },
    { title: "Avg. Islamic Ethics", value: avgIslamicScore, icon: <ShieldCheck size={20}/>, description: "Alignment with Islamic traditions" },
  ];

  if (resultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No image data to calculate metrics.</p>;
  }

  return (
    <div>
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Key Image Metrics</h3>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {metrics.map(metric => (
          <MetricCard key={metric.title} title={metric.title} value={metric.value} icon={metric.icon} description={metric.description} />
        ))}
      </div>
    </div>
  );
};

export default ImageMetrics;
