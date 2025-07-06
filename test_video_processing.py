#!/usr/bin/env python3
"""
Test script to monitor video processing status
"""
import time
import requests
import json

def check_video_status(video_id, base_url="http://localhost:8080"):
    """Check video processing status"""
    try:
        response = requests.get(f"{base_url}/api/v1/videos/{video_id}")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def monitor_video_processing(video_id, max_wait=120, check_interval=5):
    """Monitor video processing until completion or timeout"""
    print(f"🔍 Monitoring video processing for ID: {video_id}")
    print(f"⏱️  Max wait time: {max_wait}s, Check interval: {check_interval}s")
    print("-" * 60)
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_data = check_video_status(video_id)
        
        if "error" in status_data:
            print(f"❌ Error: {status_data['error']}")
            break
            
        current_status = status_data.get("status", "unknown")
        hls_url = status_data.get("hls_url")
        
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed:3d}s] Status: {current_status:<12} HLS URL: {'✅ Available' if hls_url else '⏳ Processing'}")
        
        if current_status == "ready" and hls_url:
            print(f"🎉 Video processing completed!")
            print(f"🔗 HLS URL: {hls_url}")
            return status_data
            
        if current_status == "failed":
            print(f"💥 Video processing failed!")
            error_msg = status_data.get("error_message", "Unknown error")
            print(f"❌ Error: {error_msg}")
            return status_data
            
        time.sleep(check_interval)
    
    print(f"⏰ Timeout reached after {max_wait}s")
    return check_video_status(video_id)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_video_processing.py <video_id>")
        print("Example: python test_video_processing.py 11fc803f-78d1-47c1-b12a-373659f5373b")
        sys.exit(1)
    
    video_id = sys.argv[1]
    final_status = monitor_video_processing(video_id)
    
    print("\n" + "="*60)
    print("📊 Final Status:")
    print(json.dumps(final_status, indent=2))
