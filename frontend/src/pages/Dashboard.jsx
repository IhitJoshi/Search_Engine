import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import StockCard from "../components/StockCard";
import StockDetails from "../components/StockDetails";

const Dashboard = ({ username, onLogout, initialQuery = "", sectorFilter = "", stockLimit = null, onBackToHome }) => {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [displayedStocks, setDisplayedStocks] = useState([]);
  const [allStocks, setAllStocks] = useState([]);
  const [previousStocks, setPreviousStocks] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLiveLoading, setIsLiveLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, time: 0, query: "" });
  const [message, setMessage] = useState({ text: "", type: "" });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedPulse, setLastUpdatedPulse] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [simulatedStocks, setSimulatedStocks] = useState({});
  const navigate = useNavigate();
  const prevPropsRef = useRef({ initialQuery: "", sectorFilter: "", stockLimit: null });
  const prevPricesRef = useRef({});
  const lastUpdatedTimerRef = useRef(null);
  const pollingTimerRef = useRef(null);
  const simulationTimerRef = useRef(null);
  const lastRealPriceRef = useRef({});
  const visibleSymbolsKey = useMemo(() => (
    displayedStocks
      .map((s) => s.symbol)
      .filter(Boolean)
      .join(",")
  ), [displayedStocks]);
  const categoryCacheKey = useMemo(() => {
    const base = sectorFilter || initialQuery || "all";
    const limit = stockLimit ?? "all";
    return `category_stocks:${base}:${limit}`;
  }, [sectorFilter, initialQuery, stockLimit]);
  const normalizeResults = useCallback((results = []) => {
    if (!Array.isArray(results)) return [];
    return results.map((r) => {
      if (r && r.metrics) {
        return {
          symbol: r.symbol,
          company_name: r.company_name,
          sector: r.sector,
          price: r.metrics.price,
          volume: r.metrics.volume,
          change_percent: r.metrics.change_percent,
          last_updated: r.metrics.last_updated,
          reasons: r.reasons,
          score: r.score,
        };
      }
      return r;
    });
  }, []);
  const filterLiveStocks = useCallback((queryText, sector) => {
    const q = (queryText || "").toLowerCase().trim();
    const filterNorm = (sector || "").toLowerCase().trim();
    const filtered = allStocks.filter((s) => {
      const sym = (s.symbol || "").toLowerCase();
      const name = (s.company_name || "").toLowerCase();
      const sec = (s.sector || "").toLowerCase();
      const inSector = filterNorm ? sec === filterNorm || sec.includes(filterNorm) : true;
      if (!inSector) return false;
      if (!q) return true;
      return sym.startsWith(q) || name.startsWith(q);
    });
    const limitValue = stockLimit ?? filtered.length;
    return filtered.slice(0, limitValue);
  }, [allStocks, stockLimit]);

  const getCategoryType = useCallback((queryText) => {
    const q = (queryText || "").toLowerCase().trim();
    if (!q) return "";
    if (["gainers", "top gainers", "gainer", "top gainer"].includes(q)) return "gainers";
    if (["losers", "top losers", "loser", "top loser"].includes(q)) return "losers";
    if (["high volume", "volume leaders", "most active"].includes(q)) return "high_volume";
    return "";
  }, []);

  const applyCategoryFilter = useCallback((data, categoryType) => {
    if (!categoryType) return data;
    const list = Array.isArray(data) ? data.slice() : [];
    if (categoryType === "gainers") {
      return list
        .filter((s) => (s.change_percent ?? 0) > 0)
        .sort((a, b) => (b.change_percent ?? 0) - (a.change_percent ?? 0));
    }
    if (categoryType === "losers") {
      return list
        .filter((s) => (s.change_percent ?? 0) < 0)
        .sort((a, b) => (a.change_percent ?? 0) - (b.change_percent ?? 0));
    }
    if (categoryType === "high_volume") {
      return list.sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0));
    }
    return list;
  }, []);

  const buildWsUrl = useCallback(() => {
    const base = import.meta.env.VITE_API_URL || window.location.origin;
    const trimmed = base.endsWith("/") ? base.slice(0, -1) : base;
    return trimmed.replace(/^http/, "ws") + "/ws/stocks";
  }, []);

  const applyPriceUpdates = useCallback((updates, timestamp) => {
    const updatesMap = {};
    for (const stock of updates) {
      if (stock?.symbol) updatesMap[stock.symbol] = stock;
    }

    const prevPrices = { ...prevPricesRef.current };

    const applyToList = (list) => list.map((stock) => {
      const update = updatesMap[stock.symbol];
      if (!update) return stock;

      const prevPrice = prevPrices[stock.symbol]?.price ?? stock.price;
      let changed = null;
      if (update.price != null && prevPrice != null && update.price !== prevPrice) {
        changed = update.price > prevPrice ? "up" : "down";
      }
      prevPrices[stock.symbol] = { price: update.price };
      lastRealPriceRef.current[stock.symbol] = update.price;
      const nextUpdated = update?.timestamp || timestamp || stock.last_updated;
      return { ...stock, ...update, last_updated: nextUpdated, changed };
    });

    setAllStocks((prev) => applyToList(prev));
    setDisplayedStocks((prev) => applyToList(prev));
    prevPricesRef.current = prevPrices;

    const ts = timestamp ? new Date(timestamp) : new Date();
    setLastUpdated(ts.toLocaleTimeString());
    setLastUpdatedPulse(true);
    if (lastUpdatedTimerRef.current) {
      clearTimeout(lastUpdatedTimerRef.current);
    }
    lastUpdatedTimerRef.current = setTimeout(() => {
      setLastUpdatedPulse(false);
    }, 800);
  }, []);

  const fetchStocks = useCallback(async () => {
    let previousStocksCache = {};
    try {
      setIsLiveLoading(true);
      const categoryType = getCategoryType(initialQuery);
      const params = {};
      if (sectorFilter) params.sector = sectorFilter;
      if (stockLimit) params.limit = stockLimit;

      const res = await api.get("/api/stocks", { params });
      let data = Array.isArray(res.data) ? res.data : [];
      if (!sectorFilter && categoryType) {
        data = applyCategoryFilter(data, categoryType);
      }

      setAllStocks(data);
      previousStocksCache = Object.fromEntries(data.map((s) => [s.symbol, s]));
      setPreviousStocks(previousStocksCache);
      prevPricesRef.current = Object.fromEntries(data.map((s) => [s.symbol, { price: s.price }]));
      setDisplayedStocks(data);
      setStats({ total: data.length, time: 0, query: sectorFilter || initialQuery || "All Stocks" });
      setLastUpdated(new Date().toLocaleTimeString());
      try {
        localStorage.setItem(categoryCacheKey, JSON.stringify(data));
      } catch {}
      setLastUpdatedPulse(true);
      if (lastUpdatedTimerRef.current) {
        clearTimeout(lastUpdatedTimerRef.current);
      }
      lastUpdatedTimerRef.current = setTimeout(() => {
        setLastUpdatedPulse(false);
      }, 800);
    } catch (err) {
      console.error("Error fetching stocks:", err);
    } finally {
      setIsLiveLoading(false);
      if (!initialLoadDone) setInitialLoadDone(true);
    }
  }, [sectorFilter, stockLimit, initialQuery, getCategoryType, applyCategoryFilter, initialLoadDone]);

  // Fetch stocks initially (category-aware)
  useEffect(() => {
    try {
      const cached = localStorage.getItem(categoryCacheKey);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length) {
          setDisplayedStocks(parsed);
          setStats({ total: parsed.length, time: 0, query: sectorFilter || initialQuery || "All Stocks" });
        }
      }
    } catch {}
    fetchStocks();
    return () => {};
  }, [fetchStocks]);

  // Auto refresh when tab becomes visible again
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        fetchStocks();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [fetchStocks]);

  // 🔍 Perform search - memoized to prevent infinite loops
  const performSearch = useCallback(async (overrideQuery) => {
    const rawQuery = typeof overrideQuery === "string" ? overrideQuery : searchQuery;
    const query = rawQuery.trim();
    
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
          const limitValue = stockLimit ?? allStocks.length;
          const limited = limitValue ? allStocks.slice(0, limitValue) : allStocks;
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
          const filterNorm = (sectorFilter || "").toLowerCase().trim();
          const filtered = allStocks.filter((s) => {
            const sec = (s.sector || "").toLowerCase().trim();
            return sec === filterNorm || sec.includes(filterNorm);
          });
          const limitValue = stockLimit ?? filtered.length;
          const limited = filtered.slice(0, limitValue);
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

      const response = await api.post("/api/search", requestBody);

      if (response.status === 401) {
        onLogout();
        return;
      }

      const data = response.data;

      if (!data.results || data.results.length === 0) {
        // Fallback: if sector selected, try client-side match from live /api/stocks
        if (sectorFilter && allStocks.length > 0) {
          const filterNorm = (sectorFilter || "").toLowerCase().trim();
          const q = query.toLowerCase().trim();
          const terms = q.split(/\s+/).filter(Boolean);
          const filtered = allStocks.filter((s) => {
            const sec = (s.sector || "").toLowerCase().trim();
            const name = (s.company_name || "").toLowerCase();
            const sym = (s.symbol || "").toLowerCase();
            const inSector = sec === filterNorm || sec.includes(filterNorm);
            if (!inSector) return false;
            if (!terms.length) return true;
            return terms.some((t) => name.includes(t) || sym.includes(t));
          });
          const limitValue = stockLimit ?? filtered.length;
          const limited = filtered.slice(0, limitValue);
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
        setDisplayedStocks(normalizeResults(data.results));
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
  }, [searchQuery, sectorFilter, stockLimit, onLogout, allStocks, normalizeResults]);

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
      const categoryType = getCategoryType(initialQuery);
      if (categoryType) {
        setMessage({ text: "Showing live results", type: "success" });
        return;
      }
      if (initialQuery && initialQuery.trim()) {
        // Search by query
        await performSearch(initialQuery);
      } else if (sectorFilter) {
        // For sector pages, don't call backend search; live data effects will populate
        // Show a loading message while waiting for live data
        if (!allStocks.length) {
          setDisplayedStocks([]);
        }
        setStats({ total: 0, time: 0, query: sectorFilter });
        setMessage({ text: "Loading sector data...", type: "info" });
      } else if (!initialQuery && !sectorFilter && allStocks.length > 0) {
        // "All Stocks" - show cached data
        const limitValue = stockLimit ?? allStocks.length;
        const limited = allStocks.slice(0, limitValue);
        setDisplayedStocks(limited);
        setStats({ total: limited.length, time: 0, query: "Showing all stocks" });
      }
    };
    
    triggerSearch();
  }, [initialQuery, sectorFilter, stockLimit, getCategoryType, performSearch, allStocks]);

  // Live search while typing (instant local filter only)
  useEffect(() => {
    const categoryType = getCategoryType(initialQuery);
    if (categoryType && searchQuery.trim() === initialQuery.trim()) {
      return;
    }
    const query = searchQuery.trim();
    if (!query && !sectorFilter) {
      if (allStocks.length > 0) {
        const limited = filterLiveStocks("", "");
        setDisplayedStocks(limited);
        setStats({ total: limited.length, time: 0, query: "Showing all stocks" });
        setMessage({ text: "", type: "" });
      }
      return;
    }

    // Immediate local filter for live results
    if (allStocks.length > 0) {
      const limited = filterLiveStocks(query, sectorFilter);
      setDisplayedStocks(limited);
      setStats({ total: limited.length, time: 0, query: query || sectorFilter });
      setMessage({ text: limited.length ? "Showing live results" : "No results found.", type: limited.length ? "success" : "info" });
    }

    if (!query) return;
  }, [searchQuery, sectorFilter, stockLimit, allStocks, filterLiveStocks, getCategoryType, initialQuery]);

  // HTTP-only live updates (every 5s)
  useEffect(() => {
    if (!initialLoadDone) {
      return () => {};
    }
    const poll = async () => {
      try {
        const res = await api.get("/api/stocks");
        const data = Array.isArray(res.data) ? res.data : [];
        const visibleSet = new Set(visibleSymbolsKey ? visibleSymbolsKey.split(",") : []);
        const updates = data.filter((s) => visibleSet.has(s.symbol));
        applyPriceUpdates(updates, new Date().toISOString());
      } catch (err) {
        console.error("Polling error:", err);
      }
    };
    poll();
    pollingTimerRef.current = setInterval(poll, 5000);
    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    };
  }, [initialLoadDone, visibleSymbolsKey, applyPriceUpdates]);

  // 🎬 Smooth price simulation (every 2.5s - simulates between real updates)
  useEffect(() => {
    if (!initialLoadDone || displayedStocks.length === 0) return;

    const simulatePrices = () => {
      setDisplayedStocks((prevStocks) => {
        return prevStocks.map((stock) => {
          const realPrice = lastRealPriceRef.current[stock.symbol] ?? stock.price;
          const currentDisplayed = simulatedStocks[stock.symbol]?.price ?? stock.price;
          
          // If price hasn't been set in simulation yet, initialize it
          if (!simulatedStocks[stock.symbol]) {
            lastRealPriceRef.current[stock.symbol] = stock.price;
            return stock;
          }

          // If we're already close to real price (within $0.01), jump to it
          const diff = Math.abs(realPrice - currentDisplayed);
          if (diff < 0.01) {
            return { ...stock, price: realPrice };
          }

          // Smooth transition: move 30% of the way closer to real price
          const newPrice = currentDisplayed + (realPrice - currentDisplayed) * 0.3;
          
          // Add small micro-fluctuations (+/- 0.15% random) for realism
          const microFluctuation = realPrice * (Math.random() - 0.5) * 0.003;
          const finalPrice = newPrice + microFluctuation;

          const updated = { ...stock, price: finalPrice };
          setSimulatedStocks((prev) => ({
            ...prev,
            [stock.symbol]: { price: finalPrice },
          }));

          return updated;
        });
      });
    };

    simulationTimerRef.current = setInterval(simulatePrices, 2500);
    return () => {
      if (simulationTimerRef.current) {
        clearInterval(simulationTimerRef.current);
        simulationTimerRef.current = null;
      }
    };
  }, [initialLoadDone, displayedStocks.length, simulatedStocks]);

  // When navigating for "All Stocks", update list after allStocks arrives
  useEffect(() => {
    if (!initialQuery && !sectorFilter && allStocks.length > 0) {
      const limitValue = stockLimit ?? allStocks.length;
      const limited = allStocks.slice(0, limitValue);
      setDisplayedStocks(limited);
      setStats({ total: limited.length, time: 0, query: "Showing all stocks" });
    }
  }, [allStocks, initialQuery, sectorFilter, stockLimit]);

  // When navigating for a sector, populate from live stocks once available
  useEffect(() => {
    if (sectorFilter && allStocks.length > 0 && !searchQuery.trim()) {
      const filterNorm = (sectorFilter || "").toLowerCase().trim();
      const filtered = allStocks.filter((s) => {
        const sec = (s.sector || "").toLowerCase().trim();
        return sec === filterNorm || sec.includes(filterNorm);
      });
      const limitValue = stockLimit ?? filtered.length;
      const limited = filtered.slice(0, limitValue);
      if (limited.length > 0) {
        setDisplayedStocks(limited);
        setStats({ total: limited.length, time: 0, query: sectorFilter });
        setMessage({ text: "", type: "" });
      }
    }
  }, [allStocks, sectorFilter, stockLimit, searchQuery]);

  // Cleanup all timers on unmount
  useEffect(() => {
    return () => {
      if (lastUpdatedTimerRef.current) clearTimeout(lastUpdatedTimerRef.current);
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
      if (simulationTimerRef.current) clearInterval(simulationTimerRef.current);
    };
  }, []);

  const handleLogoutClick = async () => {
    try {
      await api.post("/api/logout");
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black flex flex-col relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                          linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}></div>
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/10 to-indigo-500/5 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-purple-500/5 to-cyan-500/5 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full h-64 bg-gradient-to-r from-transparent via-cyan-500/5 to-transparent"></div>
      </div>

      {/* Header */}
      <header className="relative z-50 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Left: Back + Brand */}
          <div className="flex items-center space-x-4">
            {onBackToHome && (
              <button
                onClick={onBackToHome}
                className="flex items-center space-x-2 text-gray-300 hover:text-white bg-gray-800/60 hover:bg-gray-800 px-4 py-2.5 rounded-xl transition-all duration-300 border border-gray-700 hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/10 backdrop-blur-sm"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="font-medium">Back to Dashboard</span>
              </button>
            )}
            <div className="flex items-center space-x-3 group cursor-pointer">
              <div className="relative w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/30 group-hover:shadow-xl group-hover:shadow-cyan-500/40 transition-all duration-300 group-hover:scale-105">
                <span className="text-white font-bold text-lg">S</span>
                <div className="absolute inset-0 rounded-xl border border-cyan-400/30"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">StockSearch</h1>
                <p className="text-xs text-gray-400">Market Intelligence</p>
              </div>
            </div>
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu((s) => !s)}
              className="flex items-center space-x-3 bg-gray-800/60 hover:bg-gray-800 px-4 py-2.5 rounded-xl border border-gray-700 transition-all duration-200 hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/10"
            >
              <div className="relative w-9 h-9 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white font-semibold text-sm shadow-md">
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

      {/* Main Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 relative z-10">
        {/* Search Section */}
        <div className="mb-12">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={(e) => { e.preventDefault(); }} className="mb-6">
              <div className="relative flex items-center bg-gray-800/60 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700 hover:border-cyan-500/50 transition-all duration-300 overflow-hidden group">
                <div className="pl-6 text-gray-400 group-hover:text-cyan-400 transition-colors">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
                  className="flex-1 px-6 py-5 text-lg outline-none bg-transparent text-gray-100 placeholder-gray-500 focus:placeholder-gray-400 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => performSearch(searchQuery)}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-10 py-5 font-semibold transition-all duration-500 flex items-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed group/btn"
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
                  <div className="px-4 py-2 bg-gray-800/60 rounded-xl border border-gray-700 text-sm text-gray-300">
                    Found <span className="font-semibold text-gray-100">{stats.total}</span> results for{" "}
                    <span className="font-semibold text-cyan-400">"{stats.query}"</span>
                    {stats.time > 0 && <span> in {stats.time.toFixed(2)}s</span>}
                  </div>
                )}
                
                {isLiveLoading && (
                  <div className="flex items-center space-x-2 px-4 py-2 bg-gray-800/60 rounded-xl border border-cyan-500/30 text-sm text-cyan-400">
                    <div className="w-3 h-3 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin"></div>
                    <span>Updating live data...</span>
                  </div>
                )}
              </div>

              {lastUpdated && (
                <div className={`px-4 py-2 bg-gray-800/60 backdrop-blur-sm rounded-xl border text-sm text-gray-400 transition-all duration-300 ${
                  lastUpdatedPulse ? "border-cyan-400/70 shadow-[0_0_18px_rgba(34,211,238,0.45)]" : "border-gray-700"
                }`}>
                  Last updated: <span className="font-semibold text-gray-200">{lastUpdated}</span>
                </div>
              )}
            </div>

            {message.text && (
              <div className={`mt-6 p-5 rounded-2xl border backdrop-blur-sm ${
                message.type === 'success' 
                  ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300' 
                  : message.type === 'error'
                  ? 'bg-red-900/20 border-red-500/30 text-red-300'
                  : 'bg-cyan-900/20 border-cyan-500/30 text-cyan-300'
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    message.type === 'success' ? 'bg-emerald-900/30' : 
                    message.type === 'error' ? 'bg-red-900/30' : 'bg-cyan-900/30'
                  }`}>
                    <svg className={`w-5 h-5 ${
                      message.type === 'success' ? 'text-emerald-400' : 
                      message.type === 'error' ? 'text-red-400' : 'text-cyan-400'
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
              <h2 className="text-3xl font-bold text-gray-100 mb-2">Market Overview</h2>
              <p className="text-gray-400">Browse real-time stock data and insights</p>
            </div>
            <div className="px-4 py-2 bg-cyan-900/20 rounded-xl border border-cyan-500/30 text-sm text-cyan-400 font-medium">
              ⚡ Real-time Data
            </div>
          </div>

          {displayedStocks.length === 0 ? (
            <div className="text-center py-16 bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700 shadow-lg">
              <div className="w-20 h-20 mx-auto mb-6 text-gray-600">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-gray-400 text-xl mb-2">
                {sectorFilter
                  ? isLiveLoading
                    ? "Loading sector data..."
                    : "No stocks found in this sector."
                  : "No stocks match your search criteria."}
              </p>
              <p className="text-gray-500 text-sm">Try a different search term or explore other sectors</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {displayedStocks.map((stock) => (
                <div
                  key={stock.symbol || stock.id || Math.random()}
                  onClick={() => setSelectedStock(stock.symbol)}
                >
                  <StockCard stock={stock} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="relative bg-gray-900/50 backdrop-blur-sm border-t border-gray-800/50 py-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="text-center md:text-left">
              <div className="flex items-center space-x-3 mb-2 justify-center md:justify-start">
                <div className="w-6 h-6 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xs">S</span>
                </div>
                <span className="text-lg font-semibold text-gray-100">StockSearch Pro</span>
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

export default Dashboard;
