import React, { useCallback, useEffect, useState, useRef, useMemo } from "react";
import api from "../services/api";
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
  const wsRef = useRef(null);
  const prevPricesRef = useRef({});
  const visibleSymbolsKey = useMemo(() => (
    results
      .map((s) => s.symbol)
      .filter(Boolean)
      .join(",")
  ), [results]);

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
    const fetchStocks = async () => {
      try {
        setIsLiveLoading(true);
        const res = await api.get("/api/stocks");
        if (isMounted) {
          setAllStocks(Array.isArray(res.data) ? res.data : []);
          prevPricesRef.current = Object.fromEntries(
            (Array.isArray(res.data) ? res.data : []).map((s) => [s.symbol, { price: s.price }])
          );
        }
      } catch (err) {
        console.error("Error fetching live stocks:", err);
      } finally {
        if (isMounted) setIsLiveLoading(false);
      }
    };
    fetchStocks();
    return () => {
      isMounted = false;
    };
  }, []);

  const buildWsUrl = useCallback(() => {
    const base = import.meta.env.VITE_API_URL || window.location.origin;
    const trimmed = base.endsWith("/") ? base.slice(0, -1) : base;
    return trimmed.replace(/^http/, "ws") + "/ws/stocks";
  }, []);

  const applyPriceUpdates = useCallback((updates) => {
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
      return { ...stock, ...update, changed };
    });

    setResults((prev) => applyToList(prev));
    setAllStocks((prev) => applyToList(prev));
    prevPricesRef.current = prevPrices;
  }, []);

  // WebSocket live updates for currently visible results
  useEffect(() => {
    const symbols = visibleSymbolsKey ? visibleSymbolsKey.split(",") : [];

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (!symbols.length) {
      return () => {};
    }

    const ws = new WebSocket(buildWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ symbols }));
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const updates = Array.isArray(payload.stocks) ? payload.stocks : [];
        applyPriceUpdates(updates);
      } catch (err) {
        console.error("WebSocket message error:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [visibleSymbolsKey, buildWsUrl, applyPriceUpdates]);

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
