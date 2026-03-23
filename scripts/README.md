# Load Test Scripts (k6)

Install k6: `sudo snap install k6`

| Script | Purpose | Duration |
|---|---|---|
| `load-test.js` | Normal baseline (10 VUs) | 5 min |
| `spike-test.js` | Spike to 200 VUs — triggers HPA | ~7 min |
| `chaos-verify.js` | Continuous health checks | 10 min |

```bash
k6 run scripts/load-test.js
k6 run -e BASE_URL=http://<ec2-ip> scripts/spike-test.js
```
