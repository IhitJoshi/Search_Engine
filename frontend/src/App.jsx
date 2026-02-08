import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import api from "./config/api";

import Login from "./components/Login";
import Signup from "./components/Signup";
import Home from "./components/Home";
import Search from "./components/Search";
import Profile from "./components/Profile";

const App = () => {
  const [username, setUsername] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [stockLimit, setStockLimit] = useState(null);
  const [sectorFilter, setSectorFilter] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
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
  };

  const handleLoginSuccess = (user) => {
    setUsername(user);
    setIsAuthenticated(true);
    navigate("/home");
  };

  const handleLogout = () => {
    setUsername("");
    setIsAuthenticated(false);
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
            <Search
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
    </Routes>
  );
};

export default App;
