import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m",  target: 10  },
    { duration: "2m",  target: 100 },
    { duration: "3m",  target: 200 },
    { duration: "1m",  target: 10  },
    { duration: "30s", target: 0   },
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:80";

export default function () {
  const res = http.post(
    `${BASE_URL}/events`,
    JSON.stringify({ type: "spike.test", source: "k6", payload: { vu: __VU } }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(res, { "202": (r) => r.status === 202 });
  sleep(0.1);
}
