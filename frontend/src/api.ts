import axios from 'axios';

// Automatically send/receive cookies (session) in cross-origin requests
export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true, 
});

// Global response interceptor — handle 401s across the app
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear any stale local state — the AuthContext will handle redirect
      console.warn('Session expired or invalid. Redirecting to login.');
    }
    return Promise.reject(error);
  }
);
