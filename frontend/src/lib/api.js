import axios from 'axios'
import { clearAccessToken, getAccessToken, setAccessToken } from '@/features/auth/auth-storage'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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
