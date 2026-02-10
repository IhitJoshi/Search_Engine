import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

import Home from "../pages/Home";
import Login from "../pages/Login";
import Signup from "../pages/Signup";
import Dashboard from "../pages/Dashboard";
import Profile from "../pages/Profile";
import NotFound from "../pages/NotFound";

const AppRoutes = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { username, isAuthenticated, isLoading, login, logout, refreshAuth } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [stockLimit, setStockLimit] = useState(null);

  // Handle JWT token returned from Google OAuth redirect (?token=...&username=...)
  useEffect(() => {
    const search = location.search || "";
    if (!search.includes("token=")) return;

    const params = new URLSearchParams(search);
    const token = params.get("token");
    const userFromUrl = params.get("username");

    if (token) {
      localStorage.setItem("authToken", token);
      if (userFromUrl) {
        localStorage.setItem("username", userFromUrl);
        localStorage.setItem("isAuthenticated", "true");
        login(userFromUrl);
      } else {
        // Fallback: ask backend who we are using the token
        refreshAuth && refreshAuth();
      }

      // Clean the URL so token isn't visible after initial processing
      navigate(location.pathname, { replace: true });
    }
  }, [location.search, location.pathname, login, navigate, refreshAuth]);

  const handleLoginSuccess = (user) => {
    login(user);
    navigate("/home");
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleNavigateToSearch = (queryOrSector = "", limit = null) => {
    const sectors = [
      "Technology",
      "Financial Services",
      "Energy",
      "Healthcare",
      "Consumer Cyclical",
      "Communication Services",
      "Automotive",
    ];

    if (sectors.includes(queryOrSector)) {
      setSectorFilter(queryOrSector);
      setSearchQuery("");
    } else {
      setSearchQuery(queryOrSector);
      setSectorFilter("");
    }

    setStockLimit(limit);
    navigate("/search");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-white">
        Loading...
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/home" replace />
          ) : (
            <Login
              onLoginSuccess={handleLoginSuccess}
              onNavigateToSignup={() => navigate("/signup")}
            />
          )
        }
      />

      <Route
        path="/signup"
        element={
          isAuthenticated ? (
            <Navigate to="/home" replace />
          ) : (
            <Signup
              onSignupSuccess={() => navigate("/login")}
              onNavigateToLogin={() => navigate("/login")}
            />
          )
        }
      />

      <Route
        path="/home"
        element={
          isAuthenticated ? (
            <Home
              username={username}
              onLogout={handleLogout}
              onNavigateToSearch={handleNavigateToSearch}
            />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="/search"
        element={
          isAuthenticated ? (
            <Dashboard
              username={username}
              onLogout={handleLogout}
              initialQuery={searchQuery}
              sectorFilter={sectorFilter}
              stockLimit={stockLimit}
              onBackToHome={() => navigate("/home")}
            />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="/profile"
        element={
          isAuthenticated ? (
            <Profile username={username} onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? "/home" : "/login"} replace />}
      />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;
