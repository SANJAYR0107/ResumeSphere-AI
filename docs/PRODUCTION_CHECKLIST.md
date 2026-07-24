# v15.0.0 Production Deployment Checklist

Prior to approving the final merge into `main` and deploying to the production Kubernetes cluster, the Ops team must verify the following:

## Security (Module P3)
- [ ] **Secrets Management**: Verify `.env` is NOT checked into source control. All secrets (JWT Keys, HuggingFace Tokens, DB URIs) are stored in K8s Secrets or AWS Secrets Manager.
- [ ] **Middlewares Active**: Verified `SecurityHeadersMiddleware` (XSS, HSTS) is loaded in `main.py`.
- [ ] **CORS Restricted**: The `CORS_ORIGINS` environment variable is explicitly set to production domains (no `*`).
- [ ] **Rate Limiting**: `RATE_LIMIT_ENABLED` is true and pointing to the production Redis cluster.

## Performance & Observability (Module P4 & P6)
- [ ] **Prometheus Exporter**: Verified `/metrics` is accessible to the internal K8s Prometheus scraper.
- [ ] **Liveness Probes**: K8s `deployment.yaml` points correctly to `/api/health/liveness`.
- [ ] **Logging**: Structured JSON logging is active and flowing into Elasticsearch/Datadog.
- [ ] **Database Indexes**: Required indexes (e.g., on `tenant_id`, `email`) are applied in PostgreSQL to prevent full table scans.

## High Availability
- [ ] **Replica Count**: K8s deployment specifies a minimum of 3 replicas.
- [ ] **Resources**: CPU (`500m`) and Memory (`1Gi`) limits are strictly defined to prevent OOM kills on heavy AI model inferences.

## Release Readiness
- [ ] **Version Bump**: `API_VERSION` in `config.py` is exactly `"15.0.0"`.
- [ ] **Tests Pass**: GitHub Actions CI pipeline is fully green.
- [ ] **DR Plan**: `DISASTER_RECOVERY.md` has been read and approved by the DevOps lead.
