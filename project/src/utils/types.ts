// API response for /api/analyze
export interface AnalyzeResponse {
  job_id: string;
  status_url: string;
  status?: string;
}

// API response for /api/analyze/status/{job_id}
export interface AnalyzeStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  results_url?: string;
  error_message?: string;
}

// API response for /api/analyze/results/{job_id}
export interface AnalyzeResultsResponse {
  results: AnalysisResults;
}

// Text analysis result for a single item
export interface TextAnalysisItem {
  text_id: string;
  original_text: string;
  bias_score?: number;
  diversity_index?: number;
  western_ethics_score?: number;
  ubuntu_ethics_score?: number;
  confucian_ethics_score?: number;
  islamic_ethics_score?: number;
  [key: string]: any;
}

// Image analysis result for a single image
export interface ImageAnalysisItem {
  analysis: {
    bias_score?: number;
    diversity_index?: number;
    western_ethics_score?: number;
    ubuntu_ethics_score?: number;
    confucian_ethics_score?: number;
    islamic_ethics_score?: number;
    face_count?: number;
    object_count?: number;
    [key: string]: any;
  };
  image_url?: string;
  original_path?: string;
  [key: string]: any;
}

// The overall analysis results object
export interface AnalysisResults {
  text_analysis?: TextAnalysisItem[];
  image_analysis?: { [imageName: string]: ImageAnalysisItem };
  [key: string]: any;
} 