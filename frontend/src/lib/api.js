import axios from 'axios'
import { clearAccessToken, getAccessToken, setAccessToken } from '@/features/auth/auth-storage'

// Prefer the page hostname so 127.0.0.1 vs localhost stay consistent for CORS/cookies.
const defaultHost =
  typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const baseURL =
  import.meta.env.VITE_API_BASE_URL ?? `http://${defaultHost}:8000/api/v1`

export const api = axios.create({
  baseURL,
  // Neon round-trips can be slow on cold connections.
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    // CSRF defence for cookie-authenticated auth endpoints (refresh/logout).
    'X-Requested-With': 'XMLHttpRequest',
  },
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (!config.headers['X-Requested-With']) {
    config.headers['X-Requested-With'] = 'XMLHttpRequest'
  }
  return config
})

let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes('/auth/token/') &&
      !original.url?.includes('/auth/register/')
    ) {
      original._retry = true
      try {
        if (!refreshPromise) {
          refreshPromise = api
            .post('/auth/token/refresh/')
            .then((res) => {
              setAccessToken(res.data.access)
              return res.data.access
            })
            .finally(() => {
              refreshPromise = null
            })
        }
        const access = await refreshPromise
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch {
        clearAccessToken()
      }
    }
    return Promise.reject(error)
  },
)
