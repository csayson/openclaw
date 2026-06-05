import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = useAuthStore.getState().refreshToken
      if (refresh) {
        try {
          const { data } = await axios.post('/api/auth/refresh', null, {
            params: { token: refresh },
          })
          useAuthStore.getState().setTokens(data.access_token, data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api.request(error.config)
        } catch {
          useAuthStore.getState().logout()
        }
      }
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password })),
  register: (data: any) => api.post('/auth/register', data),
  setupTOTP: () => api.post('/auth/totp/setup'),
  enableTOTP: (code: string) => api.post('/auth/totp/enable', null, { params: { code } }),
  verifyTOTP: (code: string) => api.post('/auth/totp/verify', null, { params: { code } }),
}

export const tradingApi = {
  start: (account_id: string, strategies: string[]) =>
    api.post('/trading/start', { account_id, strategies }),
  stop: (account_id: string, mode: string) => api.post('/trading/stop', { account_id, mode }),
  pause: (account_id: string) => api.post('/trading/pause', null, { params: { account_id } }),
  resume: (account_id: string) => api.post('/trading/resume', null, { params: { account_id } }),
  emergency: (account_id: string) =>
    api.post('/trading/emergency-stop', { account_id, confirm: 'CONFIRM' }),
  status: (account_id: string) => api.get(`/trading/status/${account_id}`),
}

export const positionsApi = {
  getOpen: (account_id: string) => api.get('/positions/open', { params: { account_id } }),
  getClosed: (account_id: string, params?: any) =>
    api.get('/positions/closed', { params: { account_id, ...params } }),
  getSummary: (account_id: string, params?: any) =>
    api.get('/positions/history/summary', { params: { account_id, ...params } }),
}

export const accountsApi = {
  list: () => api.get('/accounts/'),
  create: (data: any) => api.post('/accounts/', data),
  get: (id: string) => api.get(`/accounts/${id}`),
  getBrokers: (id: string) => api.get(`/accounts/${id}/brokers`),
  connectBroker: (data: any) => api.post('/accounts/brokers/connect', data),
}

export const reportsApi = {
  generate: (data: any) => api.post('/reports/generate', data),
  list: (account_id: string) => api.get(`/reports/list/${account_id}`),
}

export default api
