# HLS Server Go SDK

[![Go Reference](https://pkg.go.dev/badge/github.com/ArunNKutty/hls-server-go-sdk.svg)](https://pkg.go.dev/github.com/ArunNKutty/hls-server-go-sdk)
[![Go Report Card](https://goreportcard.com/badge/github.com/ArunNKutty/hls-server-go-sdk)](https://goreportcard.com/report/github.com/ArunNKutty/hls-server-go-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Go SDK for interacting with the HLS Video Streaming Server API. This SDK provides a clean, idiomatic Go interface for uploading, processing, and streaming videos through your HLS server.

## Features

- 🔐 **Client Credentials Authentication** - Secure authentication using client ID and secret
- 📤 **Video Upload** - Upload videos from files or io.Reader with custom options
- ⏳ **Processing Monitoring** - Wait for video processing with customizable timeouts
- 🎬 **Streaming URLs** - Generate HLS streaming URLs with optional expiration
- 📋 **Video Management** - List, retrieve, and delete videos
- 🏥 **Health Checks** - Monitor server health and connectivity
- 🛡️ **Error Handling** - Comprehensive error handling with detailed messages
- 🔄 **Auto-retry** - Automatic token refresh and request retry logic

## Installation

```bash
go get github.com/ArunNKutty/hls-server-go-sdk
```

## Quick Start

### 1. Get Client Credentials

First, obtain your client ID and secret from your HLS server:

```bash
# Set environment variables
export HLS_CLIENT_ID="your-client-id"
export HLS_CLIENT_SECRET="your-client-secret"
export HLS_SERVER_URL="https://your-hls-server.com"
```

### 2. Basic Usage

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "time"

    hlsserver "github.com/ArunNKutty/hls-server-go-sdk"
)

func main() {
    // Initialize client
    client, err := hlsserver.NewClient(hlsserver.Config{
        BaseURL:  os.Getenv("HLS_SERVER_URL"),
        ClientID: os.Getenv("HLS_CLIENT_ID"),
        Secret:   os.Getenv("HLS_CLIENT_SECRET"),
        Timeout:  30 * time.Second,
    })
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Upload video
    uploadResp, err := client.UploadVideo(ctx, "video.mp4", nil)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Video uploaded! ID: %s\n", uploadResp.VideoID)

    // Wait for processing
    video, err := client.WaitForProcessing(ctx, uploadResp.VideoID, 5*time.Minute)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("HLS URL: %s\n", video.HLSURL)
}
```

## Advanced Usage

### Custom Upload Options

```go
uploadResp, err := client.UploadVideo(ctx, "video.mp4", &hlsserver.UploadOptions{
    Filename:    "my-custom-name.mp4",
    CallbackURL: "https://myapp.com/webhook",
    Metadata: map[string]string{
        "title":    "My Video",
        "category": "demo",
    },
    ProcessingOptions: &hlsserver.ProcessingOptions{
        SegmentDuration: 6,
        PlaylistType:    "vod",
        Quality: &hlsserver.QualitySettings{
            VideoBitrate: 2000,
            AudioBitrate: 128,
            Resolution:   "1280x720",
            FrameRate:    30.0,
        },
    },
})
```

### Upload from io.Reader

```go
file, err := os.Open("video.mp4")
if err != nil {
    log.Fatal(err)
}
defer file.Close()

uploadResp, err := client.UploadVideoFromReader(ctx, file, "video.mp4", nil)
```

### List Videos with Filtering

```go
videos, err := client.ListVideos(ctx, &hlsserver.VideoListOptions{
    Page:    1,
    PerPage: 10,
    Status:  hlsserver.VideoStatusReady,
    Sort:    "-created_at",
})
```

### Generate Streaming URLs

```go
expiresAt := time.Now().Add(24 * time.Hour)
streamingURL, err := client.GetStreamingURL(ctx, videoID, &hlsserver.StreamingURLOptions{
    ExpiresAt: &expiresAt,
})
```

## API Reference

### Client Configuration

```go
type Config struct {
    BaseURL    string        // HLS Server base URL
    ClientID   string        // Client ID for authentication
    Secret     string        // Client secret for authentication
    Timeout    time.Duration // HTTP client timeout (default: 30s)
    HTTPClient *http.Client  // Custom HTTP client (optional)
}
```

### Video Operations

- `UploadVideo(ctx, filePath, options)` - Upload video from file
- `UploadVideoFromReader(ctx, reader, filename, options)` - Upload from io.Reader
- `GetVideo(ctx, videoID)` - Get video information
- `ListVideos(ctx, options)` - List videos with filtering
- `WaitForProcessing(ctx, videoID, timeout)` - Wait for processing completion
- `DeleteVideo(ctx, videoID)` - Delete a video
- `GetStreamingURL(ctx, videoID, options)` - Generate streaming URL

### Health & Connectivity

- `HealthCheck(ctx)` - Get server health status
- `Ping(ctx)` - Simple connectivity test

## Error Handling

The SDK provides detailed error information:

```go
uploadResp, err := client.UploadVideo(ctx, "video.mp4", nil)
if err != nil {
    // Handle different error types
    switch {
    case strings.Contains(err.Error(), "authentication failed"):
        log.Println("Check your client credentials")
    case strings.Contains(err.Error(), "file too large"):
        log.Println("Video file exceeds size limit")
    default:
        log.Printf("Upload error: %v", err)
    }
}
```

## Examples

See the [examples](./examples) directory for complete working examples:

- [Basic Usage](./examples/basic/main.go) - Simple upload and streaming
- [Advanced Usage](./examples/advanced/main.go) - Custom options and monitoring

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://pkg.go.dev/github.com/ArunNKutty/hls-server-go-sdk)
- 🐛 [Issue Tracker](https://github.com/ArunNKutty/hls-server-go-sdk/issues)
- 💬 [Discussions](https://github.com/ArunNKutty/hls-server-go-sdk/discussions)
