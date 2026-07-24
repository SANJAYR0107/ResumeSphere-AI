# Disaster Recovery & Rollback Plan (v15.0.0)

## Objective
Minimize downtime and data loss in the event of a catastrophic failure (database corruption, cluster crash, malicious intrusion).

## Recovery Time Objectives (RTO / RPO)
- **RTO (Recovery Time Objective)**: 15 Minutes
- **RPO (Recovery Point Objective)**: 1 Hour (Incremental), 24 Hours (Full)

---

## 1. Database Backup Strategy (PostgreSQL)

We utilize AWS RDS / Managed PostgreSQL which handles automated daily snapshots. However, for logical backups:
- **Full Backups**: `pg_dump` executed daily at 03:00 UTC and pushed to S3.
- **WAL Archiving**: Continuous Write-Ahead Log archiving to S3 for point-in-time recovery (PITR).

### Restoring from Backup
```bash
# 1. Spin up a fresh database instance
# 2. Download latest dump from S3
aws s3 cp s3://resumesphere-backups/db-prod-latest.sql .

# 3. Restore data
psql -h <new_db_host> -U admin resumesphere < db-prod-latest.sql
```

---

## 2. Kubernetes Cluster Recovery (EKS/GKE)

If the entire Kubernetes cluster becomes unavailable:
1. Trigger the Infrastructure-as-Code (Terraform) pipeline to spin up a new cluster in an alternative availability zone.
2. Update the `ConfigMap` with the new database URI.
3. Re-apply manifests:
```bash
kubectl apply -f kubernetes/deployment.yaml
```
4. Update DNS records (Route53/Cloudflare) to point to the new Ingress controller load balancer.

---

## 3. Rollback Strategy (Application Code)

If a deployment introduces critical bugs (e.g. Memory Leak in AI Parser):
1. **Identify previous stable tag** in GitHub Actions (e.g., `v14.0.0`).
2. **Revert Kubernetes Deployment**:
```bash
kubectl rollout undo deployment/resumesphere-backend
```
3. Monitor the `/metrics` endpoint to ensure HTTP 500s drop to 0 and the AI Inference latency stabilizes.
