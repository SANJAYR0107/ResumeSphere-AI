# 🐳 Module A1 — Docker Prerequisites & Environment Setup Guide

## Overview
This document defines the Docker setup and environment prerequisites required to build, run, and deploy **ResumeSphere AI** in containerized environments (Docker Desktop, Podman, or Cloud Container Runtimes).

---

## 📋 System Prerequisites & Verification

### 1. Docker Runtime Requirements
- **Docker Engine**: Version `20.10.0+` or higher
- **Docker Compose**: Plugin version `v2.0.0+` or higher
- **Docker Desktop** (Windows / macOS): Version `4.15.0+` (Ensure WSL 2 backend is enabled on Windows)
- **System Memory**: Minimum 2 GB RAM available for the Docker daemon (4 GB recommended for PyTorch/Sentence-Transformers model loading).
- **Disk Space**: Minimum 3 GB free disk space for image layer caching and dependencies.

### 2. Python Runtime Compatibility
- **Target Python Version**: `Python 3.11.x` (slim-bookworm base image)
- **Core Native Libraries**:
  - `PyMuPDF` (fitz): Requires standard C standard library (`libc6`).
  - `torch` (PyTorch CPU): Optimized CPU inference without CUDA bloat.
  - `sentence-transformers`: Machine learning model cached in `/app/.cache/huggingface`.

---

## 🛠️ Verification Steps

Verify local Docker installation and daemon status:

```bash
# Verify Docker Client & Server Version
docker version

# Verify Docker Compose Version
docker compose version

# Verify Docker System Resource Limits
docker info
```

---

## 📁 Verified Project Directory Structure

```text
AI-Resume-Analyzer/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── config.py
│   │   └── ...
│   ├── uploads/
│   ├── main.py
│   └── resume_pipeline.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── datasets/
│   └── skills.csv
├── docs/
│   ├── DOCKER_SETUP.md
│   └── DEPLOYMENT.md
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── requirements.txt
```
