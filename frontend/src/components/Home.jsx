import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const Home = ({ username, onLogout, onNavigateToSearch }) => {
  const [stocks, setStocks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStock, setSelectedStock] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const navigate = useNavigate();

  // Categories for the boxes - matching actual database sectors
  const categories = [
    { name: "Technology", icon: "💻", filter: "Technology", limit: 10 },
    { name: "Finance", icon: "🏦", filter: "Financial Services", limit: 10 },
    { name: "Energy", icon: "⚡", filter: "Energy", limit: 10 },
    { name: "Healthcare", icon: "🏥", filter: "Healthcare", limit: 10 },
    { name: "Automotive", icon: "🚗", filter: "Automotive", limit: 10 },
    { name: "All Stocks", icon: "📈", filter: "", limit: 50 },
  ];

  // Fetch stocks for ticker
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/stocks");
        const data = await res.json();
        setStocks(data);
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
      onNavigateToSearch("", category.limit || 50);
    } else {
      onNavigateToSearch(category.filter, category.limit || 10);
    }
  };

  const handleLogoutClick = async () => {
    try {
      await fetch("http://localhost:5000/api/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("isAuthenticated");
      localStorage.removeItem("username");
      onLogout();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">StockSearch</h1>
              <p className="text-sm text-gray-500">Professional Trading Dashboard</p>
            </div>
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu((s) => !s)}
              className="flex items-center space-x-3 bg-gray-50 hover:bg-gray-100 px-4 py-2.5 rounded-xl border border-gray-200 transition-all duration-200"
            >
              <div className="w-9 h-9 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white font-semibold text-sm">
                {username ? username.charAt(0).toUpperCase() : "U"}
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">{username}</p>
                <p className="text-xs text-gray-500">Active Trader</p>
              </div>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-200 z-20 overflow-hidden">
                <div className="p-4 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{username}</p>
                  <p className="text-xs text-gray-500">Premium Account</p>
                </div>
                <button
                  onClick={() => { setShowProfileMenu(false); navigate('/profile'); }}
                  className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>Profile Settings</span>
                </button>
                <button
                  onClick={() => { setShowProfileMenu(false); handleLogoutClick(); }}
                  className="w-full text-left px-4 py-3 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2 border-t border-gray-100"
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
      <div className="bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900 text-white py-3 overflow-hidden border-b border-blue-700/30">
        <div className="ticker-wrapper">
          <div className="ticker-content">
            {stocks.concat(stocks).map((stock, index) => (
              <div key={`${stock.symbol}-${index}`} className="ticker-item">
                <span className="font-bold text-blue-200">{stock.symbol}</span>
                <span className="mx-3 text-gray-300">${stock.price?.toFixed(2)}</span>
                <span
                  className={`font-semibold ${
                    stock.change_percent >= 0 ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {stock.change_percent >= 0 ? "↗" : "↘"} 
                  {Math.abs(stock.change_percent || 0).toFixed(2)}%
                </span>
                <div className="w-px h-4 bg-blue-700/50 mx-4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Welcome Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome back, {username}!
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Access real-time market data, advanced analytics, and professional trading tools
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-16">
          <form onSubmit={handleSearch} className="max-w-3xl mx-auto">
            <div className="relative flex items-center bg-white rounded-2xl shadow-lg border border-gray-200 hover:border-blue-300 transition-all duration-300 overflow-hidden">
              <div className="pl-6 text-gray-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
                className="flex-1 px-6 py-5 text-lg outline-none bg-transparent placeholder-gray-400"
              />
              <button
                type="submit"
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-5 font-semibold transition-all duration-300 flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Search Markets</span>
              </button>
            </div>
          </form>
        </div>

        {/* Market Categories */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">Explore Market Sectors</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category, index) => (
              <button
                key={index}
                onClick={() => handleCategoryClick(category)}
                className={`group bg-white rounded-xl shadow-sm hover:shadow-xl border transition-all duration-300 transform hover:-translate-y-1 p-6 text-left ${
                  category.name === "All Stocks"
                    ? "border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50"
                    : "border-gray-100 hover:border-blue-200"
                }`}
              >
                <div className="flex items-center space-x-4 mb-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-xl ${
                    category.name === "All Stocks" 
                      ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white" 
                      : "bg-blue-100 text-blue-600"
                  }`}>
                    {category.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      {category.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {category.name === "All Stocks" ? "Complete market overview" : `${category.limit}+ companies`}
                    </p>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    View Sector
                  </span>
                  <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transform group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        {/* <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mt-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-2">{stocks.length}+</div>
              <div className="text-gray-600">Active Stocks</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-2">24/7</div>
              <div className="text-gray-600">Real-time Data</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-2">99.9%</div>
              <div className="text-gray-600">Uptime Reliability</div>
            </div>
          </div>
        </div> */}
      </div>

      {/* Ticker Animation Styles */}
      <style>{`
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
          animation: scroll-left 80s linear infinite;
          width: max-content;
        }

        .ticker-item {
          display: inline-flex;
          align-items: center;
          padding: 0 2rem;
          white-space: nowrap;
          border-right: 1px solid rgba(59, 130, 246, 0.3);
        }

        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        .ticker-content:hover {
          animation-play-state: paused;
        }

        /* Global scrollbar hiding */
        * {
          -ms-overflow-style: none;  /* IE and Edge */
          scrollbar-width: none;  /* Firefox */
        }

        *::-webkit-scrollbar {
          display: none;  /* Chrome, Safari and Opera */
        }

        /* Ensure smooth scrolling */
        html {
          scroll-behavior: smooth;
        }
      `}</style>
    </div>
  );
};

export default Home;