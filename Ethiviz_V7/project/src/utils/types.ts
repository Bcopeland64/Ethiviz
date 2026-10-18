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

// Upgrade 52 — ethiviz/metrics/individual_fairness.py, run directly on a
// lens's per-text scores (no protected-attribute labels needed, unlike
// group fairness). Only present when the job was submitted with
// advanced_options.include_statistical_metrics = true, and only for a lens
// with enough texts for a meaningful neighbor comparison.
export interface IndividualFairnessEntry {
  consistency_score: number;
  sample_distortion_score: number;
  k_neighbors: number;
  interpretation: string;
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
  // Present only when below 1.0 (full coverage) — see compute_tradition_scores.
  analysis_coverage?: number;
  individual_fairness?: IndividualFairnessEntry | null;
}

// Upgrade 51 — ethiviz/frameworks/dimension_map.py's CrossCulturalDimensionMap,
// read from a shared moral construct's scores across all contributing
// lenses. is_consensus = multiple traditions independently flag the same
// construct; is_tradition_specific = only one (distinctive_lens) does.
export interface ConstructReading {
  construct_id: string;
  description: string;
  scores: { [lensId: string]: number };
  contributing_lenses: string[];
  mean_score: number;
  spread: number;
  flagged_lenses: string[];
  is_consensus: boolean;
  is_tradition_specific: boolean;
  distinctive_lens: string | null;
  interpretation: string;
}

// ethiviz/frameworks/conflict.py's ConflictResolver — two lenses reading the
// same content in opposite directions (e.g. individual-rights framing vs.
// communal-harm framing), with a documented resolution_strategy rather than
// silently averaging the disagreement away.
export interface FrameworkConflictEntry {
  conflict_id: string;
  conflict_type: string;
  lenses_involved: string[];
  lens_a_score: number;
  lens_b_score: number;
  divergence_score: number;
  resolution_strategy: string;
  rationale: string;
}

// Upgrade 51 — Scripts/ethiviz_bridge.py's _serialize_dimension_findings,
// present on a completed text (or text_and_image) job's results.
export interface DimensionFindings {
  construct_readings: ConstructReading[];
  consensus_findings: ConstructReading[];
  tradition_specific_findings: ConstructReading[];
  conflicts: FrameworkConflictEntry[];
  synergy_amplifications: string[];
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
  dimension_findings?: DimensionFindings;
  [key: string]: any;
}