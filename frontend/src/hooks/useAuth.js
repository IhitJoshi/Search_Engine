import { useCallback, useEffect, useState } from "react";
import api from "../services/api";

export const useAuth = () => {
  const [username, setUsername] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await api.get("/api/auth/check");
      if (response.status === 200 && response.data.logged_in) {
        setUsername(response.data.username);
        setIsAuthenticated(true);
      }
    } catch (err) {
      console.log("Auth check failed");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback((user) => {
    setUsername(user);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    setUsername("");
    setIsAuthenticated(false);
  }, []);

  return {
    username,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAuth: checkAuth,
  };
};
