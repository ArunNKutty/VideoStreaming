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
	// Initialize client with custom HTTP client
	client, err := hlsserver.NewClient(hlsserver.Config{
		BaseURL:  os.Getenv("HLS_SERVER_URL"),
		ClientID: os.Getenv("HLS_CLIENT_ID"),
		Secret:   os.Getenv("HLS_CLIENT_SECRET"),
		Timeout:  60 * time.Second,
	})
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	ctx := context.Background()

	// Advanced upload with custom options
	videoPath := "sample.mp4"
	if len(os.Args) > 1 {
		videoPath = os.Args[1]
	}

	fmt.Printf("📤 Uploading video with advanced options: %s\n", videoPath)
	
	uploadResp, err := client.UploadVideo(ctx, videoPath, &hlsserver.UploadOptions{
		Filename:    "my-custom-video.mp4",
		CallbackURL: "https://myapp.com/webhook/video-processed",
		Metadata: map[string]string{
			"title":       "My Custom Video",
			"description": "Uploaded via Go SDK",
			"category":    "demo",
			"user_id":     "12345",
		},
		ProcessingOptions: &hlsserver.ProcessingOptions{
			SegmentDuration: 6, // 6-second segments
			PlaylistType:    "vod",
			Quality: &hlsserver.QualitySettings{
				VideoBitrate: 2000, // 2 Mbps
				AudioBitrate: 128,  // 128 kbps
				Resolution:   "1280x720",
				FrameRate:    30.0,
			},
		},
	})
	if err != nil {
		log.Fatalf("Upload failed: %v", err)
	}

	fmt.Printf("✅ Upload successful! Video ID: %s\n", uploadResp.VideoID)

	// Monitor processing with custom polling
	fmt.Println("⏳ Monitoring processing progress...")
	videoID := uploadResp.VideoID
	
	for {
		video, err := client.GetVideo(ctx, videoID)
		if err != nil {
			log.Fatalf("Failed to get video status: %v", err)
		}

		fmt.Printf("📊 Status: %s", video.Status)
		if video.Info != nil && video.Info.Duration > 0 {
			fmt.Printf(" | Duration: %ds", video.Info.Duration)
		}
		fmt.Println()

		switch video.Status {
		case hlsserver.VideoStatusReady:
			fmt.Printf("🎉 Processing complete!\n")
			fmt.Printf("🎬 HLS URL: %s\n", video.HLSURL)
			
			if video.Info != nil {
				fmt.Printf("📹 Video Info:\n")
				fmt.Printf("  - Resolution: %dx%d\n", video.Info.Width, video.Info.Height)
				fmt.Printf("  - Duration: %ds\n", video.Info.Duration)
				fmt.Printf("  - Bitrate: %d kbps\n", video.Info.Bitrate)
				fmt.Printf("  - Codec: %s\n", video.Info.Codec)
				fmt.Printf("  - FPS: %.2f\n", video.Info.FPS)
				fmt.Printf("  - File Size: %d bytes\n", video.Info.FileSize)
			}
			
			// Generate streaming URL with expiration
			expiresAt := time.Now().Add(24 * time.Hour)
			streamingURL, err := client.GetStreamingURL(ctx, videoID, &hlsserver.StreamingURLOptions{
				ExpiresAt: &expiresAt,
			})
			if err != nil {
				log.Printf("Failed to get streaming URL: %v", err)
			} else {
				fmt.Printf("🔗 Streaming URL (expires %s): %s\n", 
					streamingURL.ExpiresAt.Format("2006-01-02 15:04:05"), 
					streamingURL.HLSURL)
			}
			return
			
		case hlsserver.VideoStatusFailed:
			log.Fatalf("❌ Processing failed: %s", video.ErrorMessage)
			
		case hlsserver.VideoStatusDeleted:
			log.Fatalf("❌ Video was deleted")
		}

		// Wait before next check
		time.Sleep(3 * time.Second)
	}
}
