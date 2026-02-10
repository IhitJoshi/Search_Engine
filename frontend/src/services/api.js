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
 *   VITE_API_URL - The backend API base URL (optional)
 *   - Development: Can be set to http://localhost:5000 if backend runs separately
 *   - Production: Uses relative paths (empty string) for same-origin requests
 */

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach JWT token if available & log in development
api.interceptors.request.use(
  (config) => {
    // Attach Authorization header from localStorage token (JWT)
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

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
