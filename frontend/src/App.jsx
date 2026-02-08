import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import api from "./config/api";
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
      const response = await api.get("/api/auth/check");

      if (response.status === 200) {
        const data = response.data;
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
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black flex items-center justify-center">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
        
        <div className="relative text-center z-10">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <div className="relative w-14 h-14 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/30 group">
              <span className="text-white font-bold text-2xl">S</span>
              <div className="absolute inset-0 rounded-xl border border-cyan-400/30"></div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              StockSearch
            </h1>
          </div>
          <div className="flex items-center justify-center space-x-3 text-gray-400">
            <div className="w-6 h-6 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-lg">Loading your trading dashboard...</span>
          </div>
          
          {/* Glowing pulse line */}
          <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-pulse mt-8"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                          linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}></div>
        
        {/* Glowing orbs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10">
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