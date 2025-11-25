/**
 * API Client
 * ----------
 * Centralized API client with unified error handling and TanStack Query integration.
 */

import axios, { AxiosError, AxiosInstance } from 'axios';

// Get API URL from environment variable, fallback to /api for production
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// Debug log (only in development)
if (import.meta.env.DEV) {
  console.log('🔧 API Configuration:', {
    VITE_API_URL: import.meta.env.VITE_API_URL,
    API_BASE,
    mode: import.meta.env.MODE,
  });
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60 seconds for file uploads
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for unified error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle unified error format from backend
    if (error.response?.data) {
      const errorData = error.response.data as any;
      if (errorData.error) {
        // Backend returns {success: false, error: {type, message, details}}
        const apiError = new Error(errorData.error.message || 'An error occurred');
        (apiError as any).type = errorData.error.type || 'InternalError';
        (apiError as any).details = errorData.error.details || {};
        (apiError as any).status = error.response.status;
        return Promise.reject(apiError);
      }
    }
    
    // Fallback for non-API errors
    const defaultError = new Error(error.message || 'Network error');
    (defaultError as any).type = 'NetworkError';
    (defaultError as any).status = error.response?.status || 0;
    return Promise.reject(defaultError);
  }
);

export default apiClient;

// API Response types
export interface ApiError {
  type: string;
  message: string;
  details?: Record<string, any>;
  status?: number;
}

export interface UnifiedIngestionResponse {
  success: boolean;
  dataset_id: string;
  filename: string;
  file_type: string;
  stored_path: string;
  normalized_path: string;
  classification: 'quantitative' | 'qualitative' | 'transcript' | 'audio';
  row_count: number | null;
  columns: Array<{
    name: string;
    dtype: string;
    null_ratio: number;
    is_numeric: boolean;
  }> | null;
  numeric_ratio: number | null;
  summary: {
    name: string;
    classification: string;
    row_count?: number;
    metrics?: Record<string, Record<string, number>>;
    themes?: string[];
    generated_at: string;
  };
  summary_path: string;
  dq_report_path: string | null;
  auto_summary?: string | null;
  metadata?: Record<string, any>;
  cultural_analysis?: {
    mindset_shift_score: number;
    collaboration_score: number;
    teacher_confidence_score: number;
    cooperation_municipality_score: number;
    sentiment: number;
    themes: string[];
    practical_change: string;
    mindset_change: string;
    impact_summary: string;
    culture_change_detected: boolean;
  };
}

export interface DatasetInfo {
  dataset_name: string;
  dataset_id: string;
  file_type: 'table' | 'text' | 'unknown';
  row_count: number | null;
  columns: string[] | null;
  dq_score: number | null;
  ingested_at: string | null;
  summary_path: string;
  dq_report_path: string | null;
  normalized_path: string;
  raw_files: string[];
}

export interface TranscriptDetail {
  id: string;
  metadata: {
    school_id: string;
    region_id: string;
    school_type: string;
    intervention_type: string;
    participant_role: string;
    interview_date: string;
  };
  transcript_text: string | null;
  clean_text: string | null;
  cultural_analysis: {
    mindset_shift_score: number;
    collaboration_score: number;
    teacher_confidence_score: number;
    municipality_cooperation_score: number;
    sentiment_score: number;
    themes: string[];
    practical_change: string;
    mindset_change: string;
    impact_summary: string;
    culture_change_detected: boolean;
  } | null;
  dq_report: {
    dq_score: number;
    total_rows: number;
    valid_rows: number;
    invalid_rows: number;
    missing_values: Record<string, number>;
    pii_found_and_masked: {
      names: number;
      emails: number;
      phones: number;
    };
    schema_issues: Array<{column: string; issue: string}>;
    normalization_fixes: string[];
  } | null;
  file_paths: Record<string, string>;
  file_type: string;
  original_filename: string;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSummary {
  id: string;
  school_id: string | null;
  region_id: string | null;
  school_type: string | null;
  intervention_type: string | null;
  participant_role: string | null;
  interview_date: string | null;
  created_at: string | null;
}

export interface DQReport {
  dq_score: number;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  missing_values: Record<string, number>;
  pii_found_and_masked: {
    names: number;
    emails: number;
    phones: number;
  };
  schema_issues: Array<{column: string; issue: string}>;
  normalization_fixes: string[];
  quarantined_rows_path: string | null;
  report_path?: string;
}

export interface RegionInsights {
  region_id: string;
  summary: {
    total_transcripts: number;
    avg_mindset_shift: number;
    avg_collaboration: number;
    avg_confidence: number;
    avg_municipality_cooperation: number;
    avg_sentiment: number;
  };
  top_schools: Array<{
    school_id: string;
    scores: Record<string, number>;
  }>;
  schools_needing_support: Array<{
    school_id: string;
    scores: Record<string, number>;
  }>;
  intervention_effectiveness: Record<string, {
    avg_score: number;
    count: number;
  }>;
  frequent_themes: Array<{
    theme: string;
    count: number;
  }>;
}

export interface Recommendations {
  school_recommendations: string[];
  region_recommendations: string[];
  intervention_recommendations: string[];
  culture_warnings: string[];
  strengths: string[];
}

export interface SchoolComparison {
  comparisons: Record<string, Record<string, number>>;
}

export interface AnalyticsSummary {
  datasets: string[];
  metrics: Record<string, {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  }>;
  generated_at: string;
}

