// API response for /api/analyze
export interface AnalyzeResponse {
  job_id: string;
  status_url: string;
  status?: string;
}

// Progress info reported while a job is pending/processing
export interface AnalysisProgress {
  percent: number;
  message: string;
}

// API response for /api/analyze/status/{job_id}
export interface AnalyzeStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  results_url?: string;
  error_message?: string;
  progress?: AnalysisProgress;
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
  buddhist_ethics_score?: number;
  hindu_ethics_score?: number;
  indigenous_ethics_score?: number;
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
    buddhist_ethics_score?: number;
    hindu_ethics_score?: number;
    indigenous_ethics_score?: number;
    face_count?: number;
    object_count?: number;
    [key: string]: any;
  };
  image_url?: string;
  original_path?: string;
  [key: string]: any;
}

// Per-tradition aggregate score, keyed by engine framework id (e.g.
// "confucian_v2") — produced by Scripts/ethiviz_bridge.py's
// compute_tradition_scores, consumed directly by CulturalFairnessHeatmap and
// CrossCulturalEquityDashboard.
export interface TraditionScoreEntry {
  tradition: string;
  score: number;
  severity: 'low' | 'moderate' | 'high' | 'critical' | 'unknown';
  confidence?: number;
  // Present only when there's a caveat: false = relies on a machine-generated,
  // unreviewed translation; null = the lens has no translation_provenance
  // declaration at all. Absent (undefined) means no caveat applies (English,
  // or a reviewed translation).
  translation_reviewed?: boolean | null;
  warnings?: string[];
}

// GET /api/framework-coverage — ethiviz/frameworks/coverage_audit.py
export interface TraditionCoverageEntry {
  framework_id: string;
  label: string;
  prototype_count: number;
  category_count: number;
  languages_declared: string[];
  translations_reviewed: number;
  translations_machine_generated: number;
  translations_undeclared: boolean;
}

export interface FrameworkCoverageReport {
  framework_coverage_index: number;
  traditions: TraditionCoverageEntry[];
}

// The overall analysis results object
export interface AnalysisResults {
  text_analysis?: TextAnalysisItem[];
  image_analysis?: { [imageName: string]: ImageAnalysisItem };
  tradition_scores?: TraditionScoreEntry[];
  [key: string]: any;
}