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
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Left: Back + Brand */}
          <div className="flex items-center space-x-4">
            {onBackToHome && (
              <button
                onClick={onBackToHome}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 px-4 py-2 rounded-lg transition-all duration-200 border border-gray-200"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="font-medium">Back to Dashboard</span>
              </button>
            )}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">StockSearch</h1>
                <p className="text-xs text-gray-500">Market Intelligence</p>
              </div>
            </div>
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu((s) => !s)}
              className="flex items-center space-x-3 bg-gray-50 hover:bg-gray-100 px-4 py-2.5 rounded-xl border border-gray-200 transition-all duration-200"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white font-semibold text-sm">
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

      {/* Main Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={(e) => { e.preventDefault(); performSearch(); }} className="mb-4">
              <div className="relative flex items-center bg-white rounded-2xl shadow-lg border border-gray-200 hover:border-blue-300 transition-all duration-300 overflow-hidden">
                <div className="pl-6 text-gray-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
                  className="flex-1 px-6 py-4 text-lg outline-none bg-transparent placeholder-gray-400"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-4 font-semibold transition-all duration-300 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Searching...</span>
                    </div>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span>Search Markets</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Stats + Message */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {stats.query && (
                  <div className="text-sm text-gray-600">
                    Found <span className="font-semibold text-gray-900">{stats.total}</span> results for{" "}
                    <span className="font-semibold text-blue-600">"{stats.query}"</span>
                    {stats.time > 0 && <span> in {stats.time.toFixed(2)}s</span>}
                  </div>
                )}
                
                {isLiveLoading && (
                  <div className="flex items-center space-x-2 text-sm text-blue-600">
                    <div className="w-3 h-3 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
                    <span>Updating live data...</span>
                  </div>
                )}
              </div>

              {lastUpdated && (
                <div className="text-sm text-gray-500">
                  Last updated: <span className="font-medium text-gray-700">{lastUpdated}</span>
                </div>
              )}
            </div>

            {message.text && (
              <div className={`mt-4 p-4 rounded-lg border ${
                message.type === 'success' 
                  ? 'bg-green-50 border-green-200 text-green-700' 
                  : message.type === 'error'
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-blue-50 border-blue-200 text-blue-700'
              }`}>
                <div className="flex items-center space-x-2">
                  <svg className={`w-4 h-4 ${
                    message.type === 'success' ? 'text-green-500' : 
                    message.type === 'error' ? 'text-red-500' : 'text-blue-500'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {message.type === 'success' ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    ) : message.type === 'error' ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    )}
                  </svg>
                  <span className="font-medium">{message.text}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stocks Grid */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Market Overview</h2>
            <div className="text-sm text-gray-500 bg-white px-3 py-1 rounded-lg border border-gray-200">
              Real-time Data
            </div>
          </div>

          {displayedStocks.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-lg">
                {sectorFilter
                  ? isLiveLoading
                    ? "Loading sector data..."
                    : "No stocks found in this sector."
                  : "No stocks match your search criteria."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {displayedStocks.map((stock) => (
                <div
                  key={stock.symbol || stock.id || Math.random()}
                  onClick={() => setSelectedStock(stock.symbol)}
                  className={`bg-white rounded-xl p-6 shadow-sm hover:shadow-xl border transition-all duration-300 transform hover:-translate-y-1 cursor-pointer ${
                    stock.changed === "up"
                      ? "border-green-200 hover:border-green-300"
                      : stock.changed === "down"
                      ? "border-red-200 hover:border-red-300"
                      : "border-gray-200 hover:border-blue-300"
                  }`}
                >
                  <StockCard stock={stock} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
            <span>StockSearch © 2025</span>
            <span>•</span>
            <span>Professional Trading Platform</span>
            <span>•</span>
            <span>Real-time Market Data</span>
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
    </div>
  );
};

export default Search;