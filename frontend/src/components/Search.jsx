import React, { useState, useEffect } from "react";

const Search = ({ username, onLogout }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, time: 0, query: "" });
  const [showWelcome, setShowWelcome] = useState(true);
  const [message, setMessage] = useState({ text: "", type: "" });


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
      const response = await fetch("http://localhost:5000/search", {
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

  const handleQuickSearch = (query) => {
    setSearchQuery(query);
    setTimeout(() => performSearch(), 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      performSearch();
    }
  };

  const handleLogoutClick = async () => {
    try {
      await fetch("http://localhost:5000/logout", {
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
          <i className="fas fa-search"></i> SearchEngine
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

      {/* Navigation */}
      <nav className="bg-gray-800 px-6 py-3 border-b border-gray-700">
        <ul className="flex gap-8 text-gray-300">
          <li>
            <button className="hover:text-white transition-colors">
              Bookmarks
            </button>
          </li>
          <li>
            <button className="hover:text-white transition-colors">
              Search
            </button>
          </li>
          <li>
            <button className="hover:text-white transition-colors">
              Categories
            </button>
          </li>
        </ul>
      </nav>

      {/* Header with Search */}
      <header className="bg-gradient-to-br from-gray-700 to-gray-900 text-white py-12 px-4 border-b border-gray-600">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-8 flex items-center justify-center gap-3">
            <i className="fas fa-search"></i> SearchEngine
          </h1>
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden flex">
              <input
                type="text"
                className="flex-1 px-6 py-4 text-gray-900 outline-none"
                placeholder="Enter your search query..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button
                onClick={performSearch}
                className="bg-gray-700 hover:bg-gray-600 px-8 py-4 text-white font-semibold transition-colors"
              >
                <i className="fas fa-search"></i>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4">
    
        {/* Loading */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="w-10 h-10 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Searching...</p>
          </div>
        )}

        {/* Stats */}
        {stats.total > 0 && (
          <div className="text-gray-600 text-lg mb-6">
            Found {stats.total} results for "{stats.query}"
          </div>
        )}

        {/* Results */}
        <div className="space-y-6">
          {showWelcome && !isLoading && (
            <div className="text-center py-16">
              <i className="fas fa-search text-6xl text-gray-400 mb-6"></i>
              <h2 className="text-3xl font-bold text-gray-700 mb-4">
                Search Engine
              </h2>
              <p className="text-gray-500 text-lg">
                Enter a query above to find relevant documents
              </p>
            </div>
          )}

          {!showWelcome && searchResults.length === 0 && !isLoading && (
            <div className="text-center py-16">
              <i className="fas fa-search text-4xl text-gray-400 mb-4"></i>
              <h3 className="text-2xl font-semibold text-gray-700 mb-2">
                No results found for "{stats.query}"
              </h3>
              <p className="text-gray-500">
                Try different keywords or more general terms
              </p>
            </div>
          )}

          {searchResults.map((result, index) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 transition-all duration-300 hover:shadow-md"
            >
              <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-100">
                <span className="font-semibold text-blue-600">
                  Document {result.doc_id}
                </span>
                <span className="bg-gray-700 text-white px-3 py-1 rounded-full text-sm font-medium">
                  Score: {result.score?.toFixed(4)}
                </span>
              </div>
              <div className="text-gray-700 leading-relaxed">
                <p>{result.preview}</p>
              </div>
            </div>
          ))}
        </div>
      </main>

      <footer class="fixed bottom-0 left-0 w-full bg-gray-800 text-gray-300 text-center py-6 border-t border-gray-700">
        <p>Search Engine &copy; 2023 | Powered by Python & BM25</p>
      </footer>

      {message.text && (
        <div
          className={`fixed top-4 right-4 p-3 rounded-lg z-50 ${
            message.type === "success"
              ? "bg-green-100 text-green-700 border border-green-200"
              : "bg-red-100 text-red-700 border border-red-200"
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
};

export default Search;
