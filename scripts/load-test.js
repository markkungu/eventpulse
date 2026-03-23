import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const eventsSubmitted = new Counter("events_submitted");
const processingLatency = new Trend("processing_latency_ms");

export const options = {
  vus: 10,
  duration: "5m",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed:   ["rate<0.01"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:80";

export default function () {
  const types = ["user.signup","payment.completed","order.created","session.started"];
  const eventType = types[Math.floor(Math.random() * types.length)];

  const submitRes = http.post(
    `${BASE_URL}/events`,
    JSON.stringify({ type: eventType, source: "load-test", payload: { vu: __VU, iter: __ITER } }),
    { headers: { "Content-Type": "application/json" } }
  );

  check(submitRes, {
    "submit 202": (r) => r.status === 202,
    "has event_id": (r) => JSON.parse(r.body).event_id !== undefined,
  });

  if (submitRes.status === 202) {
    eventsSubmitted.add(1);
    const eventId = JSON.parse(submitRes.body).event_id;
    sleep(1);
    const start = Date.now();
    const getRes = http.get(`${BASE_URL}/events/${eventId}`);
    processingLatency.add(Date.now() - start);
    check(getRes, {
      "get 200": (r) => r.status === 200,
      "processed": (r) => { try { return JSON.parse(r.body).status === "processed"; } catch { return false; } },
    });
  }
  sleep(0.5);
}
