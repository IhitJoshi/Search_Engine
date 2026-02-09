import React, { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

import Home from "../pages/Home";
import Login from "../pages/Login";
import Signup from "../pages/Signup";
import Dashboard from "../pages/Dashboard";
import Profile from "../pages/Profile";
import NotFound from "../pages/NotFound";

const AppRoutes = () => {
  const navigate = useNavigate();
  const { username, isAuthenticated, isLoading, login, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [stockLimit, setStockLimit] = useState(null);

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
