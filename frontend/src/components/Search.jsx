import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import StockCard from "./StockCard";
import StockDetails from "./StockDetails";

const Search = ({ username, onLogout, initialQuery = "", sectorFilter = "", stockLimit = null, onBackToHome }) => {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [displayedStocks, setDisplayedStocks] = useState([]);
  const [allStocks, setAllStocks] = useState([]);
  const [previousStocks, setPreviousStocks] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLiveLoading, setIsLiveLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, time: 0, query: "" });
  const [message, setMessage] = useState({ text: "", type: "" });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const navigate = useNavigate();
  const prevPropsRef = useRef({ initialQuery: "", sectorFilter: "", stockLimit: null });

  // 🟢 Fetch stocks initially and every 10 seconds
  useEffect(() => {
    let previousStocksCache = {};

    const fetchStocks = async () => {
      try {
        setIsLiveLoading(true);
        const res = await fetch("http://localhost:5000/api/stocks");
        const data = await res.json();

        // Detect price changes for animation
        const updated = data.map((stock) => {
          const prev = previousStocksCache[stock.symbol];
          const changed =
            prev && prev.price !== stock.price
              ? stock.price > prev.price
                ? "up"
                : "down"
              : null;
          return { ...stock, changed };
        });

        setAllStocks(updated);
        previousStocksCache = Object.fromEntries(data.map((s) => [s.symbol, s]));
        setPreviousStocks(previousStocksCache);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.error("Error fetching stocks:", err);
      } finally {
        setIsLiveLoading(false);
      }
    };

    fetchStocks();
    const interval = setInterval(fetchStocks, 10000);
    return () => clearInterval(interval);
  }, []);

  // 🔍 Perform search - memoized to prevent infinite loops
  const performSearch = useCallback(async () => {
    const query = searchQuery.trim();
    
    setIsLoading(true);
    setMessage({ text: "", type: "" });

    try {
      // If the user typed a plain "all"/"every"/"everything" query (and
      // did not name a sector), show live cached stocks. This handles a
      // variety of user phrasings like "all", "all stocks", "everything",
      // "show all", "list all" etc.
      const lowerQuery = query.toLowerCase();
      const allKeywords = ['all', 'every', 'everything', 'anything', 'show all', 'list all', 'display all', 'all the'];
      // Sector name hints to avoid treating 'all tech stocks' as a plain 'all'
      const sectorHints = ['tech', 'technology', 'software', 'finance', 'financial', 'bank', 'energy', 'health', 'healthcare', 'pharma', 'automotive', 'auto', 'retail', 'industrial', 'india', 'consumer', 'telecom', 'utilities', 'realty', 'metal', 'chemical', 'infrastructure'];

      const containsAllKeyword = allKeywords.some(k => lowerQuery.includes(k));
      const containsSectorHint = sectorHints.some(s => lowerQuery.includes(s));

      if (containsAllKeyword && !containsSectorHint && !sectorFilter) {
        if (allStocks.length > 0) {
          const limited = allStocks.slice(0, stockLimit || 50);
          setDisplayedStocks(limited);
          setStats({ total: limited.length, time: 0, query: "all stocks" });
          setMessage({ text: "Showing live results", type: "success" });
        } else {
          setDisplayedStocks([]);
          setMessage({ text: "No results found.", type: "info" });
        }
        setIsLoading(false);
        return;
      }

      // If this is a sector navigation (no query, has sector), prefer live data and skip backend search
      if (!query && sectorFilter) {
        // If we already have live data, show it immediately
        if (allStocks.length > 0) {
          const limited = allStocks
            .filter((s) => s.sector === sectorFilter)
            .slice(0, stockLimit || 10);
          setDisplayedStocks(limited);
          setStats({ total: limited.length, time: 0, query: sectorFilter });
          setMessage({ text: "", type: "" });
        }
        return; // Skip backend /api/search for sector-only navigation
      }

      const requestBody = {
        query: query,
        limit: stockLimit || 50
      };
      
      // Add sector filter if provided
      if (sectorFilter) {
        requestBody.sector = sectorFilter;
      }

      const response = await fetch("http://localhost:5000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(requestBody),
      });

      if (response.status === 401) {
        onLogout();
        return;
      }

      const data = await response.json();

      if (!data.results || data.results.length === 0) {
        // Fallback: if sector selected, try client-side from live /api/stocks
        if (sectorFilter && allStocks.length > 0) {
          const limited = allStocks
            .filter((s) => s.sector === sectorFilter)
            .slice(0, stockLimit || 10);
          if (limited.length > 0) {
            setDisplayedStocks(limited);
            setStats({ total: limited.length, time: 0, query: sectorFilter });
            setMessage({ text: "Showing live results", type: "success" });
          } else {
            setDisplayedStocks([]);
            setStats({ total: 0, time: 0, query: sectorFilter || query });
            setMessage({ text: "No results found.", type: "info" });
          }
        } else {
          setDisplayedStocks([]);
          setStats({ total: 0, time: 0, query: sectorFilter || query });
          setMessage({ text: "No results found.", type: "info" });
        }
      } else {
        // Results are already limited by backend, no need to slice again
        setDisplayedStocks(data.results);
        setStats({
          total: data.results.length,
          time: data.time || 0,
          query: sectorFilter || query,
        });
      }
    } catch (error) {
      console.error("Search error:", error);
      setMessage({
        text: "Error performing search. Please try again.",
        type: "error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, sectorFilter, stockLimit, onLogout, allStocks]);

  // Auto-search if initialQuery or sectorFilter is provided
  useEffect(() => {
    // Check if props have actually changed
    const propsChanged = 
      prevPropsRef.current.initialQuery !== initialQuery ||
      prevPropsRef.current.sectorFilter !== sectorFilter ||
      prevPropsRef.current.stockLimit !== stockLimit;
    
    if (!propsChanged) {
      return; // Don't re-search if props haven't changed
    }
    
    // Update ref with current props
    prevPropsRef.current = { initialQuery, sectorFilter, stockLimit };
    
    // Trigger search based on the type of navigation
    const triggerSearch = async () => {
      if (initialQuery && initialQuery.trim()) {
        // Search by query
        await performSearch();
      } else if (sectorFilter) {
        // For sector pages, don't call backend search; live data effects will populate
        // Show a loading message while waiting for live data
        setDisplayedStocks([]);
        setStats({ total: 0, time: 0, query: sectorFilter });
        setMessage({ text: "Loading sector data…", type: "info" });
      } else if (!initialQuery && !sectorFilter && stockLimit && allStocks.length > 0) {
        // "All Stocks" - show limited stocks from cached data
        const limited = allStocks.slice(0, stockLimit);
        setDisplayedStocks(limited);
        setStats({ total: limited.length, time: 0, query: "Showing all stocks" });
      }
    };
    
    triggerSearch();
  }, [initialQuery, sectorFilter, stockLimit]);

  // When navigating for "All Stocks", update list after allStocks arrives
  useEffect(() => {
    if (!initialQuery && !sectorFilter && stockLimit && allStocks.length > 0) {
      const limited = allStocks.slice(0, stockLimit);
      setDisplayedStocks(limited);
      setStats({ total: limited.length, time: 0, query: "Showing all stocks" });
    }
  }, [allStocks, initialQuery, sectorFilter, stockLimit]);

  // When navigating for a sector, populate from live stocks once available
  useEffect(() => {
    if (sectorFilter && allStocks.length > 0) {
      const limited = allStocks
        .filter((s) => s.sector === sectorFilter)
        .slice(0, stockLimit || 10);
      if (limited.length > 0) {
        setDisplayedStocks(limited);
        setStats({ total: limited.length, time: 0, query: sectorFilter });
        setMessage({ text: "", type: "" });
      }
    }
  }, [allStocks, sectorFilter, stockLimit]);

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
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/70 flex flex-col relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-200/20 to-indigo-200/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-slate-200/20 to-blue-100/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full h-64 bg-gradient-to-r from-transparent via-blue-50/5 to-transparent"></div>
      </div>

      {/* Header */}
      <header className="relative bg-white/90 backdrop-blur-md shadow-lg/50 border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Left: Back + Brand */}
          <div className="flex items-center space-x-4">
            {onBackToHome && (
              <button
                onClick={onBackToHome}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 bg-white/50 hover:bg-white px-4 py-2.5 rounded-xl transition-all duration-300 border border-gray-200/80 hover:border-blue-300 hover:shadow-lg backdrop-blur-sm"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="font-medium">Back to Dashboard</span>
              </button>
            )}
            <div className="flex items-center space-x-3 group cursor-pointer">
              <div className="relative w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 group-hover:shadow-xl group-hover:shadow-blue-500/40 transition-all duration-300 group-hover:scale-105">
                <span className="text-white font-bold text-lg">S</span>
                <div className="absolute inset-0 rounded-xl border border-white/20"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text">StockSearch</h1>
                <p className="text-xs text-gray-500">Market Intelligence</p>
              </div>
            </div>
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu((s) => !s)}
              className="flex items-center space-x-3 bg-white/50 hover:bg-white px-4 py-2.5 rounded-xl border border-gray-200/80 transition-all duration-200 hover:shadow-lg hover:border-blue-200 backdrop-blur-sm"
            >
              <div className="relative w-9 h-9 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                {username ? username.charAt(0).toUpperCase() : "U"}
                <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">{username}</p>
                <p className="text-xs text-gray-500">Active Trader</p>
              </div>
              <svg className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showProfileMenu ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl border border-gray-200/50 z-50 overflow-hidden animate-fade-in">
                <div className="p-4 border-b border-gray-100/50 bg-gradient-to-r from-blue-50/50 to-indigo-50/50">
                  <p className="text-sm font-medium text-gray-900">{username}</p>
                  <p className="text-xs text-gray-500">Premium Account</p>
                </div>
                <button
                  onClick={() => { setShowProfileMenu(false); navigate('/profile'); }}
                  className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50/80 flex items-center space-x-2 transition-colors duration-150"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>Profile Settings</span>
                </button>
                <button
                  onClick={() => { setShowProfileMenu(false); handleLogoutClick(); }}
                  className="w-full text-left px-4 py-3 text-sm text-red-600 hover:bg-red-50/80 flex items-center space-x-2 border-t border-gray-100/50 transition-colors duration-150"
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

      {/* Main Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 relative z-10">
        {/* Search Section */}
        <div className="mb-12">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={(e) => { e.preventDefault(); performSearch(); }} className="mb-6">
              <div className="relative flex items-center bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-200/80 hover:border-blue-300/80 transition-all duration-300 overflow-hidden group">
                <div className="pl-6 text-gray-400 group-hover:text-blue-500 transition-colors">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
                  className="flex-1 px-6 py-5 text-lg outline-none bg-transparent placeholder-gray-400 focus:placeholder-gray-300 transition-colors"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-10 py-5 font-semibold transition-all duration-500 flex items-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed group/btn"
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span className="text-lg">Searching...</span>
                    </div>
                  ) : (
                    <>
                      <svg className="w-6 h-6 transform group-hover/btn:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span className="text-lg">Search Markets</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Stats + Message */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {stats.query && (
                  <div className="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200/50 text-sm text-gray-700">
                    Found <span className="font-semibold text-gray-900">{stats.total}</span> results for{" "}
                    <span className="font-semibold text-blue-600">"{stats.query}"</span>
                    {stats.time > 0 && <span> in {stats.time.toFixed(2)}s</span>}
                  </div>
                )}
                
                {isLiveLoading && (
                  <div className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200/50 text-sm text-blue-600">
                    <div className="w-3 h-3 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
                    <span>Updating live data...</span>
                  </div>
                )}
              </div>

              {lastUpdated && (
                <div className="px-4 py-2 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-200/50 text-sm text-gray-600">
                  Last updated: <span className="font-semibold text-gray-800">{lastUpdated}</span>
                </div>
              )}
            </div>

            {message.text && (
              <div className={`mt-6 p-5 rounded-2xl border backdrop-blur-sm ${
                message.type === 'success' 
                  ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200/70 text-emerald-800' 
                  : message.type === 'error'
                  ? 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200/70 text-red-800'
                  : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200/70 text-blue-800'
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    message.type === 'success' ? 'bg-emerald-100' : 
                    message.type === 'error' ? 'bg-red-100' : 'bg-blue-100'
                  }`}>
                    <svg className={`w-5 h-5 ${
                      message.type === 'success' ? 'text-emerald-600' : 
                      message.type === 'error' ? 'text-red-600' : 'text-blue-600'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {message.type === 'success' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      ) : message.type === 'error' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      )}
                    </svg>
                  </div>
                  <span className="font-semibold text-lg">{message.text}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stocks Grid */}
        <div className="mb-8 animate-fade-up">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Market Overview</h2>
              <p className="text-gray-600">Browse real-time stock data and insights</p>
            </div>
            <div className="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200/50 text-sm text-blue-600 font-medium">
              ⚡ Real-time Data
            </div>
          </div>

          {displayedStocks.length === 0 ? (
            <div className="text-center py-16 bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg">
              <div className="w-20 h-20 mx-auto mb-6 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-xl mb-2">
                {sectorFilter
                  ? isLiveLoading
                    ? "Loading sector data..."
                    : "No stocks found in this sector."
                  : "No stocks match your search criteria."}
              </p>
              <p className="text-gray-400 text-sm">Try a different search term or explore other sectors</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {displayedStocks.map((stock) => (
                <div
                  key={stock.symbol || stock.id || Math.random()}
                  onClick={() => setSelectedStock(stock.symbol)}
                  className={`relative bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover:shadow-2xl border transition-all duration-500 transform hover:-translate-y-2 cursor-pointer group ${
                    stock.changed === "up"
                      ? "border-emerald-200/70 hover:border-emerald-300"
                      : stock.changed === "down"
                      ? "border-red-200/70 hover:border-red-300"
                      : "border-gray-200/70 hover:border-blue-300"
                  }`}
                >
                  {/* Glow effect */}
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-transparent via-gray-50/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  {/* Price change indicator */}
                  {stock.changed && (
                    <div className={`absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center shadow-lg ${
                      stock.changed === "up"
                        ? "bg-emerald-500 text-white"
                        : "bg-red-500 text-white"
                    }`}>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {stock.changed === "up" ? (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                        )}
                      </svg>
                    </div>
                  )}
                  
                  <StockCard stock={stock} />
                  
                  {/* Hover overlay */}
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/0 to-indigo-500/0 opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="relative bg-white/90 backdrop-blur-sm border-t border-gray-200/50 py-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="text-center md:text-left">
              <div className="flex items-center space-x-3 mb-2 justify-center md:justify-start">
                <div className="w-6 h-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xs">S</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">StockSearch Pro</span>
              </div>
              <p className="text-sm text-gray-500">Professional Trading Platform</p>
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-500">
              <span>© 2025 StockSearch</span>
              <span>•</span>
              <span>Real-time Market Data</span>
              <span>•</span>
              <span>Secure Trading</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Stock Details Modal */}
      {selectedStock && (
        <StockDetails
          symbol={selectedStock}
          onClose={() => setSelectedStock(null)}
        />
      )}

      {/* Add custom animation styles */}
      <style>{`
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

        .animate-fade-up {
          animation: fade-up 0.6s ease-out;
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default Search;