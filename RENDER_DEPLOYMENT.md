# 🚀 Render Cloud Deployment Guide

This guide explains how to deploy the HLS Video Streaming Platform on Render with persistent storage.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **AWS S3 Credentials**: For video storage (optional but recommended)

## 🔧 Deployment Steps

### **Method 1: Using render.yaml (Recommended)**

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**:
   - In Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add these **secret** environment variables:
     ```
     AWS_ACCESS_KEY_ID=your_access_key_here
     AWS_SECRET_ACCESS_KEY=your_secret_key_here
     ```

### **Method 2: Manual Web Service Creation**

1. **Create Web Service**:
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   ```
   Name: hls-video-server
   Runtime: Docker
   Dockerfile Path: ./Dockerfile
   Build Command: (leave empty)
   Start Command: (leave empty - uses Dockerfile CMD)
   ```

3. **Add Persistent Disk**:
   - In service settings, go to "Disks" tab
   - Click "Add Disk"
   - Configure:
     ```
     Name: hls-storage
     Mount Path: /opt/render/project/src/persistent
     Size: 10 GB (or more based on needs)
     ```

4. **Set Environment Variables**:
   ```
   AWS_ACCESS_KEY_ID=your_access_key (secret)
   AWS_SECRET_ACCESS_KEY=your_secret_key (secret)
   AWS_REGION=us-east-2
   S3_BUCKET_NAME=cogito-videos
   DEBUG=false
   PERSISTENT_HLS_DIR=/opt/render/project/src/persistent/hls
   PERSISTENT_VIDEOS_DIR=/opt/render/project/src/persistent/videos
   ```

## 💾 **Persistent Storage Configuration**

### **Render Disk Specifications**:
- **Mount Path**: `/opt/render/project/src/persistent`
- **Directory Structure**:
  ```
  /opt/render/project/src/persistent/
  ├── hls/           # HLS files (playlists and segments)
  │   └── {video_id}/
  │       ├── index.m3u8
  │       └── *.ts
  └── videos/        # Original video files
  ```

### **Storage Tiers**:
- **Starter Plan**: Up to 1GB free persistent storage
- **Standard Plan**: Up to 10GB persistent storage
- **Pro Plan**: Up to 100GB persistent storage

## 🌐 **Access Your Deployed App**

After deployment, your app will be available at:
```
https://your-app-name.onrender.com
```

### **API Endpoints**:
```
POST https://your-app-name.onrender.com/api/v1/upload
GET  https://your-app-name.onrender.com/api/v1/videos/{id}
GET  https://your-app-name.onrender.com/api/v1/videos/{id}/hls/index.m3u8
GET  https://your-app-name.onrender.com/api/v1/videos/{id}/player
```

## 🧪 **Testing Deployment**

1. **Health Check**:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

2. **Upload Test Video**:
   ```bash
   curl -X POST "https://your-app-name.onrender.com/api/v1/upload" \
     -F "file=@test_video.mp4"
   ```

3. **Verify Persistent Storage**:
   - Upload a video
   - Check if files persist after service restart
   - Files should be in `/opt/render/project/src/persistent/hls/`

## ⚙️ **Configuration Options**

### **Disk Size Recommendations**:
- **Small Projects**: 5-10 GB
- **Medium Projects**: 20-50 GB  
- **Large Projects**: 100+ GB

### **Instance Types**:
- **Starter**: 0.5 CPU, 512 MB RAM (good for testing)
- **Standard**: 1 CPU, 2 GB RAM (recommended for production)
- **Pro**: 2+ CPU, 4+ GB RAM (high traffic)

## 🔒 **Security Best Practices**

1. **Environment Variables**:
   - Mark AWS credentials as "secret"
   - Use strong S3 bucket policies
   - Enable CORS only for your domains

2. **HTTPS**:
   - Render provides free SSL certificates
   - All traffic is automatically HTTPS

3. **Access Control**:
   - Consider adding authentication for upload endpoints
   - Implement rate limiting for production

## 🚨 **Troubleshooting**

### **Common Issues**:

1. **Build Failures**:
   ```bash
   # Check build logs in Render dashboard
   # Ensure all dependencies are in requirements.txt
   ```

2. **Persistent Storage Not Working**:
   ```bash
   # Verify mount path: /opt/render/project/src/persistent
   # Check environment variables are set correctly
   # Ensure disk is properly attached to service
   ```

3. **FFmpeg Issues**:
   ```bash
   # FFmpeg is installed in Dockerfile
   # Check if apt-get update/install completed successfully
   ```

4. **Port Issues**:
   ```bash
   # Render automatically sets PORT environment variable
   # Dockerfile uses ${PORT:-8080} for flexibility
   ```

## 📊 **Monitoring**

### **Render Dashboard**:
- **Metrics**: CPU, Memory, Disk usage
- **Logs**: Real-time application logs
- **Events**: Deployment history

### **Health Checks**:
- Render automatically monitors `/health` endpoint
- Service restarts if health checks fail

## 💰 **Cost Estimation**

### **Monthly Costs** (approximate):
- **Starter + 10GB Disk**: ~$7-10/month
- **Standard + 20GB Disk**: ~$25-30/month
- **Pro + 50GB Disk**: ~$85-100/month

### **Cost Optimization**:
- Use S3 for primary storage (cheaper for large files)
- Keep only active/recent files on persistent disk
- Implement cleanup jobs for old files

## 🔄 **Auto-Deployment**

With `render.yaml`, your app will automatically redeploy when you push to GitHub:

```bash
git add .
git commit -m "Update video processing"
git push origin main
# Render automatically deploys the changes
```

## 📈 **Scaling Considerations**

1. **Horizontal Scaling**: 
   - Use multiple Render services behind a load balancer
   - Share persistent storage via network file systems

2. **Database**: 
   - Consider PostgreSQL for video metadata
   - Use Render's managed PostgreSQL service

3. **CDN**: 
   - Use CloudFlare or AWS CloudFront
   - Cache HLS files for better performance

Your HLS Video Platform is now ready for production deployment on Render! 🎉
