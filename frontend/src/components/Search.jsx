import React, { useState, useEffect } from "react";
import StockCard from "./StockCard";
import StockDetails from "./StockDetails";

const Search = ({ username, onLogout }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [displayedStocks, setDisplayedStocks] = useState([]);
  const [allStocks, setAllStocks] = useState([]);
  const [previousStocks, setPreviousStocks] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, time: 0, query: "" });
  const [message, setMessage] = useState({ text: "", type: "" });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);

  // 🟢 Fetch stocks initially and every 10 seconds
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/stocks");
        const data = await res.json();

        // Detect price changes for animation
        const updated = data.map((stock) => {
          const prev = previousStocks[stock.symbol];
          const changed =
            prev && prev.price !== stock.price
              ? stock.price > prev.price
                ? "up"
                : "down"
              : null;
          return { ...stock, changed };
        });

        setAllStocks(updated);
        setDisplayedStocks(updated); // show all if not searching
        setPreviousStocks(Object.fromEntries(data.map((s) => [s.symbol, s])));
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.error("Error fetching stocks:", err);
      }
    };

    fetchStocks();
    const interval = setInterval(fetchStocks, 10000);
    return () => clearInterval(interval);
  }, [previousStocks]);

  // 🔍 Perform search
  const performSearch = async () => {
    const query = searchQuery.trim();
    if (query === "") {
      setDisplayedStocks(allStocks);
      setStats({ total: allStocks.length, time: 0, query: "" });
      return;
    }

    setIsLoading(true);
    setMessage({ text: "", type: "" });

    try {
      const response = await fetch("http://localhost:5000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ query }),
      });

      if (response.status === 401) {
        onLogout();
        return;
      }

      const data = await response.json();

      if (!data.results || data.results.length === 0) {
        setDisplayedStocks([]);
        setStats({ total: 0, time: 0, query });
        setMessage({ text: "No results found.", type: "info" });
      } else {
        setDisplayedStocks(data.results);
        setStats({
          total: data.results.length,
          time: data.time || 0,
          query,
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
  <div className="bg-gray-900 text-white px-6 py-3 flex justify-between items-center shadow-lg">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <i className="fas fa-chart-line"></i> Stock Dashboard
        </h1>
        <div className="flex gap-4 items-center">
          <span className="text-gray-300">Welcome, {username}</span>
          <button
            onClick={handleLogoutClick}
            className="text-gray-300 hover:text-white transition-colors flex items-center gap-2"
          >
            <i className="fas fa-sign-out-alt"></i> Logout
          </button>
        </div>
      </div>

      {/* Search Section */}
      <div className="max-w-4xl mx-auto mt-8 px-4">
        <div className="flex gap-3 items-center">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && performSearch()}
            placeholder="🔍 Search for company, sector, or symbol..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
          <button
            onClick={performSearch}
            disabled={isLoading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg transition disabled:opacity-60"
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Stats + Message */}
        <div className="mt-4 text-sm ">
          {stats.query && (
            <p className="text-gray-600">
              Found{" "}
              <span className="font-semibold">{stats.total}</span> results for{" "}
              <span className="font-semibold text-indigo-600">
                “{stats.query}”
              </span>{" "}
              in {stats.time.toFixed(2)}s
            </p>
          )}
          {message.text && (
            <p
              className={`mt-1 ${
                message.type === "error"
                  ? "text-red-600"
                  : message.type === "info"
                  ? "text-gray-600"
                  : "text-green-600"
              }`}
            >
              {message.text}
            </p>
          )}
        </div>
      </div>

      {/* Stocks Section */}
      <main className="max-w-7xl mx-auto py-8 px-4 ">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          📈 Live Stock Market Overview
        </h2>

        <p className="text-gray-500 text-sm mb-6">
          Last updated:{" "}
          <span className="font-medium text-gray-700">
            {lastUpdated || "—"}
          </span>
        </p>

        {displayedStocks.length === 0 ? (
          <p className="text-gray-500">No stock data available.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 ">
            {displayedStocks.map((stock) => (
              <div
  key={stock.symbol}
  onClick={() => setSelectedStock(stock.symbol)} // 🟢 Add this
  className={`rounded-xl p-6 shadow-lg hover:shadow-2xl border transition-all duration-300 transform hover:-translate-y-2 cursor-pointer ${
    stock.changed === "up"
      ? "bg-white border-green-200 hover:border-green-300"
      : stock.changed === "down"
      ? "bg-white border-red-200 hover:border-red-300"
      : "bg-white border-gray-200 hover:border-indigo-300"
  }`}
>
                <StockCard stock={stock} />
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 text-center py-6 border-t border-gray-700 shadow-lg">
        <p>Stock Dashboard © 2025 | Powered by Python & React</p>
      </footer>
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
