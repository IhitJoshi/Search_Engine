import React, { useCallback, useEffect, useRef, useState } from "react";
import api from "../services/api";
import StockCard from "./StockCard";
import StockDetails from "./StockDetails"; // 👈 import your detailed modal

const QuerySearch = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const debounceRef = useRef(null);

  const runSearch = useCallback(async (queryText) => {
    const q = (queryText || "").trim();
    if (!q) {
      setResults([]);
      setSummary("");
      return;
    }
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

  const handleSearch = async (e) => {
    e.preventDefault();
    runSearch(searchQuery);
  };

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    const q = searchQuery.trim();
    if (!q) {
      setResults([]);
      setSummary("");
      return;
    }
    debounceRef.current = setTimeout(() => {
      runSearch(q);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [searchQuery, runSearch]);

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
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search stocks, symbols, or sectors (e.g., AAPL, Technology, Tesla...)"
            className="flex-1 px-6 py-5 text-lg outline-none bg-transparent text-gray-100 placeholder-gray-500 focus:placeholder-gray-400 transition-colors"
          />
          <button
            type="submit"
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
