# 🚀 Production Deployment Guide — ResumeSphere AI

## Overview
This guide provides step-by-step instructions for deploying **ResumeSphere AI** across major cloud platforms (Render, Railway, AWS ECS/App Runner, Docker Engine).

---

## 🛠️ Environment Variable Reference

| Variable Name | Default Value | Description |
|---|---|---|
| `APP_ENV` | `production` | Deployment stage (`production`, `staging`, `development`). |
| `PORT` | `8000` | Port for Uvicorn ASGI server. |
| `DEBUG` | `false` | Enables verbose logging and interactive debug mode. |
| `ALLOWED_ORIGINS` | `*` | Comma-separated list of permitted CORS frontend domains. |
| `MAX_UPLOAD_BYTES` | `10485760` | Max file upload limit in bytes (Default: 10MB). |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face model repository ID. |

---

## ☁️ Cloud Deployment Options

### Option 1: Render Deployment (Recommended for 1-Click)
1. Fork or push your code to GitHub.
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Blueprint**.
3. Connect your repository `ResumeSphere-AI`. Render will automatically pick up `render.yaml`.
4. Click **Apply**. Render will build the Docker container and deploy the app with automatic SSL.

### Option 2: Railway Deployment
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select `ResumeSphere-AI`. Railway will automatically read `railway.json` and `Dockerfile`.
4. Set Environment Variables (`ALLOWED_ORIGINS`, `APP_ENV=production`).
5. Deploy service.

### Option 3: Standard Docker Server Deployment
```bash
# 1. Clone repository
git clone https://github.com/SANJAYR0107/ResumeSphere-AI.git
cd ResumeSphere-AI

# 2. Build and start containers
docker compose -f docker-compose.yml up -d --build

# 3. Verify health endpoint
curl http://localhost:8000/health
```

---

## 🔍 Verification & Health Monitoring

Verify container health:
```bash
docker ps --filter "name=resumesphere_ai_app"
curl -f http://localhost:8000/health
```

Expected Output:
```json
{
  "status": "ok",
  "app": "ResumeSphere AI",
  "version": "2.0.0",
  "environment": "production",
  "uptime_seconds": 12.45,
  "model_loaded": true
}
```
