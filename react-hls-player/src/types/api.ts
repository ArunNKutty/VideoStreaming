// API Response Types

export interface VideoAsset {
  id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'ready' | 'failed' | 'deleted';
  duration?: number;
  created_at: string;
  updated_at: string;
  hls_url?: string;
  player_url?: string;
  error_message?: string;
  info?: VideoInfo;
}

export interface VideoInfo {
  duration?: number;
  width?: number;
  height?: number;
  bitrate?: number;
  codec?: string;
  fps?: number;
  file_size?: number;
}

export interface VideoSchedule {
  id: string;
  video_id: string;
  video_title: string;
  video_url: string;
  recipient_email: string;
  recipient_name?: string;
  sender_name: string;
  scheduled_date: string;
  frequency: FrequencyType;
  custom_cron?: string;
  timezone: string;
  subject: string;
  message?: string;
  template: EmailTemplate;
  status: ScheduleStatus;
  created_at: string;
  updated_at: string;
  last_sent?: string;
  next_send?: string;
  send_count: number;
  include_thumbnail: boolean;
  include_duration: boolean;
  auto_expire?: string;
}

export type FrequencyType = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom';
export type EmailTemplate = 'standard' | 'premium' | 'minimal' | 'custom';
export type ScheduleStatus = 'active' | 'paused' | 'completed' | 'failed';

export interface ScheduleCreateRequest {
  video_id: string;
  recipient_email: string;
  recipient_name?: string;
  sender_name?: string;
  scheduled_date: string;
  frequency?: FrequencyType;
  custom_cron?: string;
  timezone?: string;
  subject: string;
  message?: string;
  template?: EmailTemplate;
  include_thumbnail?: boolean;
  include_duration?: boolean;
  auto_expire?: string;
}

export interface ScheduleListResponse {
  schedules: VideoSchedule[];
  total: number;
  page: number;
  per_page: number;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  description?: string;
  video_id: string;
  recipient_email: string;
  status: ScheduleStatus;
  frequency: FrequencyType;
}

export interface ApiError {
  error: string;
  message: string;
  details?: string;
  timestamp: string;
}

// Form Data Types
export interface ScheduleFormData {
  video_id: string;
  recipient_email: string;
  recipient_name: string;
  sender_name: string;
  scheduled_date: string;
  frequency: FrequencyType;
  subject: string;
  message: string;
  template: EmailTemplate;
  include_thumbnail: boolean;
  include_duration: boolean;
}
