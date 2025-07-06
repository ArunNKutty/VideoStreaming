package hlsserver

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestNewClient(t *testing.T) {
	tests := []struct {
		name    string
		config  Config
		wantErr bool
	}{
		{
			name: "valid config",
			config: Config{
				BaseURL:  "https://api.example.com",
				ClientID: "test-client",
				Secret:   "test-secret",
				Timeout:  30 * time.Second,
			},
			wantErr: false,
		},
		{
			name: "missing base URL",
			config: Config{
				ClientID: "test-client",
				Secret:   "test-secret",
			},
			wantErr: true,
		},
		{
			name: "missing client ID",
			config: Config{
				BaseURL: "https://api.example.com",
				Secret:  "test-secret",
			},
			wantErr: true,
		},
		{
			name: "missing secret",
			config: Config{
				BaseURL:  "https://api.example.com",
				ClientID: "test-client",
			},
			wantErr: true,
		},
		{
			name: "invalid base URL",
			config: Config{
				BaseURL:  "not-a-valid-url",
				ClientID: "test-client",
				Secret:   "test-secret",
			},
			wantErr: true, // Authentication will fail with invalid URL
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Mock server for authentication
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/api/v1/auth/token" {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusOK)
					w.Write([]byte(`{"access_token":"test-token","token_type":"bearer","expires_in":3600}`))
					return
				}
				w.WriteHeader(http.StatusNotFound)
			}))
			defer server.Close()

			// Use test server URL if BaseURL is valid
			if tt.config.BaseURL != "" && tt.config.BaseURL != "not-a-valid-url" {
				tt.config.BaseURL = server.URL
			}

			client, err := NewClient(tt.config)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewClient() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr && client == nil {
				t.Error("NewClient() returned nil client without error")
			}
		})
	}
}

func TestClient_authenticate(t *testing.T) {
	tests := []struct {
		name           string
		serverResponse string
		statusCode     int
		wantErr        bool
	}{
		{
			name:           "successful authentication",
			serverResponse: `{"access_token":"test-token","token_type":"bearer","expires_in":3600}`,
			statusCode:     http.StatusOK,
			wantErr:        false,
		},
		{
			name:           "invalid credentials",
			serverResponse: `{"error":"invalid_client","error_description":"Invalid client credentials"}`,
			statusCode:     http.StatusUnauthorized,
			wantErr:        true,
		},
		{
			name:           "server error",
			serverResponse: `{"error":"server_error"}`,
			statusCode:     http.StatusInternalServerError,
			wantErr:        true,
		},
		{
			name:           "invalid JSON response",
			serverResponse: `invalid json`,
			statusCode:     http.StatusOK,
			wantErr:        true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/api/v1/auth/token" {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(tt.statusCode)
					w.Write([]byte(tt.serverResponse))
					return
				}
				w.WriteHeader(http.StatusNotFound)
			}))
			defer server.Close()

			client := &Client{
				baseURL:    server.URL,
				httpClient: &http.Client{Timeout: 10 * time.Second},
				clientID:   "test-client",
				secret:     "test-secret",
			}

			err := client.authenticate(context.Background())
			if (err != nil) != tt.wantErr {
				t.Errorf("authenticate() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if client.token == "" {
					t.Error("authenticate() did not set token")
				}
				if client.tokenExp.IsZero() {
					t.Error("authenticate() did not set token expiration")
				}
			}
		})
	}
}

func TestClient_ensureAuthenticated(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/auth/token" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"access_token":"new-token","token_type":"bearer","expires_in":3600}`))
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	client := &Client{
		baseURL:    server.URL,
		httpClient: &http.Client{Timeout: 10 * time.Second},
		clientID:   "test-client",
		secret:     "test-secret",
	}

	t.Run("no token", func(t *testing.T) {
		err := client.ensureAuthenticated(context.Background())
		if err != nil {
			t.Errorf("ensureAuthenticated() error = %v", err)
		}
		if client.token == "" {
			t.Error("ensureAuthenticated() did not set token")
		}
	})

	t.Run("valid token", func(t *testing.T) {
		client.token = "existing-token"
		client.tokenExp = time.Now().Add(1 * time.Hour)

		oldToken := client.token
		err := client.ensureAuthenticated(context.Background())
		if err != nil {
			t.Errorf("ensureAuthenticated() error = %v", err)
		}
		if client.token != oldToken {
			t.Error("ensureAuthenticated() should not refresh valid token")
		}
	})

	t.Run("expired token", func(t *testing.T) {
		client.token = "expired-token"
		client.tokenExp = time.Now().Add(-1 * time.Hour)

		err := client.ensureAuthenticated(context.Background())
		if err != nil {
			t.Errorf("ensureAuthenticated() error = %v", err)
		}
		if client.token == "expired-token" {
			t.Error("ensureAuthenticated() should refresh expired token")
		}
	})
}
