export interface FarmerInfo {
  id: number;
  name: string;
  phone: string;
}

export interface SeaArea {
  id: number;
  name: string;
  location: string;
  area: number;
  depth?: number;
  boundary?: [number, number][];
  center_lat?: number;
  center_lng?: number;
  description?: string;
  created_at: string;
  updated_at: string;
  cage_count?: number;
  farmer_count?: number;
  cages?: Cage[];
  farmers?: FarmerInfo[];
}

export interface Farmer {
  id: number;
  name: string;
  phone: string;
  id_card: string;
  sea_area?: number;
  sea_area_name?: string;
  scale?: string;
  registration_date?: string;
  contact_info?: string;
  created_at: string;
  updated_at: string;
  cage_farmers?: CageFarmer[];
}

export interface CageFarmer {
  id: number;
  cage: number;
  cage_code?: string;
  farmer: number;
  farmer_name?: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
}

export interface Cage {
  id: number;
  code: string;
  sea_area?: number;
  sea_area_name?: string;
  location: string;
  capacity: number;
  species?: string;
  stocking_date?: string;
  status: 'normal' | 'maintenance' | 'empty' | 'abnormal';
  area?: number;
  created_at: string;
  updated_at: string;
  cage_farmers?: CageFarmer[];
  farmer_names?: string[];
  farmers?: FarmerInfo[];
  farmer_ids?: number[];
  is_high_risk?: boolean;
  risk_level?: string;
  inspection_points?: InspectionPoint[];
  disease_reports?: DiseaseReport[];
  mortality_reports?: MortalityReport[];
}

export interface DiseaseReport {
  id: number;
  cage: number;
  cage_code?: string;
  reporter: number | null;
  reporter_name?: string;
  report_time: string;
  disease_type: 'bacterial' | 'viral' | 'parasitic' | 'fungal' | 'nutritional' | 'environmental' | 'other';
  severity: 'mild' | 'moderate' | 'severe' | 'critical';
  image?: string;
  description: string;
  status: 'pending' | 'processing' | 'resolved' | 'closed';
  treated_by?: string;
  treatment_method?: string;
  treatment_time?: string;
  is_anomaly: boolean;
  anomaly_score: number;
  created_at: string;
  updated_at: string;
}

export interface MortalityReport {
  id: number;
  cage: number;
  cage_code?: string;
  reporter: number | null;
  reporter_name?: string;
  report_time: string;
  mortality_count: number;
  cause: 'disease' | 'predation' | 'environment' | 'feeding' | 'operation' | 'unknown' | 'other';
  image?: string;
  description: string;
  status: 'pending' | 'processing' | 'resolved' | 'closed';
  treated_by?: string;
  treatment_method?: string;
  treatment_time?: string;
  is_anomaly: boolean;
  anomaly_score: number;
  created_at: string;
  updated_at: string;
}

export interface InspectionRoute {
  id: number;
  name: string;
  description?: string;
  cages: number[];
  cage_details?: Cage[];
  creator?: number | null;
  creator_name?: string;
  created_at: string;
  updated_at: string;
}

export interface InspectionRouteCage {
  id: number;
  route: number;
  cage: number;
  order: number;
  created_at: string;
}

export interface InspectionRecord {
  id: number;
  route: number;
  route_name?: string;
  inspector: number | null;
  inspector_name?: string;
  start_time?: string;
  end_time?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  remarks?: string;
  created_at: string;
  updated_at: string;
  points?: InspectionPoint[];
}

export interface InspectionPoint {
  id: number;
  record: number;
  cage: number;
  cage_code?: string;
  check_time: string;
  water_temperature?: number;
  salinity?: number;
  ph_value?: number;
  water_quality?: 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor';
  abnormal_condition?: string;
  has_abnormality: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  sea_areas_count: number;
  cages_count: number;
  farmers_count: number;
  pending_reports_count: number;
}

export interface MonthlyTrend {
  month: string;
  disease_count: number;
  mortality_count: number;
  inspection_count: number;
}

export interface HighRiskArea {
  id: number;
  name: string;
  lat: number;
  lng: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface RecentReport {
  id: number;
  type: 'disease' | 'mortality';
  cage_code: string;
  report_time: string;
  status: string;
  description: string;
}

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  user_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface UserRoleInfo {
  id: number;
  name: string;
  code: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  role?: UserRoleInfo | null;
  role_id?: number | null;
  role_code?: string;
  role_name?: string;
  phone?: string;
  profile_phone?: string;
  display_name?: string;
  is_admin?: boolean;
  farmer_id?: number | null;
  date_joined?: string;
  token?: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface ApiResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results: T;
}
