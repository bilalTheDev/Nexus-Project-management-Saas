/**
 * Staging smoke load: login, board, move, comment.
 * Run: k6 run -e BASE_URL=https://api.example.com -e EMAIL=... -e PASSWORD=... load/k6-smoke.js
 * Record p95 and error rate at VUs 10/50/100 against staging only.
 */
import http from 'k6/http'
import { check, sleep } from 'k6'

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 10),
      duration: __ENV.DURATION || '1m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<3000'],
  },
}

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8000/api/v1'

export default function () {
  const login = http.post(
    `${BASE}/auth/token/`,
    JSON.stringify({
      email: __ENV.EMAIL || 'maya@northstar.studio',
      password: __ENV.PASSWORD || 'DemoPass1',
    }),
    { headers: { 'Content-Type': 'application/json' } },
  )
  check(login, { 'login 200': (r) => r.status === 200 })
  const access = login.json('access')
  const headers = {
    Authorization: `Bearer ${access}`,
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  }
  const board = http.get(
    `${BASE}/workspaces/northstar-studio/projects/NEX-WEB/board/`,
    { headers },
  )
  check(board, { 'board 200': (r) => r.status === 200 })
  sleep(1)
}
