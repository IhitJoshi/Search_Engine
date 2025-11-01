import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import Login from "./components/Login";
import Signup from "./components/Signup";
import Home from "./components/Home";
import Search from "./components/Search";
import Profile from "./components/Profile";

const AppContent = () => {
  const [username, setUsername] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [stockLimit, setStockLimit] = useState(null);
  const [sectorFilter, setSectorFilter] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/auth/check", {
        method: "GET",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        if (data.logged_in) {
          setUsername(data.username);
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error("Auth check failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSuccess = (username) => {
    setUsername(username);
    setIsAuthenticated(true);
    navigate("/home");
  };

  const handleLogout = () => {
    setUsername("");
    setIsAuthenticated(false);
    navigate("/login");
  };

  const handleNavigateToSearch = (queryOrSector = "", limit = null) => {
    // Determine if this is a sector filter or search query
    const sectors = ["Technology", "Financial Services", "Energy", "Healthcare", "Consumer Cyclical", "Communication Services", "Automotive"];
    
    if (sectors.includes(queryOrSector)) {
      // It's a sector filter
      setSectorFilter(queryOrSector);
      setSearchQuery("");
    } else if (queryOrSector === "") {
      // Empty string means show all stocks (no filter)
      setSearchQuery("");
      setSectorFilter("");
    } else {
      // It's a search query
      setSearchQuery(queryOrSector);
      setSectorFilter("");
    }
    
    setStockLimit(limit);
    navigate("/search");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">S</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">StockSearch</h1>
          </div>
          <div className="flex items-center justify-center space-x-2 text-gray-600">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Loading your trading dashboard...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
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
    </div>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;