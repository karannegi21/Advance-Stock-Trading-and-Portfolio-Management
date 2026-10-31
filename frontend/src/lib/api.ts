import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/prices';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = useAuthStore.getState().refreshToken;
      if (refresh) {
        try {
          const r = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh });
          const newAccess = r.data.access_token;
          const user = useAuthStore.getState().user!;
          const newRefresh = r.data.refresh_token || refresh;
          useAuthStore.getState().setAuth(user, newAccess, newRefresh);
          original.headers.Authorization = `Bearer ${newAccess}`;
          return api(original);
        } catch {
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  }
);

export { WS_URL };
