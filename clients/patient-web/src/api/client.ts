import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Attach JWT token from localStorage for all outgoing requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('clinova_patient_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global response interceptor: handle 401 expired/invalid sessions
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      // Don't loop redirect if already on login/identify or landing
      if (currentPath !== '/' && currentPath !== '/identify') {
        localStorage.removeItem('clinova_patient_token');
        localStorage.removeItem('clinova_patient_data');
        window.location.href = '/identify?expired=1';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
