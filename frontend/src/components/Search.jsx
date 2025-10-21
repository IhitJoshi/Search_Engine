import React, { useState, useEffect } from "react";

const Search = ({ username, onLogout }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, time: 0, query: "" });
  const [showWelcome, setShowWelcome] = useState(true);
  const [message, setMessage] = useState({ text: "", type: "" });
  const [stocks, setStocks] = useState([]); // 🟢 new state for stocks

  useEffect(() => {
    fetch("http://localhost:5000/api/stocks")
      .then((res) => res.json())
      .then((data) => {
        console.log("Live stocks:", data);
        setStocks(data); // 🟢 store data
      })
      .catch((err) => console.error("Error fetching stocks:", err));
  }, []);

  const performSearch = async () => {
    const query = searchQuery.trim();

    if (query === "") {
      setMessage({ text: "Please enter a search query", type: "error" });
      return;
    }

    setShowWelcome(false);
    setIsLoading(true);
    setSearchResults([]);

    try {
      const response = await fetch("http://localhost:5000/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ query }),
      });

      if (response.status === 401) {
        onLogout();
        return;
      }

      if (!response.ok) throw new Error("Search failed");

      const data = await response.json();
      displayResults(data, query);
    } catch (error) {
      console.error("Error:", error);
      setMessage({
        text: "Error performing search. Please try again.",
        type: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const displayResults = (data, query) => {
    if (!data.results || data.results.length === 0) {
      setSearchResults([]);
      setStats({ total: 0, time: 0, query });
      return;
    }

    setSearchResults(data.results);
    setStats({
      total: data.results.length,
      time: data.time || 0,
      query,
    });
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
      {/* Top Bar */}
      <div className="bg-gray-900 text-white px-6 py-3 flex justify-between items-center border-b border-gray-700">
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

      {/* Stock Dashboard Section */}
      <main className="max-w-7xl mx-auto py-8 px-4">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          📈 Live Stock Market Overview
        </h2>

        {stocks.length === 0 ? (
          <p className="text-gray-500">Loading latest stock data...</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {stocks.map((stock) => (
              <div
                key={stock.id}
                className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-all"
              >
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-bold text-gray-800">
                    {stock.company_name}
                  </h3>
                  <span
                    className={`px-2 py-1 text-sm font-semibold rounded-full ${
                      stock.change_percent >= 0
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {stock.change_percent
                      ? `${stock.change_percent.toFixed(2)}%`
                      : "—"}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mb-2">{stock.symbol}</p>
                <p className="text-xl font-semibold text-gray-900 mb-2">
                  ${stock.price.toFixed(2)}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  Volume: {stock.volume.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">
                  <span className="font-medium">Sector:</span> {stock.sector}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer className="bg-gray-800 text-gray-300 text-center py-6 border-t border-gray-700">
        <p>Stock Dashboard © 2025 | Powered by Python & React</p>
      </footer>
    </div>
  );
};

export default Search;
