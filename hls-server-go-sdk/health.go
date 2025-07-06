package hlsserver

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// HealthCheck performs a health check on the HLS server
func (c *Client) HealthCheck(ctx context.Context) (*HealthResponse, error) {
	resp, err := c.makeRequest(ctx, "GET", "/api/v1/health", nil, nil)
	if err != nil {
		return nil, fmt.Errorf("health check request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, c.handleErrorResponse(resp)
	}

	var healthResp HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&healthResp); err != nil {
		return nil, fmt.Errorf("failed to decode health response: %w", err)
	}

	return &healthResp, nil
}

// Ping performs a simple connectivity test
func (c *Client) Ping(ctx context.Context) error {
	_, err := c.HealthCheck(ctx)
	return err
}
