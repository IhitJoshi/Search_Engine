import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import QuerySearch from "../components/QuerySearch";

const Home = ({ username, onLogout, onNavigateToSearch }) => {
  const [stocks, setStocks] = useState(() => {
    try {
      const cached = localStorage.getItem("slider_stocks");
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStock, setSelectedStock] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const navigate = useNavigate();

  
// Categories for the boxes - matching actual database sectors
// Alternative - More cohesive gradient combinations
const categories = [
  { 
    name: "Technology", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ), 
    filter: "Technology", 
    limit: null, 
    color: "from-blue-700 to-blue-500" 
  },
  { 
    name: "Finance", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ), 
    filter: "Financial Services", 
    limit: null, 
    color: "from-emerald-700 to-emerald-500" 
  },
  { 
    name: "Energy", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ), 
    filter: "Energy", 
    limit: null, 
    color: "from-amber-700 to-amber-500" 
  },
  { 
    name: "Healthcare", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ), 
    filter: "Healthcare", 
    limit: null, 
    color: "from-rose-600 to-rose-400" 
  },
  { 
    name: "Automotive", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ), 
    filter: "Automotive", 
    limit: null, 
    color: "from-indigo-600 to-indigo-400" 
  },
  { 
    name: "All Stocks", 
    icon: (
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ), 
    filter: "", 
    limit: null, 
    color: "from-slate-800 to-slate-600" 
  },
];

  // Fetch stocks for ticker
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await api.get("/api/stocks", { params: { limit: 50 } });
        const next = Array.isArray(res.data) ? res.data : [];
        if (next.length > 0) {
          setStocks(next);
          try {
            localStorage.setItem("slider_stocks", JSON.stringify(next));
          } catch {}
        }
      } catch (err) {
        console.error("Error fetching stocks:", err);
      }
    };

    fetchStocks();
    const interval = setInterval(fetchStocks, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onNavigateToSearch(searchQuery);
    }
  };

  const handleCategoryClick = (category) => {
    if (category.filter === "") {
      onNavigateToSearch("", category.limit);
    } else {
      onNavigateToSearch(category.filter, category.limit);
    }
  };

  const handleLogoutClick = async () => {
    try {
      await api.post("/api/logout");
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("isAuthenticated");
      localStorage.removeItem("username");
      onLogout();
      navigate('/login'); // FIXED: Added navigation
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black overflow-hidden relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                          linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}></div>
        
        {/* Animated trading chart lines */}
        <div className="absolute top-1/4 left-0 w-full h-32">
          <svg width="100%" height="100%" className="opacity-10">
            <path d="M0,60 Q100,30 200,80 T400,40 T600,100 T800,20 L1000,60" 
                  stroke="#3b82f6" strokeWidth="2" fill="none" className="animate-pulse"/>
            <path d="M0,100 Q100,60 200,120 T400,80 T600,140 T800,60 L1000,100" 
                  stroke="#10b981" strokeWidth="2" fill="none" className="animate-pulse delay-75"/>
          </svg>
        </div>

        {/* Glowing orbs */}
        <div className="absolute top-20 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header */}
      <header className="relative z-50 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Brand */}
          <div className="flex items-center space-x-3 group cursor-pointer">
            <div className="relative w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/30 group-hover:shadow-xl group-hover:shadow-cyan-500/40 transition-all duration-300 group-hover:scale-105">
              <span className="text-white font-bold text-lg">S</span>
              <div className="absolute inset-0 rounded-lg border border-cyan-400/30"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                StockSearch
              </h1>
              <p className="text-xs text-gray-400">Professional Trading Terminal</p>
            </div>
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu((s) => !s)}
              className="flex items-center space-x-3 bg-gray-800/60 hover:bg-gray-800 px-4 py-2.5 rounded-xl border border-gray-700 transition-all duration-200 hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/10"
            >
              <div className="w-9 h-9 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                {username ? username.charAt(0).toUpperCase() : "U"}
                <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-gray-900"></div>
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-100">{username}</p>
                <p className="text-xs text-cyan-400">Active Trader</p>
              </div>
              <svg className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showProfileMenu ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-gray-800/95 backdrop-blur-xl rounded-xl shadow-2xl border border-gray-700 z-[100] overflow-hidden animate-fade-in">
                <div className="p-4 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900/50">
                  <p className="text-sm font-medium text-gray-100">{username}</p>
                  <p className="text-xs text-cyan-400 mt-1">Premium Trading Account</p>
                </div>
                <button
                  onClick={() => { setShowProfileMenu(false); navigate('/profile'); }}
                  className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-gray-700/50 flex items-center space-x-2 transition-colors duration-150 border-b border-gray-700/50"
                >
                  <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>Profile Settings</span>
                </button>
                <button
                  onClick={() => { setShowProfileMenu(false); handleLogoutClick(); }}
                  className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 flex items-center space-x-2 transition-colors duration-150"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Live Market Ticker */}
      <div className="relative bg-gradient-to-r from-gray-900 via-gray-900 to-gray-800 text-white py-3 overflow-hidden border-b border-cyan-500/20">
        {/* Animated pulse line */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-pulse"></div>
        
        <div className="ticker-wrapper">
          <div className="ticker-content">
            {stocks.concat(stocks).map((stock, index) => (
              <div key={`${stock.symbol}-${index}`} className="ticker-item group hover:bg-gray-800/50 transition-all duration-200 px-6 py-2 rounded-lg">
                <span className="font-bold text-cyan-300 group-hover:text-cyan-200 transition-colors">{stock.symbol}</span>
                <span className="mx-3 text-gray-300 group-hover:text-white transition-colors">${stock.price?.toFixed(2)}</span>
                <span
                  className={`font-semibold px-3 py-1 rounded-lg transition-all duration-200 flex items-center space-x-1 ${
                    stock.change_percent >= 0 
                      ? "text-emerald-300 bg-emerald-900/20 group-hover:bg-emerald-900/30" 
                      : "text-red-300 bg-red-900/20 group-hover:bg-red-900/30"
                  }`}
                >
                  {stock.change_percent >= 0 ? (
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  ) : (
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  )}
                  <span>{Math.abs(stock.change_percent || 0).toFixed(2)}%</span>
                </span>
                <div className="w-px h-6 bg-cyan-700/30 mx-4 group-hover:bg-cyan-500/50 transition-colors"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12 relative z-10">
        {/* Welcome Section */}
        <div className="text-center mb-12 animate-fade-up">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800/50 backdrop-blur-sm rounded-full border border-cyan-500/20 mb-4">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-cyan-400">LIVE MARKET DATA</span>
          </div>
          <h2 className="text-5xl font-bold mb-4 bg-gradient-to-r from-gray-100 via-cyan-100 to-gray-100 bg-clip-text text-transparent">
            Welcome back, {username}!
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Access real-time market data, advanced analytics, and professional trading tools
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-12 animate-fade-up" style={{animationDelay: "0.1s"}}>
          <QuerySearch />
        </div>

        {/* Market Categories */}
        <div className="mb-12 animate-fade-up" style={{animationDelay: "0.2s"}}>
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-2xl font-bold text-gray-100">Explore Market Sectors</h3>
            <span className="text-sm text-gray-400">Click to explore</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category, index) => (
              <button
                key={index}
                onClick={() => handleCategoryClick(category)}
                className={`group relative bg-gray-800/40 backdrop-blur-sm rounded-2xl border transition-all duration-500 transform hover:-translate-y-2 p-6 text-left overflow-hidden hover:shadow-2xl ${
                  category.name === "All Stocks"
                    ? "border-cyan-500/30 hover:border-cyan-400"
                    : "border-gray-700 hover:border-gray-600"
                }`}
              >
                {/* Animated gradient border */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-gray-700/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-transparent via-gray-900/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                <div className="relative">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className={`relative w-14 h-14 rounded-xl flex items-center justify-center text-2xl shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl bg-gradient-to-r ${category.color}`}>
                      {category.icon}
                      <div className="absolute inset-0 rounded-xl border border-white/10"></div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-100 group-hover:text-white transition-colors">
                        {category.name}
                      </h3>
                      <p className="text-sm text-gray-400">
                        {category.name === "All Stocks"
                          ? "Complete market overview"
                          : category.limit
                          ? `${category.limit}+ companies`
                          : "All companies"}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-medium text-cyan-400 bg-cyan-900/20 px-3 py-1.5 rounded-full group-hover:bg-cyan-900/30 transition-colors">
                      View Sector →
                    </span>
                    <svg className="w-5 h-5 text-gray-500 group-hover:text-cyan-400 transform group-hover:translate-x-2 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-up" style={{animationDelay: "0.3s"}}>
          <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 hover:border-cyan-500/30 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-900/50 to-cyan-900/50 flex items-center justify-center">
                <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-100">{stocks.length}+</div>
                <div className="text-gray-400">Active Stocks</div>
              </div>
            </div>
          </div>
          <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 hover:border-emerald-500/30 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-emerald-900/50 to-green-900/50 flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-100">24/7</div>
                <div className="text-gray-400">Real-time Data</div>
              </div>
            </div>
          </div>
          <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 hover:border-purple-500/30 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-900/50 to-pink-900/50 flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-100">99.9%</div>
                <div className="text-gray-400">Uptime Reliability</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="relative border-t border-gray-800/50 mt-20 py-6 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-sm text-gray-500">
            © 2024 StockSearch Pro • Real-time market data • Professional analytics • Secure trading
          </p>
        </div>
      </div>

      {/* Enhanced Ticker Animation Styles */}
      <style>{`
        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        /* Hide scrollbar for all browsers */
        .ticker-wrapper {
          width: 100%;
          overflow: hidden;
          position: relative;
        }

        .ticker-wrapper::-webkit-scrollbar {
          display: none;
        }

        .ticker-content {
          display: flex;
          animation: scroll-left 60s linear infinite;
          width: max-content;
          will-change: transform;
        }

        .ticker-item {
          display: inline-flex;
          align-items: center;
          padding: 0 1rem;
          white-space: nowrap;
          border-right: 1px solid rgba(6, 182, 212, 0.2);
          transition: all 0.3s ease;
        }

        .ticker-content:hover {
          animation-play-state: paused;
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-fade-up {
          animation: fade-up 0.6s ease-out;
        }

        /* Global scrollbar hiding */
        * {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        *::-webkit-scrollbar {
          display: none;
        }

        /* Ensure smooth scrolling */
        html {
          scroll-behavior: smooth;
        }

        /* Custom glow effects */
        .glow {
          box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
        }

        .glow:hover {
          box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
        }
      `}</style>
    </div>
  );
};

export default Home;
