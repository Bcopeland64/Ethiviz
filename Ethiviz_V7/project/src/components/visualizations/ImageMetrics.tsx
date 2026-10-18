import React from 'react';
import { Image as ImageIcon, Users, Scale, Globe, Zap, BookOpen, ShieldCheck } from 'lucide-react';
import MetricCard from '../common/MetricCard';
import { calculateAverageScore } from '../../utils/visualizationUtils';
import { ImageAnalysisItem } from '../../utils/types';

interface ImageMetricsProps {
  imageResults: { [imageName: string]: ImageAnalysisItem };
}

const ImageMetrics: React.FC<ImageMetricsProps> = ({ imageResults }) => {
  const resultsArray = imageResults ? Object.values(imageResults) : [];

  const formatScore = (score: number | null) => score !== null ? score.toFixed(2) : "N/A";

  const totalImages = resultsArray.length;
  const avgDiversityIndex = formatScore(calculateAverageScore(resultsArray, 'diversity_index', true));
  const avgBiasScore = formatScore(calculateAverageScore(resultsArray, 'bias_score', true));
  const avgWesternScore = formatScore(calculateAverageScore(resultsArray, 'western_ethics_score', true));
  const avgUbuntuScore = formatScore(calculateAverageScore(resultsArray, 'ubuntu_ethics_score', true));
  const avgConfucianScore = formatScore(calculateAverageScore(resultsArray, 'confucian_ethics_score', true));
  const avgIslamicScore = formatScore(calculateAverageScore(resultsArray, 'islamic_ethics_score', true));

  const metrics = [
    { title: "Total Images Processed", value: totalImages, icon: <ImageIcon size={20}/>, description: "Number of images analyzed", colorClass: 'bg-green-500' },
    { title: "Avg. Diversity Index", value: avgDiversityIndex, icon: <Users size={20}/>, description: "Visual diversity", colorClass: 'bg-green-500' },
    { title: "Avg. Bias Score", value: avgBiasScore, icon: <Scale size={20}/>, description: "Overall visual bias", colorClass: 'bg-green-500' },
    { title: "Avg. Western Ethics", value: avgWesternScore, icon: <Globe size={20}/>, description: "Alignment with Western traditions", colorClass: 'bg-green-500' },
    { title: "Avg. Ubuntu Ethics", value: avgUbuntuScore, icon: <Zap size={20}/>, description: "Alignment with Ubuntu traditions", colorClass: 'bg-green-500' },
    { title: "Avg. Confucian Ethics", value: avgConfucianScore, icon: <BookOpen size={20}/>, description: "Alignment with Confucian traditions", colorClass: 'bg-green-500' },
    { title: "Avg. Islamic Ethics", value: avgIslamicScore, icon: <ShieldCheck size={20}/>, description: "Alignment with Islamic traditions", colorClass: 'bg-green-500' },
  ];

  if (resultsArray.length === 0) {
    return <p className="text-sm text-gray-500">No image data to calculate metrics.</p>;
  }

  return (
    <div>
      <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Key Image Metrics</h3>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {metrics.map(metric => (
          <MetricCard key={metric.title} title={metric.title} value={metric.value} icon={metric.icon} description={metric.description} colorClass={metric.colorClass} />
        ))}
      </div>
    </div>
  );
};

export default ImageMetrics;
