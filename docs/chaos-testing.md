# Chaos Testing Report

> Chaos engineering = deliberately breaking the system to verify it recovers correctly.
> Each scenario below documents: what was done, what was observed, what it proves.

---

## Setup

Load testing tool: **k6**
Monitoring: **Grafana** (screenshots attached per scenario)
Environment: **Kubernetes on AWS EC2**

---

## Scenario 1: Normal Load Baseline

**What:** 10 requests/second sustained for 5 minutes.

**Command:**
```bash
k6 run --vus 10 --duration 5m scripts/load-test.js
```

**Observed:**
> _[Fill in after running — include Grafana screenshot]_
- P95 latency: __ms
- Error rate: __%
- Pod count: __
- CPU usage: __%

**What it proves:** The system handles baseline production load within SLO targets.

---

## Scenario 2: Traffic Spike + HPA Scaling

**What:** Ramp from 10 to 200 requests/second over 2 minutes, hold for 3 minutes.

**Command:**
```bash
k6 run scripts/spike-test.js
```

**Observed:**
> _[Fill in after running — include Grafana screenshot showing pod count increase]_
- Time to first scale event: __s
- Max pod count reached: __
- P95 latency during spike: __ms
- Error rate during spike: __%

**What it proves:** HPA detects CPU pressure and scales pods automatically. The system remains available under 20x load.

---

## Scenario 3: Pod Kill (Self-Healing)

**What:** Delete a FastAPI pod while load test is running at 50 req/sec.

**Commands:**
```bash
# Terminal 1 — run load test
k6 run --vus 50 --duration 3m scripts/load-test.js

# Terminal 2 — kill a pod mid-test
kubectl delete pod $(kubectl get pods -l app=fastapi -o jsonpath='{.items[0].metadata.name}')
```

**Observed:**
> _[Fill in after running — include Grafana screenshot showing error rate spike (if any) and recovery]_
- Errors during pod kill: __
- Time to replacement pod Ready: __s
- Total downtime: __s

**What it proves:** K8s detects the dead pod and schedules a replacement. The Service routes traffic to healthy pods only. With 2+ replicas, downtime is zero or near-zero.

---

## Scenario 4: Database Outage

**What:** Block the RDS security group to simulate a complete database failure.

**How:**
```bash
# In AWS console or CLI — remove the inbound rule allowing EC2 → RDS on port 5432
aws ec2 revoke-security-group-ingress \
  --group-id <rds-sg-id> \
  --protocol tcp \
  --port 5432 \
  --source-group <ec2-sg-id>
```

**Observed:**
> _[Fill in after running — include Grafana screenshot showing error rate spike]_
- FastAPI error response returned: `HTTP __ — ___`
- Error rate: __%
- What happened to in-flight Celery tasks: ___

**Restore:**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id <rds-sg-id> \
  --protocol tcp \
  --port 5432 \
  --source-group <ec2-sg-id>
```

- Recovery time after restore: __s

**What it proves:** FastAPI returns a graceful error (not a crash). After DB is restored, system recovers automatically without pod restarts.

---

## Scenario 5: CPU Stress + Resource Limits

**What:** Add a CPU-intensive operation to the Celery task (e.g., SHA-256 hashing in a loop for 500ms per task). Run spike load.

**Observed:**
> _[Fill in after running — include Grafana screenshot showing CPU usage and HPA scaling]_
- CPU usage per worker pod: __%
- Time until HPA triggered scale-out: __s
- Worker pods scaled from __ to __
- Did any pod hit the CPU limit? (yes/no)
- What happened when CPU limit was hit: ___

**What it proves:** CPU limits prevent one pod from starving others. HPA scales workers to distribute the CPU load.

---

## Summary Table

| Scenario | SLO Met? | Max Error Rate | Recovery Time |
|---|---|---|---|
| Normal baseline | | | — |
| Traffic spike | | | — |
| Pod kill | | | |
| DB outage | | | |
| CPU stress | | | |

---

## Lessons Learned

> _[Fill in after completing all scenarios]_
