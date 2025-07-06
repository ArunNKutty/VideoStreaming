package hlsserver

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

// UploadVideo uploads a video file to the HLS server
func (c *Client) UploadVideo(ctx context.Context, filePath string, options *UploadOptions) (*UploadResponse, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	return c.UploadVideoFromReader(ctx, file, filepath.Base(filePath), options)
}

// UploadVideoFromReader uploads a video from an io.Reader
func (c *Client) UploadVideoFromReader(ctx context.Context, reader io.Reader, filename string, options *UploadOptions) (*UploadResponse, error) {
	if options == nil {
		options = &UploadOptions{}
	}

	// Use provided filename or default
	if options.Filename != "" {
		filename = options.Filename
	}

	// Create multipart form
	pipeReader, pipeWriter := io.Pipe()
	multipartWriter := multipart.NewWriter(pipeWriter)

	// Start goroutine to write multipart data
	go func() {
		defer pipeWriter.Close()
		defer multipartWriter.Close()

		// Add file field
		fileWriter, err := multipartWriter.CreateFormFile("file", filename)
		if err != nil {
			pipeWriter.CloseWithError(fmt.Errorf("failed to create form file: %w", err))
			return
		}

		if _, err := io.Copy(fileWriter, reader); err != nil {
			pipeWriter.CloseWithError(fmt.Errorf("failed to copy file data: %w", err))
			return
		}

		// Add optional fields
		if options.CallbackURL != "" {
			if err := multipartWriter.WriteField("callback_url", options.CallbackURL); err != nil {
				pipeWriter.CloseWithError(fmt.Errorf("failed to write callback_url: %w", err))
				return
			}
		}

		// Add metadata as JSON
		if len(options.Metadata) > 0 {
			metadataJSON, err := json.Marshal(options.Metadata)
			if err != nil {
				pipeWriter.CloseWithError(fmt.Errorf("failed to marshal metadata: %w", err))
				return
			}
			if err := multipartWriter.WriteField("metadata", string(metadataJSON)); err != nil {
				pipeWriter.CloseWithError(fmt.Errorf("failed to write metadata: %w", err))
				return
			}
		}

		// Add processing options as JSON
		if options.ProcessingOptions != nil {
			processingJSON, err := json.Marshal(options.ProcessingOptions)
			if err != nil {
				pipeWriter.CloseWithError(fmt.Errorf("failed to marshal processing options: %w", err))
				return
			}
			if err := multipartWriter.WriteField("processing_options", string(processingJSON)); err != nil {
				pipeWriter.CloseWithError(fmt.Errorf("failed to write processing options: %w", err))
				return
			}
		}
	}()

	// Make request
	headers := map[string]string{
		"Content-Type": multipartWriter.FormDataContentType(),
	}

	resp, err := c.makeRequest(ctx, "POST", "/api/v1/upload", pipeReader, headers)
	if err != nil {
		return nil, fmt.Errorf("upload request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, c.handleErrorResponse(resp)
	}

	var uploadResp UploadResponse
	if err := json.NewDecoder(resp.Body).Decode(&uploadResp); err != nil {
		return nil, fmt.Errorf("failed to decode upload response: %w", err)
	}

	return &uploadResp, nil
}

// GetVideo retrieves video information by ID
func (c *Client) GetVideo(ctx context.Context, videoID string) (*VideoAsset, error) {
	endpoint := fmt.Sprintf("/api/v1/videos/%s", videoID)

	resp, err := c.makeRequest(ctx, "GET", endpoint, nil, nil)
	if err != nil {
		return nil, fmt.Errorf("get video request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("video not found: %s", videoID)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, c.handleErrorResponse(resp)
	}

	var video VideoAsset
	if err := json.NewDecoder(resp.Body).Decode(&video); err != nil {
		return nil, fmt.Errorf("failed to decode video response: %w", err)
	}

	return &video, nil
}

// ListVideos retrieves a list of videos with optional filtering
func (c *Client) ListVideos(ctx context.Context, options *VideoListOptions) (*VideoListResponse, error) {
	if options == nil {
		options = &VideoListOptions{}
	}

	// Build query parameters
	params := url.Values{}
	if options.Page > 0 {
		params.Set("page", strconv.Itoa(options.Page))
	}
	if options.PerPage > 0 {
		params.Set("per_page", strconv.Itoa(options.PerPage))
	}
	if options.Status != "" {
		params.Set("status", string(options.Status))
	}
	if options.Sort != "" {
		params.Set("sort", options.Sort)
	}

	endpoint := "/api/v1/videos"
	if len(params) > 0 {
		endpoint += "?" + params.Encode()
	}

	resp, err := c.makeRequest(ctx, "GET", endpoint, nil, nil)
	if err != nil {
		return nil, fmt.Errorf("list videos request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, c.handleErrorResponse(resp)
	}

	var listResp VideoListResponse
	if err := json.NewDecoder(resp.Body).Decode(&listResp); err != nil {
		return nil, fmt.Errorf("failed to decode list response: %w", err)
	}

	return &listResp, nil
}

// WaitForProcessing waits for a video to finish processing
func (c *Client) WaitForProcessing(ctx context.Context, videoID string, timeout time.Duration) (*VideoAsset, error) {
	if timeout == 0 {
		timeout = 10 * time.Minute // Default timeout
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("timeout waiting for video processing: %w", ctx.Err())
		case <-ticker.C:
			video, err := c.GetVideo(ctx, videoID)
			if err != nil {
				return nil, fmt.Errorf("failed to check video status: %w", err)
			}

			switch video.Status {
			case VideoStatusReady:
				return video, nil
			case VideoStatusFailed:
				return video, fmt.Errorf("video processing failed: %s", video.ErrorMessage)
			case VideoStatusDeleted:
				return video, fmt.Errorf("video was deleted")
			}
			// Continue waiting for processing/uploading status
		}
	}
}

// DeleteVideo deletes a video by ID
func (c *Client) DeleteVideo(ctx context.Context, videoID string) error {
	endpoint := fmt.Sprintf("/api/v1/videos/%s", videoID)

	resp, err := c.makeRequest(ctx, "DELETE", endpoint, nil, nil)
	if err != nil {
		return fmt.Errorf("delete video request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("video not found: %s", videoID)
	}

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent {
		return c.handleErrorResponse(resp)
	}

	return nil
}

// GetStreamingURL generates a streaming URL for a video
func (c *Client) GetStreamingURL(ctx context.Context, videoID string, options *StreamingURLOptions) (*StreamingURLResponse, error) {
	video, err := c.GetVideo(ctx, videoID)
	if err != nil {
		return nil, fmt.Errorf("failed to get video: %w", err)
	}

	if video.Status != VideoStatusReady {
		return nil, fmt.Errorf("video is not ready for streaming (status: %s)", video.Status)
	}

	if video.HLSURL == "" {
		return nil, fmt.Errorf("video does not have an HLS URL")
	}

	// For now, return the direct HLS URL
	// In a production system, you might want to generate signed URLs with expiration
	response := &StreamingURLResponse{
		HLSURL: video.HLSURL,
	}

	if options != nil && options.ExpiresAt != nil {
		response.ExpiresAt = *options.ExpiresAt
	}

	return response, nil
}

// handleErrorResponse processes error responses from the API
func (c *Client) handleErrorResponse(resp *http.Response) error {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("HTTP %d: failed to read error response", resp.StatusCode)
	}

	var errorResp ErrorResponse
	if err := json.Unmarshal(body, &errorResp); err != nil {
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	return fmt.Errorf("HTTP %d: %w", resp.StatusCode, errorResp)
}
