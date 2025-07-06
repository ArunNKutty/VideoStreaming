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
	// Initialize the client
	client, err := hlsserver.NewClient(hlsserver.Config{
		BaseURL:  "http://localhost:8080", // Replace with your HLS server URL
		ClientID: os.Getenv("HLS_CLIENT_ID"),
		Secret:   os.Getenv("HLS_CLIENT_SECRET"),
		Timeout:  30 * time.Second,
	})
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	ctx := context.Background()

	// Health check
	fmt.Println("🏥 Performing health check...")
	health, err := client.HealthCheck(ctx)
	if err != nil {
		log.Fatalf("Health check failed: %v", err)
	}
	fmt.Printf("✅ Server is healthy: %s (version: %s)\n", health.Status, health.Version)

	// Upload a video
	videoPath := "sample.mp4" // Replace with your video file path
	if len(os.Args) > 1 {
		videoPath = os.Args[1]
	}

	fmt.Printf("📤 Uploading video: %s\n", videoPath)
	uploadResp, err := client.UploadVideo(ctx, videoPath, &hlsserver.UploadOptions{
		ProcessingOptions: &hlsserver.ProcessingOptions{
			SegmentDuration: 10,
			PlaylistType:    "vod",
		},
	})
	if err != nil {
		log.Fatalf("Upload failed: %v", err)
	}

	fmt.Printf("✅ Upload successful! Video ID: %s\n", uploadResp.VideoID)
	fmt.Printf("📊 Status: %s\n", uploadResp.Asset.Status)

	// Wait for processing to complete
	fmt.Println("⏳ Waiting for processing to complete...")
	video, err := client.WaitForProcessing(ctx, uploadResp.VideoID, 5*time.Minute)
	if err != nil {
		log.Fatalf("Processing failed: %v", err)
	}

	fmt.Printf("🎉 Processing complete! Status: %s\n", video.Status)
	if video.HLSURL != "" {
		fmt.Printf("🎬 HLS URL: %s\n", video.HLSURL)
	}

	// Get streaming URL
	streamingURL, err := client.GetStreamingURL(ctx, video.ID, nil)
	if err != nil {
		log.Printf("Failed to get streaming URL: %v", err)
	} else {
		fmt.Printf("🔗 Streaming URL: %s\n", streamingURL.HLSURL)
	}

	// List videos
	fmt.Println("\n📋 Listing recent videos...")
	videos, err := client.ListVideos(ctx, &hlsserver.VideoListOptions{
		Page:    1,
		PerPage: 5,
		Sort:    "-created_at",
	})
	if err != nil {
		log.Printf("Failed to list videos: %v", err)
	} else {
		fmt.Printf("Found %d videos (total: %d)\n", len(videos.Videos), videos.Total)
		for i, v := range videos.Videos {
			fmt.Printf("  %d. %s (%s) - %s\n", i+1, v.Filename, v.ID, v.Status)
		}
	}
}
