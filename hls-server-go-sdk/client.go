// Package hlsserver provides a Go SDK for interacting with the HLS Video Streaming Server API.
package hlsserver

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// Client represents the HLS Server API client
type Client struct {
	baseURL    string
	httpClient *http.Client
	clientID   string
	secret     string
	token      string
	tokenExp   time.Time
}

// Config holds the configuration for the HLS Server client
type Config struct {
	BaseURL    string        // HLS Server base URL (e.g., "https://api.hlsserver.com")
	ClientID   string        // Client ID for authentication
	Secret     string        // Client secret for authentication
	Timeout    time.Duration // HTTP client timeout (default: 30s)
	HTTPClient *http.Client  // Custom HTTP client (optional)
}

// NewClient creates a new HLS Server API client
func NewClient(config Config) (*Client, error) {
	if config.BaseURL == "" {
		return nil, fmt.Errorf("base URL is required")
	}
	if config.ClientID == "" {
		return nil, fmt.Errorf("client ID is required")
	}
	if config.Secret == "" {
		return nil, fmt.Errorf("secret is required")
	}

	// Set default timeout
	if config.Timeout == 0 {
		config.Timeout = 30 * time.Second
	}

	// Use provided HTTP client or create default
	httpClient := config.HTTPClient
	if httpClient == nil {
		httpClient = &http.Client{
			Timeout: config.Timeout,
		}
	}

	// Parse and validate base URL
	baseURL, err := url.Parse(config.BaseURL)
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	client := &Client{
		baseURL:    baseURL.String(),
		httpClient: httpClient,
		clientID:   config.ClientID,
		secret:     config.Secret,
	}

	// Authenticate on initialization
	if err := client.authenticate(context.Background()); err != nil {
		return nil, fmt.Errorf("authentication failed: %w", err)
	}

	return client, nil
}

// authenticate performs client authentication and obtains an access token
func (c *Client) authenticate(ctx context.Context) error {
	authURL := c.baseURL + "/api/v1/auth/token"

	payload := map[string]string{
		"client_id":     c.clientID,
		"client_secret": c.secret,
		"grant_type":    "client_credentials",
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal auth payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", authURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create auth request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("auth request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("authentication failed with status %d: %s", resp.StatusCode, string(body))
	}

	var authResp AuthResponse
	if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
		return fmt.Errorf("failed to decode auth response: %w", err)
	}

	c.token = authResp.AccessToken
	c.tokenExp = time.Now().Add(time.Duration(authResp.ExpiresIn) * time.Second)

	return nil
}

// ensureAuthenticated checks if the token is valid and refreshes if needed
func (c *Client) ensureAuthenticated(ctx context.Context) error {
	if c.token == "" || time.Now().After(c.tokenExp.Add(-5*time.Minute)) {
		return c.authenticate(ctx)
	}
	return nil
}

// makeRequest performs an authenticated HTTP request
func (c *Client) makeRequest(ctx context.Context, method, endpoint string, body io.Reader, headers map[string]string) (*http.Response, error) {
	if err := c.ensureAuthenticated(ctx); err != nil {
		return nil, fmt.Errorf("authentication failed: %w", err)
	}

	url := c.baseURL + endpoint
	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set default headers
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Accept", "application/json")

	// Set custom headers
	for key, value := range headers {
		req.Header.Set(key, value)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}

	return resp, nil
}
