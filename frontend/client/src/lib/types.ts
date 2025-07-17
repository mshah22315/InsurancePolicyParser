export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DashboardStats {
  totalPolicies: number;
  processingQueue: number;
  completedToday: number;
  avgProcessingTime: string;
}

export interface PolicyUploadResponse {
  taskId: string;
  message: string;
}

export interface WebSocketMessage {
  type: 'task_started' | 'task_progress' | 'task_completed' | 'task_failed';
  taskId: string;
  progress?: number;
  status?: ProcessingStatus;
  filename?: string;
  error?: string;
}

export interface AvailableFeature {
  name: string;
  description: string;
  discountPercentage?: number;
}

export const AVAILABLE_FEATURES: AvailableFeature[] = [
  { name: 'Monitored Alarm', description: '24/7 monitoring security system', discountPercentage: 5 },
  { name: 'Sprinkler System', description: 'Fire suppression system', discountPercentage: 10 },
  { name: 'Impact Resistant Roof', description: 'Storm-resistant roofing material', discountPercentage: 15 },
  { name: 'New Construction', description: 'Less than 5 years old', discountPercentage: 10 },
  { name: 'Security Camera', description: 'Surveillance system', discountPercentage: 3 },
  { name: 'Smart Home System', description: 'Connected home automation', discountPercentage: 5 },
  { name: 'Storm Shutters', description: 'Hurricane protection', discountPercentage: 8 },
  { name: 'Backup Generator', description: 'Emergency power system', discountPercentage: 7 },
];
