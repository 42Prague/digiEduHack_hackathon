/**
 * API Endpoints
 * -------------
 * Centralized API endpoint functions using the API client.
 */

import apiClient, {
  UnifiedIngestionResponse,
  DatasetInfo,
  TranscriptDetail,
  TranscriptSummary,
  DQReport,
  RegionInsights,
  Recommendations,
  SchoolComparison,
  AnalyticsSummary,
} from './client';

// Ingestion endpoints
export const ingestionApi = {
  ingestFile: async (file: File): Promise<UnifiedIngestionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<UnifiedIngestionResponse>('/ingestion/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadAudio: async (
    file: File,
    metadata: {
      school_id: string;
      region_id: string;
      school_type: string;
      intervention_type: string;
      participant_role: string;
      interview_date: string;
    }
  ): Promise<UnifiedIngestionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));
    
    const response = await apiClient.post<UnifiedIngestionResponse>('/ingestion/upload_audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listDatasets: async (): Promise<DatasetInfo[]> => {
    const response = await apiClient.get<DatasetInfo[]>('/ingestion/datasets');
    return response.data;
  },

  getDQReport: async (datasetId: string): Promise<DQReport> => {
    const response = await apiClient.get<DQReport>(`/ingestion/dq_report/${datasetId}`);
    return response.data;
  },
};

// Transcript endpoints
export const transcriptsApi = {
  getTranscript: async (id: string): Promise<TranscriptDetail> => {
    const response = await apiClient.get<TranscriptDetail>(`/transcripts/${id}`);
    return response.data;
  },

  listTranscripts: async (filters?: {
    school_id?: string;
    region_id?: string;
    school_type?: string;
    intervention_type?: string;
    participant_role?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<TranscriptSummary[]> => {
    const response = await apiClient.get<TranscriptSummary[]>('/transcripts/', {
      params: filters,
    });
    return response.data;
  },
};

// Analytics endpoints
export const analyticsApi = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const response = await apiClient.get<AnalyticsSummary>('/analytics/summary');
    return response.data;
  },

  getRegionInsights: async (regionId: string): Promise<RegionInsights> => {
    const response = await apiClient.get<RegionInsights>('/analytics/region_insights', {
      params: { region_id: regionId },
    });
    return response.data;
  },

  getRecommendations: async (params?: {
    school_id?: string;
    region_id?: string;
  }): Promise<Recommendations> => {
    const response = await apiClient.get<Recommendations>('/analytics/recommendations', {
      params,
    });
    return response.data;
  },

  getTrends: async (metric: string): Promise<any> => {
    const response = await apiClient.get('/analytics/trends', {
      params: { metric },
    });
    return response.data;
  },
};

// Schools endpoints
export const schoolsApi = {
  compareSchools: async (
    school_ids: string[],
    metric?: string
  ): Promise<SchoolComparison> => {
    // Backend expects 'names' parameter (comma-separated school IDs/names)
    const response = await apiClient.get<SchoolComparison>('/schools/compare', {
      params: {
        names: school_ids.join(','), // Backend uses 'names' param but accepts school_ids
        metric,
      },
    });
    return response.data;
  },

  compareByDimension: async (
    dimension: 'school_type' | 'intervention_type' | 'participant_role',
    filters?: {
      school_type?: string;
      intervention_type?: string;
      participant_role?: string;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<{ dimension: string; groups: Record<string, any> }> => {
    const response = await apiClient.get('/schools/compare_by_dimension', {
      params: {
        dimension,
        ...filters,
      },
    });
    return response.data;
  },
};

// Search endpoint
export const searchApi = {
  search: async (query: string): Promise<any[]> => {
    const response = await apiClient.get('/search', {
      params: { q: query },
    });
    return response.data;
  },
};

