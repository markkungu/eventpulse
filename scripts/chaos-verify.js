import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";

const failures = new Counter("health_check_failures");

export const options = {
  vus: 1,
  duration: "10m",
  thresholds: { health_check_failures: ["count<5"] },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:80";

export default function () {
  const res = http.get(`${BASE_URL}/health`, { timeout: "3s" });
  const ok = check(res, {
    "health 200": (r) => r.status === 200,
    "status ok":  (r) => { try { return JSON.parse(r.body).status === "ok"; } catch { return false; } },
  });
  if (!ok) {
    failures.add(1);
    console.log(`FAILURE at ${new Date().toISOString()}: HTTP ${res.status}`);
  }
}
