import React, { useCallback, useEffect, useRef, useState } from "react";
import api from "../services/api";
import { getStockSocket, subscribeSymbols, unsubscribeSymbols } from "../services/stockSocket";
import StockCard from "./StockCard";
import StockDetails from "./StockDetails"; // 👈 import your detailed modal

const QuerySearch = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [allStocks, setAllStocks] = useState([]);
  const [isLiveLoading, setIsLiveLoading] = useState(false);
  const [searchMode, setSearchMode] = useState("live"); // live | ai
  const [lastAiQuery, setLastAiQuery] = useState("");
  const subscribedSymbolsRef = useRef(new Set());
  const changeTimersRef = useRef({});

  const filterLiveStocks = useCallback((queryText) => {
    const q = (queryText || "").toLowerCase().trim();
    if (!q) return [];
    return allStocks.filter((s) => {
      const sym = (s.symbol || "").toLowerCase();
      const name = (s.company_name || "").toLowerCase();
      return sym.startsWith(q) || name.startsWith(q);
    });
  }, [allStocks]);

  useEffect(() => {
    let isMounted = true;
    const socket = getStockSocket();

    const fetchStocks = async () => {
      try {
        setIsLiveLoading(true);
        const res = await api.get("/api/stocks");
        if (!isMounted) return;
        const data = Array.isArray(res.data) ? res.data : [];
        setAllStocks(data.map((s) => ({ ...s, changed: null })));

        const symbols = data.map((s) => s.symbol).filter(Boolean);
        const newSymbols = symbols.filter((s) => !subscribedSymbolsRef.current.has(s));
        if (newSymbols.length > 0) {
          subscribeSymbols(newSymbols, { interval: 5 });
          newSymbols.forEach((s) => subscribedSymbolsRef.current.add(s));
        }
      } catch (err) {
        console.error("Error fetching live stocks:", err);
      } finally {
        if (isMounted) setIsLiveLoading(false);
      }
    };

    fetchStocks();

    const clearChangeTimer = (symbol) => {
      const timer = changeTimersRef.current[symbol];
      if (timer) {
        clearTimeout(timer);
      }
      changeTimersRef.current[symbol] = setTimeout(() => {
        setAllStocks((prev) =>
          prev.map((s) => (s.symbol === symbol ? { ...s, changed: null } : s))
        );
        setResults((prev) =>
          prev.map((s) => (s.symbol === symbol ? { ...s, changed: null } : s))
        );
        delete changeTimersRef.current[symbol];
      }, 1500);
    };

    const handleUpdate = (payload) => {
      if (!payload?.symbol) return;
      setAllStocks((prev) =>
        prev.map((stock) => {
          if (stock.symbol !== payload.symbol) return stock;
          const prevPrice = stock.price;
          const nextPrice = payload.price ?? stock.price;
          let changed = null;
          if (prevPrice != null && nextPrice != null && prevPrice !== nextPrice) {
            changed = nextPrice > prevPrice ? "up" : "down";
          }
          if (changed) {
            clearChangeTimer(stock.symbol);
          }
          return {
            ...stock,
            price: nextPrice,
            change_percent: payload.change_percent ?? stock.change_percent,
            last_updated: payload.last_updated ?? stock.last_updated,
            changed,
          };
        })
      );
      setResults((prev) =>
        prev.map((stock) => {
          if (stock.symbol !== payload.symbol) return stock;
          const prevPrice = stock.price;
          const nextPrice = payload.price ?? stock.price;
          let changed = null;
          if (prevPrice != null && nextPrice != null && prevPrice !== nextPrice) {
            changed = nextPrice > prevPrice ? "up" : "down";
          }
          if (changed) {
            clearChangeTimer(stock.symbol);
          }
          return {
            ...stock,
            price: nextPrice,
            change_percent: payload.change_percent ?? stock.change_percent,
            last_updated: payload.last_updated ?? stock.last_updated,
            changed,
          };
        })
      );
    };

    const handleConnect = () => {
      if (subscribedSymbolsRef.current.size > 0) {
        subscribeSymbols(Array.from(subscribedSymbolsRef.current), { interval: 5 });
      }
    };

    socket.on("stock_update", handleUpdate);
    socket.on("connect", handleConnect);

    return () => {
      isMounted = false;
      socket.off("stock_update", handleUpdate);
      socket.off("connect", handleConnect);
      if (subscribedSymbolsRef.current.size > 0) {
        unsubscribeSymbols(Array.from(subscribedSymbolsRef.current));
      }
      Object.values(changeTimersRef.current).forEach(clearTimeout);
      changeTimersRef.current = {};
    };
  }, []);

  const runSearch = useCallback(async (queryText) => {
    const q = (queryText || "").trim();
    if (!q) {
      setResults([]);
      setSummary("");
      return;
    }
    setSearchMode("ai");
    setLastAiQuery(q);
    setIsSearching(true);
    try {
      const res = await api.post("/api/ai_search", {
        query: q,
      });
      if (res.data.results && res.data.results.length > 0) {
        setResults(res.data.results);
        setSummary(res.data.summary || "");
      } else {
        setResults([]);
        setSummary(
          res.data.summary || `No matching results found for "${q}".`
        );
      }
    } catch (error) {
      console.error("Error:", error);
      setResults([]);
      setSummary("Server error or invalid query.");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    runSearch(searchQuery);
  };

  useEffect(() => {
    const q = searchQuery.trim();
    if (!q) {
      if (searchMode === "live") {
        setResults([]);
        setSummary("");
      }
      return;
    }
    // Only run live filtering while typing.
    if (searchMode !== "live") return;

    const filtered = filterLiveStocks(q);
    setResults(filtered);
    if (filtered.length > 0) {
      setSummary(`Showing ${filtered.length} live result${filtered.length === 1 ? "" : "s"}`);
    } else {
      setSummary("Searching...");
    }
  }, [searchQuery, filterLiveStocks, searchMode]);

  return (
    <div className="px-6">
      {/* 🔍 Search Bar */}
      <form onSubmit={handleSearch} className="max-w-3xl mx-auto mb-12">
        <div className="relative flex items-center bg-gray-800/60 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700 hover:border-cyan-500/50 transition-all duration-300 overflow-hidden group">
          <div className="pl-6 text-gray-400 group-hover:text-cyan-400 transition-colors">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchMode("live");
              setSearchQuery(e.target.value);
            }}
            placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
            className="flex-1 px-6 py-5 text-lg outline-none bg-transparent text-gray-100 placeholder-gray-500 focus:placeholder-gray-400 transition-colors"
          />
          <button
            type="button"
            onClick={() => runSearch(searchQuery)}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-8 py-5 font-semibold transition-all duration-300"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {/* 🧠 Summary */}
      {summary && (
        <p className="text-center text-gray-400 mb-8 transition-all">
          {summary}
        </p>
      )}

      {isLiveLoading && (
        <p className="text-center text-cyan-400 mb-4 text-sm">
          Updating live data...
        </p>
      )}

      {/* 📊 Results */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {results.length > 0 ? (
          results.map((stock, index) => (
            <div
              key={index}
              onClick={() => setSelectedSymbol(stock.symbol)} // 👈 opens StockDetails
              className="cursor-pointer"
            >
              <StockCard stock={stock} />
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500 col-span-full">
            
          </p>
        )}
      </div>

      {/* 📈 Stock Details Modal */}
      {selectedSymbol && (
        <StockDetails
          symbol={selectedSymbol}
          onClose={() => setSelectedSymbol(null)}
        />
      )}
    </div>
  );
};

export default QuerySearch;
