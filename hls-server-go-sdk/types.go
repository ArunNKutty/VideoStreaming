package hlsserver

import (
	"fmt"
	"time"
)

// VideoStatus represents the status of a video processing job
type VideoStatus string

const (
	VideoStatusUploading  VideoStatus = "uploading"
	VideoStatusProcessing VideoStatus = "processing"
	VideoStatusReady      VideoStatus = "ready"
	VideoStatusFailed     VideoStatus = "failed"
	VideoStatusDeleted    VideoStatus = "deleted"
)

// AuthResponse represents the authentication response
type AuthResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
}

// VideoInfo contains metadata about a video
type VideoInfo struct {
	Duration int     `json:"duration,omitempty"`
	Width    int     `json:"width,omitempty"`
	Height   int     `json:"height,omitempty"`
	Bitrate  int     `json:"bitrate,omitempty"`
	Codec    string  `json:"codec,omitempty"`
	FPS      float64 `json:"fps,omitempty"`
	FileSize int64   `json:"file_size,omitempty"`
}

// VideoAsset represents a video asset in the system
type VideoAsset struct {
	ID           string      `json:"id"`
	Filename     string      `json:"filename"`
	Status       VideoStatus `json:"status"`
	Info         *VideoInfo  `json:"info,omitempty"`
	HLSURL       string      `json:"hls_url,omitempty"`
	PlayerURL    string      `json:"player_url,omitempty"`
	CreatedAt    time.Time   `json:"created_at"`
	UpdatedAt    time.Time   `json:"updated_at"`
	ErrorMessage string      `json:"error_message,omitempty"`
}

// UploadResponse represents the response from video upload
type UploadResponse struct {
	Success bool       `json:"success"`
	VideoID string     `json:"video_id"`
	Message string     `json:"message"`
	Asset   VideoAsset `json:"asset"`
}

// UploadOptions contains options for video upload
type UploadOptions struct {
	// Filename override (optional, will use file's name if not provided)
	Filename string

	// Callback URL for processing completion notification (optional)
	CallbackURL string

	// Custom metadata (optional)
	Metadata map[string]string

	// Processing options
	ProcessingOptions *ProcessingOptions
}

// ProcessingOptions contains video processing configuration
type ProcessingOptions struct {
	// HLS segment duration in seconds (default: 10)
	SegmentDuration int `json:"segment_duration,omitempty"`

	// HLS playlist type (default: "vod")
	PlaylistType string `json:"playlist_type,omitempty"`

	// Video quality settings
	Quality *QualitySettings `json:"quality,omitempty"`
}

// QualitySettings contains video quality configuration
type QualitySettings struct {
	// Video bitrate in kbps
	VideoBitrate int `json:"video_bitrate,omitempty"`

	// Audio bitrate in kbps
	AudioBitrate int `json:"audio_bitrate,omitempty"`

	// Video resolution (e.g., "1920x1080", "1280x720")
	Resolution string `json:"resolution,omitempty"`

	// Frame rate
	FrameRate float64 `json:"frame_rate,omitempty"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
	Version   string    `json:"version"`
	Uptime    float64   `json:"uptime,omitempty"`
}

// ErrorResponse represents an API error response
type ErrorResponse struct {
	ErrorCode string `json:"error"`
	Message   string `json:"message"`
	Details   string `json:"details,omitempty"`
}

// Error implements the error interface for ErrorResponse
func (e ErrorResponse) Error() string {
	if e.Details != "" {
		return fmt.Sprintf("%s: %s (%s)", e.ErrorCode, e.Message, e.Details)
	}
	return fmt.Sprintf("%s: %s", e.ErrorCode, e.Message)
}

// VideoListOptions contains options for listing videos
type VideoListOptions struct {
	// Page number (default: 1)
	Page int

	// Number of items per page (default: 10, max: 100)
	PerPage int

	// Filter by status
	Status VideoStatus

	// Sort order: "created_at", "-created_at", "updated_at", "-updated_at"
	Sort string
}

// VideoListResponse represents the response from video list endpoint
type VideoListResponse struct {
	Videos  []VideoAsset `json:"videos"`
	Total   int          `json:"total"`
	Page    int          `json:"page"`
	PerPage int          `json:"per_page"`
	Pages   int          `json:"pages"`
}

// StreamingURLOptions contains options for generating streaming URLs
type StreamingURLOptions struct {
	// Expiration time for the URL (optional)
	ExpiresAt *time.Time

	// IP address restriction (optional)
	AllowedIP string

	// Referrer restriction (optional)
	AllowedReferrer string
}

// StreamingURLResponse represents the response from streaming URL generation
type StreamingURLResponse struct {
	HLSURL    string    `json:"hls_url"`
	ExpiresAt time.Time `json:"expires_at,omitempty"`
}
