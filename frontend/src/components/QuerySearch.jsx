import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import StockCard from "./StockCard";

const QuerySearch = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Extract query parameter from URL
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get("query");
    if (q) {
      setQuery(q);
      fetchResults(q);
    }
  }, [location.search]);

  // Fetch from Flask AI Search endpoint
  const fetchResults = async (userQuery) => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await fetch("http://localhost:5000/api/ai_search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQuery }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error("Backend error:", errorText);
        setErrorMsg("Server error. Please try again later.");
        setIsLoading(false);
        return;
      }

      const data = await res.json();
      if (data.error) {
        setErrorMsg(data.error);
        setResults([]);
      } else {
        setResults(data.results || []);
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setErrorMsg("Network or server issue. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/searcx?query=${encodeURIComponent(query)}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      {/* Header / Back Button */}
      <div className="max-w-6xl mx-auto mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">AI Stock Search</h1>
        <button
          onClick={() => navigate("/")}
          className="text-blue-600 hover:text-indigo-700 font-medium"
        >
          ← Back to Home
        </button>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={handleNewSearch}
        className="max-w-3xl mx-auto mb-12 flex items-center bg-white rounded-2xl shadow-md border border-gray-200 hover:border-blue-300 transition-all duration-300 overflow-hidden"
      >
        <div className="pl-6 text-gray-400">
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
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything — e.g., profitable tech companies in USA"
          className="flex-1 px-6 py-5 text-lg outline-none bg-transparent placeholder-gray-400"
        />
        <button
          type="submit"
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-5 font-semibold transition-all duration-300 flex items-center space-x-2"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Searching...</span>
            </>
          ) : (
            <>
              <svg
                className="w-5 h-5"
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
              <span>Search</span>
            </>
          )}
        </button>
      </form>

      {/* Error */}
      {errorMsg && (
        <div className="text-center text-red-600 font-medium bg-red-50 border border-red-200 rounded-xl py-3 px-4 inline-block mx-auto mb-8">
          {errorMsg}
        </div>
      )}

      {/* Results */}
      {isLoading ? (
        <div className="text-center text-gray-600 text-lg">Fetching results...</div>
      ) : results.length > 0 ? (
        <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((stock, index) => (
            <StockCard key={index} stock={stock} />
          ))}
        </div>
      ) : (
        !errorMsg && (
          <div className="text-center text-gray-500 text-lg">
            Type your query above to explore stocks ✨
          </div>
        )
      )}
    </div>
  );
};

export default QuerySearch;
