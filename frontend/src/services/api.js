import axios from "axios";

/**
 * Centralized API configuration for the frontend.
 * 
 * All API calls MUST use this instance to ensure:
 * - Consistent base URL configuration
 * - Proper credentials handling (cookies)
 * - Easy environment switching between development and production
 * 
 * Usage:
 *   import api from "../services/api";
 *   api.get("/api/stocks");
 *   api.post("/api/login", { username, password });
 * 
 * Environment Variables:
 *   VITE_API_URL - The backend API base URL
 *   - Development: http://localhost:5000
 *   - Production: https://stock-engine-c1py.onrender.com
 */

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for debugging (can be removed in production)
api.interceptors.request.use(
  (config) => {
    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - could trigger logout here if needed
      console.warn("[API] Unauthorized request");
    }
    
    if (!error.response) {
      // Network error
      console.error("[API] Network error - server may be unreachable");
    }
    
    return Promise.reject(error);
  }
);

export default api;
