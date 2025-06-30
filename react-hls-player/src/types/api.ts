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

export interface ApiError {
  error: string;
  message: string;
  details?: string;
  timestamp: string;
}
