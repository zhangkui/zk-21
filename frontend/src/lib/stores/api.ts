import axios from 'axios';
import type {
  SeaArea,
  Cage,
  Farmer,
  DiseaseReport,
  MortalityReport,
  InspectionRoute,
  InspectionRecord,
  InspectionPoint,
  DashboardStats,
  MonthlyTrend,
  HighRiskArea,
  RecentReport,
  ApiResponse
} from '$lib/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const isBrowser = typeof window !== 'undefined';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  if (isBrowser) {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    if (isBrowser && error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

export const apiClient = api;

export const seaAreaApi = {
  getAll: () => api.get<ApiResponse<SeaArea[]>>('/core/sea-areas/'),
  getById: (id: number) => api.get<SeaArea>(`/core/sea-areas/${id}/`),
  create: (data: Partial<SeaArea>) => api.post<SeaArea>('/core/sea-areas/', data),
  update: (id: number, data: Partial<SeaArea>) => api.put<SeaArea>(`/core/sea-areas/${id}/`, data),
  delete: (id: number) => api.delete(`/core/sea-areas/${id}/`),
  getHighRiskAreas: () => api.get<HighRiskArea[]>('/core/sea-areas/high_risk_areas/')
};

export const cageApi = {
  getAll: (params?: Record<string, any>) => api.get<ApiResponse<Cage[]>>('/core/cages/', { params }),
  getById: (id: number) => api.get<Cage>(`/core/cages/${id}/`),
  create: (data: Partial<Cage> & { farmer_ids?: number[] }) => api.post<Cage>('/core/cages/', data),
  update: (id: number, data: Partial<Cage> & { farmer_ids?: number[] }) => api.put<Cage>(`/core/cages/${id}/`, data),
  delete: (id: number) => api.delete(`/core/cages/${id}/`),
  getHighRisk: () => api.get('/core/cages/high_risk/'),
  getStatistics: () => api.get('/core/cages/statistics/')
};

export const farmerApi = {
  getAll: () => api.get<ApiResponse<Farmer[]>>('/core/farmers/'),
  getById: (id: number) => api.get<Farmer>(`/core/farmers/${id}/`),
  create: (data: Partial<Farmer>) => api.post<Farmer>('/core/farmers/', data),
  update: (id: number, data: Partial<Farmer>) => api.put<Farmer>(`/core/farmers/${id}/`, data),
  delete: (id: number) => api.delete(`/core/farmers/${id}/`),
  getCages: (id: number) => api.get<Cage[]>(`/core/farmers/${id}/cages/`)
};

export const cageFarmerApi = {
  getAll: () => api.get('/core/cage-farmers/'),
  create: (data: { cage: number; farmer: number; start_date?: string }) => api.post('/core/cage-farmers/', data),
  delete: (id: number) => api.delete(`/core/cage-farmers/${id}/`)
};

export const diseaseReportApi = {
  getAll: (params?: Record<string, string>) => api.get<ApiResponse<DiseaseReport[]>>('/disease/disease-reports/', { params }),
  getById: (id: number) => api.get<DiseaseReport>(`/disease/disease-reports/${id}/`),
  create: (data: FormData | Partial<DiseaseReport>) => api.post<DiseaseReport>('/disease/disease-reports/', data, {
    headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
  }),
  update: (id: number, data: FormData | Partial<DiseaseReport>) => api.put<DiseaseReport>(`/disease/disease-reports/${id}/`, data, {
    headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
  }),
  delete: (id: number) => api.delete(`/disease/disease-reports/${id}/`),
  process: (id: number, data: { treated_by: string; treatment_method: string }) => api.post(`/disease/disease-reports/${id}/process/`, data),
  resolve: (id: number) => api.post(`/disease/disease-reports/${id}/resolve/`)
};

export const mortalityReportApi = {
  getAll: (params?: Record<string, string>) => api.get<ApiResponse<MortalityReport[]>>('/disease/mortality-reports/', { params }),
  getById: (id: number) => api.get<MortalityReport>(`/disease/mortality-reports/${id}/`),
  create: (data: FormData | Partial<MortalityReport>) => api.post<MortalityReport>('/disease/mortality-reports/', data, {
    headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
  }),
  update: (id: number, data: FormData | Partial<MortalityReport>) => api.put<MortalityReport>(`/disease/mortality-reports/${id}/`, data, {
    headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
  }),
  delete: (id: number) => api.delete(`/disease/mortality-reports/${id}/`),
  process: (id: number, data: { treated_by: string; treatment_method: string }) => api.post(`/disease/mortality-reports/${id}/process/`, data),
  resolve: (id: number) => api.post(`/disease/mortality-reports/${id}/resolve/`)
};

export const anomalyDetectionApi = {
  getHighRiskAreas: () => api.get('/disease/anomaly-detection/high_risk_areas/'),
  getHighRiskSummary: () => api.get('/disease/anomaly-detection/high_risk_summary/'),
  runAll: () => api.post('/disease/anomaly-detection/run_all/'),
  runDisease: () => api.post('/disease/anomaly-detection/run_disease/'),
  runMortality: () => api.post('/disease/anomaly-detection/run_mortality/')
};

export const inspectionRouteApi = {
  getAll: () => api.get<ApiResponse<InspectionRoute[]>>('/inspection/routes/'),
  getById: (id: number) => api.get<InspectionRoute>(`/inspection/routes/${id}/`),
  create: (data: Partial<InspectionRoute>) => api.post<InspectionRoute>('/inspection/routes/', data),
  update: (id: number, data: Partial<InspectionRoute>) => api.put<InspectionRoute>(`/inspection/routes/${id}/`, data),
  delete: (id: number) => api.delete(`/inspection/routes/${id}/`)
};

export const inspectionRecordApi = {
  getAll: () => api.get<ApiResponse<InspectionRecord[]>>('/inspection/records/'),
  getById: (id: number) => api.get<InspectionRecord>(`/inspection/records/${id}/`),
  create: (data: Partial<InspectionRecord>) => api.post<InspectionRecord>('/inspection/records/', data),
  update: (id: number, data: Partial<InspectionRecord>) => api.put<InspectionRecord>(`/inspection/records/${id}/`, data),
  delete: (id: number) => api.delete(`/inspection/records/${id}/`),
  start: (id: number) => api.post(`/inspection/records/${id}/start/`),
  complete: (id: number) => api.post(`/inspection/records/${id}/complete/`)
};

export const inspectionPointApi = {
  getAll: (recordId?: number) => api.get('/inspection/points/', recordId ? { params: { record: recordId } } : undefined),
  create: (data: Partial<InspectionPoint>) => api.post<InspectionPoint>('/inspection/points/', data),
  update: (id: number, data: Partial<InspectionPoint>) => api.put<InspectionPoint>(`/inspection/points/${id}/`, data),
  delete: (id: number) => api.delete(`/inspection/points/${id}/`)
};

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>('/core/dashboard/stats/'),
  getMonthlyTrends: () => api.get<MonthlyTrend[]>('/core/dashboard/monthly_trends/'),
  getHighRiskAreas: () => api.get<HighRiskArea[]>('/core/sea-areas/high_risk_areas/'),
  getRecentReports: () => api.get<RecentReport[]>('/disease/dashboard/recent_reports/')
};

export const analyticsApi = {
  getDiseaseTrends: () => api.get('/disease/analytics/disease_trends/'),
  getMortalityStats: () => api.get('/disease/analytics/mortality_stats/'),
  getHeatmapData: () => api.get('/core/analytics/heatmap/'),
  getFarmerResponsibility: () => api.get('/core/analytics/farmer_responsibility/')
};
