import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../config/api";

const menuItems = [
  { key: "overview", label: "Overview" },
  { key: "account", label: "Account" },
  { key: "security", label: "Security" },
];

const Profile = ({ username = "User", onLogout }) => {
  const [active, setActive] = useState("overview");
  const [auth, setAuth] = useState({ logged_in: false, username, email: "" });
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState({ auth: true, stocks: true });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Fix: Proper logout function
  const handleLogout = async () => {
    try {
      const response = await api.post("/api/logout");
      
      if (response.status === 200) {
        console.log("Profile logout successful");
      } else {
        console.error("Profile logout failed:", response.status);
      }
    } catch (error) {
      console.error("Profile logout error:", error);
    } finally {
      // Always clear local storage and call parent logout
      localStorage.removeItem("isAuthenticated");
      localStorage.removeItem("username");
      onLogout();
      navigate('/login');
    }
  };

  // Fetch auth info and stock stats
  useEffect(() => {
    const fetchAuth = async () => {
      try {
        const res = await api.get("/api/auth/check");
        setAuth(res.data);
      } catch (e) {
        setError("Failed to load profile info");
      } finally {
        setLoading((s) => ({ ...s, auth: false }));
      }
    };

    const fetchStocks = async () => {
      try {
        const res = await api.get("/api/stocks");
        setStocks(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        setError((prev) => prev || "Failed to load stock stats");
      } finally {
        setLoading((s) => ({ ...s, stocks: false }));
      }
    };

    fetchAuth();
    fetchStocks();
  }, []);

  const sectorBreakdown = useMemo(() => {
    const map = new Map();
    for (const s of stocks) {
      const key = s.sector || "Unknown";
      map.set(key, (map.get(key) || 0) + 1);
    }
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  }, [stocks]);

  const lastUpdated = useMemo(() => {
    if (!stocks.length) return "—";
    const latestISO = stocks.reduce((acc, s) => (new Date(acc) > new Date(s.last_updated) ? acc : s.last_updated), stocks[0].last_updated);
    return latestISO ? new Date(latestISO).toISOString().replace("T", " ").slice(0, 19) : "—";
  }, [stocks]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                          linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}></div>
        
        {/* Animated trading chart lines */}
        <div className="absolute top-1/4 left-0 w-full h-48">
          <svg width="100%" height="100%" className="opacity-10">
            <path d="M0,80 Q200,40 400,100 T800,60 T1200,120 L1600,80" 
                  stroke="#3b82f6" strokeWidth="2" fill="none" className="animate-pulse"/>
            <path d="M0,140 Q200,100 400,160 T800,120 T1200,180 L1600,140" 
                  stroke="#10b981" strokeWidth="2" fill="none" className="animate-pulse delay-300"/>
          </svg>
        </div>

        {/* Glowing orbs */}
        <div className="absolute top-20 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header */}
      <header className="relative z-20 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Brand */}
          <div className="flex items-center space-x-3 group cursor-pointer" onClick={() => navigate("/home")}>
            <div className="relative w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/30 group-hover:shadow-xl group-hover:shadow-cyan-500/40 transition-all duration-300 group-hover:scale-105">
              <span className="text-white font-bold text-lg">S</span>
              <div className="absolute inset-0 rounded-lg border border-cyan-400/30"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                StockSearch
              </h1>
              <p className="text-xs text-gray-400">Profile Management</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate("/home")}
              className="flex items-center space-x-2 text-gray-300 hover:text-white bg-gray-800/60 hover:bg-gray-800 px-4 py-2.5 rounded-xl transition-all duration-300 border border-gray-700 hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/10"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span className="font-medium">Dashboard</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-80 flex-shrink-0 relative z-10">
            <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700/50 p-6 sticky top-8">
              {/* User Profile Card */}
              <div className="text-center mb-8">
                <div className="relative w-24 h-24 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center text-white text-3xl font-bold mx-auto mb-4 shadow-lg shadow-cyan-500/30">
                  {(auth.username || username || "U").charAt(0).toUpperCase()}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-3 border-gray-900 flex items-center justify-center">
                    <svg className="w-3 h-3 text-gray-900" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-xl font-bold text-gray-100 mb-1">{auth.username || username}</h2>
                <p className="text-gray-400 text-sm mb-3">{auth.email || "Premium Trading Account"}</p>
                <div className="inline-flex items-center space-x-1 bg-gradient-to-r from-cyan-900/20 to-blue-900/20 text-cyan-400 px-3 py-1.5 rounded-full text-xs font-medium border border-cyan-500/20">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Verified Trader</span>
                </div>
              </div>

              {/* Navigation Menu */}
              <nav className="space-y-2">
                {menuItems.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setActive(item.key)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-300 group ${
                      active === item.key
                        ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-300 shadow-lg shadow-cyan-500/10"
                        : "text-gray-400 hover:bg-gray-700/50 hover:text-gray-200 hover:shadow-md border border-transparent"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      active === item.key ? "bg-cyan-400" : "bg-gray-600 group-hover:bg-cyan-500"
                    }`}></div>
                    <span className="font-medium">{item.label}</span>
                    <svg className={`w-4 h-4 ml-auto transition-transform duration-300 ${
                      active === item.key ? "rotate-0 text-cyan-400" : "-rotate-90 text-gray-500"
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </nav>

              {/* Logout Button */}
              <div className="mt-8 pt-6 border-t border-gray-700/50">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-3.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl border border-red-500/20 hover:border-red-400/30 transition-all duration-300 font-medium hover:shadow-md group"
                >
                  <svg className="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          </aside>

          {/* Main Content Panel */}
          <main className="flex-1 relative z-10">
            <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700/50 p-8">
              {error && (
                <div className="mb-6 p-4 rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-900/20 to-yellow-900/20 text-amber-300 text-sm flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-amber-900/30 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span>{error}</span>
                </div>
              )}

              {active === "overview" && (
                <div className="space-y-8 animate-fade-in">
                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Account Card */}
                    <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-cyan-500/20 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                      <div className="flex items-center space-x-4">
                        <div className="relative w-14 h-14 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white font-semibold text-xl shadow-md">
                          {(auth.username || username || "U").charAt(0).toUpperCase()}
                          <div className="absolute inset-0 rounded-full border-2 border-white/10"></div>
                        </div>
                        <div>
                          <p className="text-sm text-cyan-400 font-medium">Account</p>
                          <p className="text-lg font-bold text-gray-100 truncate">{auth.username || username}</p>
                          <p className="text-xs text-gray-400 mt-1">Active Trader</p>
                        </div>
                      </div>
                    </div>

                    {/* Stocks Summary */}
                    <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-400 font-medium">Tracked Stocks</p>
                          <p className="text-3xl font-bold text-gray-100 mt-2">
                            {loading.stocks ? (
                              <div className="w-24 h-8 bg-gray-700 rounded-xl animate-pulse"></div>
                            ) : (
                              stocks.length.toLocaleString()
                            )}
                          </p>
                        </div>
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-900/30 to-cyan-900/30 flex items-center justify-center shadow-md">
                          <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-3">Last updated: {lastUpdated}</p>
                    </div>

                    {/* Sectors Summary */}
                    <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                      <p className="text-sm text-gray-400 font-medium mb-4">Top Sectors</p>
                      <div className="space-y-3">
                        {(loading.stocks ? Array(3).fill(null) : sectorBreakdown.slice(0, 3)).map((sector, index) => (
                          <div key={sector?.[0] || index} className="flex items-center justify-between group">
                            <div className="flex items-center space-x-3">
                              <div className={`w-2 h-2 rounded-full ${index === 0 ? 'bg-cyan-500' : index === 1 ? 'bg-blue-400' : 'bg-gray-500'}`}></div>
                              <span className="text-sm text-gray-300 truncate flex-1">
                                {loading.stocks ? (
                                  <div className="w-24 h-4 bg-gray-700 rounded animate-pulse"></div>
                                ) : (
                                  sector[0]
                                )}
                              </span>
                            </div>
                            <span className="text-sm font-semibold text-gray-100 bg-gray-700 px-2.5 py-1 rounded-lg group-hover:bg-gray-600 transition-colors">
                              {loading.stocks ? (
                                <div className="w-8 h-4 bg-gray-700 rounded animate-pulse"></div>
                              ) : (
                                sector[1]
                              )}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Recent Prices Table */}
                  <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-xl font-bold text-gray-100">Market Overview</h3>
                        <p className="text-sm text-gray-400 mt-1">Real-time stock performance</p>
                      </div>
                      <button
                        onClick={async () => {
                          setLoading((s) => ({ ...s, stocks: true }));
                          try {
                            const res = await api.get("/api/stocks");
                            setStocks(Array.isArray(res.data) ? res.data : []);
                          } finally {
                            setLoading((s) => ({ ...s, stocks: false }));
                          }
                        }}
                        className="flex items-center space-x-2 px-4 py-2.5 rounded-lg border border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 transition-all duration-300 hover:shadow-md group"
                      >
                        <svg className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span className="font-medium">Refresh Data</span>
                      </button>
                    </div>
                    
                    <div className="overflow-hidden rounded-xl border border-gray-700/50">
                      <table className="w-full text-sm">
                        <thead className="bg-gradient-to-r from-gray-800 to-gray-900/50">
                          <tr>
                            <th className="px-4 py-3 text-left font-semibold text-gray-300">Symbol</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-300">Company</th>
                            <th className="px-4 py-3 text-right font-semibold text-gray-300">Price</th>
                            <th className="px-4 py-3 text-right font-semibold text-gray-300">Change</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-300">Sector</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700/50">
                          {(loading.stocks ? Array(5).fill(null) : stocks.slice(0, 10)).map((stock, index) => (
                            <tr key={stock?.symbol || index} className="hover:bg-gray-700/30 transition-colors group">
                              <td className="px-4 py-3 font-semibold text-gray-100">
                                {loading.stocks ? (
                                  <div className="w-12 h-4 bg-gray-700 rounded animate-pulse"></div>
                                ) : (
                                  <span className="group-hover:text-cyan-300 transition-colors">{stock.symbol}</span>
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-300 max-w-[200px] truncate">
                                {loading.stocks ? (
                                  <div className="w-32 h-4 bg-gray-700 rounded animate-pulse"></div>
                                ) : (
                                  stock.company_name
                                )}
                              </td>
                              <td className="px-4 py-3 text-right font-semibold text-gray-100">
                                {loading.stocks ? (
                                  <div className="w-16 h-4 bg-gray-700 rounded animate-pulse ml-auto"></div>
                                ) : (
                                  stock.price != null ? `$${Number(stock.price).toFixed(2)}` : "—"
                                )}
                              </td>
                              <td className={`px-4 py-3 text-right font-semibold ${
                                stock?.change_percent >= 0 ? "text-emerald-400" : "text-red-400"
                              }`}>
                                {loading.stocks ? (
                                  <div className="w-12 h-4 bg-gray-700 rounded animate-pulse ml-auto"></div>
                                ) : (
                                  <div className="flex items-center justify-end space-x-1">
                                    <svg className={`w-3 h-3 ${stock.change_percent >= 0 ? 'text-emerald-500' : 'text-red-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      {stock.change_percent >= 0 ? (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                                      ) : (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                                      )}
                                    </svg>
                                    <span>{stock.change_percent != null ? `${Number(stock.change_percent).toFixed(2)}%` : "—"}</span>
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-3">
                                {loading.stocks ? (
                                  <div className="w-20 h-4 bg-gray-700 rounded animate-pulse"></div>
                                ) : (
                                  <span className="inline-block px-2.5 py-1 text-xs rounded-full bg-gray-700 text-gray-300">
                                    {stock.sector || "—"}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {active === "account" && (
                <AccountPanel auth={auth} username={username} onLogout={onLogout} />
              )}

              {active === "security" && (
                <SecurityPanel auth={auth} username={username} onLogout={onLogout} />
              )}
            </div>
          </main>
        </div>
      </div>

      {/* Add custom animation styles */}
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.4s ease-out;
        }
      `}</style>
    </div>
  );
};

// Account Panel Component
function AccountPanel({ auth, username, onLogout }) {
  const [isEditingEmail, setIsEditingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState(auth.email || "");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEmailUpdate = async () => {
    if (!newEmail) {
      setMessage("Email cannot be empty");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/api/auth/update-email", { email: newEmail });
      const data = res.data;

      if (res.status === 200) {
        setMessage("Email updated successfully");
        auth.email = newEmail;
        setIsEditingEmail(false);
        setTimeout(() => setMessage(""), 3000);
      } else {
        setMessage(data.error || "Failed to update email");
      }
    } catch (e) {
      setMessage("Error updating email");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-2">Account Settings</h2>
        <p className="text-gray-400">Manage your account information</p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-sm font-medium backdrop-blur-sm ${
          message.includes("successfully")
            ? "bg-gradient-to-r from-emerald-900/20 to-green-900/20 text-emerald-300 border border-emerald-700/30"
            : "bg-gradient-to-r from-red-900/20 to-rose-900/20 text-red-300 border border-red-700/30"
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              message.includes("successfully") ? 'bg-emerald-900/30' : 'bg-red-900/30'
            }`}>
              <svg className={`w-4 h-4 ${message.includes("successfully") ? 'text-emerald-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {message.includes("successfully") ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </div>
            <span>{message}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Profile Information */}
        <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-900/30 to-blue-900/30 flex items-center justify-center">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <span>Profile Information</span>
          </h3>
          <div className="space-y-5">
            <div className="group">
              <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">Username</label>
              <div className="relative">
                <input 
                  disabled 
                  value={auth.username || username || ""} 
                  className="w-full px-4 py-3.5 bg-gray-900/50 border border-gray-700 rounded-xl text-gray-300 focus:outline-none group-hover:bg-gray-900/70 transition-colors"
                />
                <div className="absolute right-3 top-3.5 text-gray-500">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="group">
              <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">Email Address</label>
              {isEditingEmail ? (
                <div className="space-y-3">
                  <input 
                    type="email"
                    value={newEmail} 
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="w-full px-4 py-3.5 bg-gray-900/50 border border-cyan-500/50 rounded-xl text-gray-100 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-200"
                    placeholder="Enter new email"
                  />
                  <div className="flex gap-3">
                    <button
                      onClick={handleEmailUpdate}
                      disabled={loading}
                      className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-800 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg"
                    >
                      {loading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                          <span>Saving...</span>
                        </div>
                      ) : "Save Changes"}
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingEmail(false);
                        setNewEmail(auth.email || "");
                      }}
                      className="flex-1 px-4 py-3 border border-gray-600 text-gray-300 hover:bg-gray-700/50 hover:border-gray-500 rounded-xl font-medium transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center">
                  <div className="relative flex-1">
                    <input 
                      disabled 
                      value={auth.email || ""} 
                      className="w-full px-4 py-3.5 bg-gray-900/50 border border-gray-700 rounded-xl text-gray-300 focus:outline-none group-hover:bg-gray-900/70 transition-colors"
                    />
                    <div className="absolute right-3 top-3.5 text-gray-500">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsEditingEmail(true)}
                    className="ml-3 px-5 py-3.5 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 hover:border-cyan-400/50 rounded-xl font-medium transition-all duration-300 whitespace-nowrap hover:shadow-md hover:shadow-cyan-500/10"
                  >
                    Edit Email
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Account Type */}
        <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 backdrop-blur-sm rounded-2xl border border-cyan-500/30 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span>Account Type</span>
          </h3>
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-gray-100">Standard Trader</p>
              <p className="text-sm text-gray-400 mt-1">Full market access with real-time data</p>
              <button className="mt-3 px-4 py-2 text-sm bg-gray-800 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 rounded-lg font-medium transition-colors">
                Upgrade Plan
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Sign Out */}
      <div className="bg-gradient-to-br from-red-900/20 to-rose-900/20 backdrop-blur-sm rounded-2xl border border-red-500/30 p-6 shadow-lg hover:shadow-xl transition-all duration-300">
        <h3 className="text-lg font-semibold text-red-300 mb-4 flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-red-900/30 to-rose-900/30 flex items-center justify-center">
            <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </div>
          <span>Sign Out</span>
        </h3>
        <p className="text-red-300 mb-5">Sign out from your account. You can sign back in anytime.</p>
        <button 
          onClick={onLogout}
          className="px-6 py-3.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 text-white rounded-xl font-semibold transition-all duration-300 shadow-md hover:shadow-lg flex items-center space-x-2 group"
        >
          <svg className="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}

// Security Panel Component
function SecurityPanel({ auth, username, onLogout }) {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [passwords, setPasswords] = useState({ current: "", new: "", confirm: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async () => {
    if (!passwords.current || !passwords.new || !passwords.confirm) {
      setMessage("All fields are required");
      return;
    }

    if (passwords.new !== passwords.confirm) {
      setMessage("New passwords do not match");
      return;
    }

    if (passwords.new.length < 6) {
      setMessage("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/api/auth/change-password", {
        current_password: passwords.current,
        new_password: passwords.new,
      });
      const data = res.data;

      if (res.status === 200) {
        setMessage("Password changed successfully");
        setPasswords({ current: "", new: "", confirm: "" });
        setShowPasswordForm(false);
        setTimeout(() => setMessage(""), 3000);
      } else {
        setMessage(data.error || "Failed to change password");
      }
    } catch (e) {
      setMessage("Error changing password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-2">Security Settings</h2>
        <p className="text-gray-400">Manage your account security</p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-sm font-medium backdrop-blur-sm ${
          message.includes("successfully")
            ? "bg-gradient-to-r from-emerald-900/20 to-green-900/20 text-emerald-300 border border-emerald-700/30"
            : "bg-gradient-to-r from-red-900/20 to-rose-900/20 text-red-300 border border-red-700/30"
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              message.includes("successfully") ? 'bg-emerald-900/30' : 'bg-red-900/30'
            }`}>
              <svg className={`w-4 h-4 ${message.includes("successfully") ? 'text-emerald-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {message.includes("successfully") ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </div>
            <span>{message}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Password Security */}
        <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-900/30 to-blue-900/30 flex items-center justify-center">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span>Password Security</span>
          </h3>
          
          {!showPasswordForm ? (
            <>
              <p className="text-sm text-gray-400 mb-6">Keep your account secure with a strong password.</p>
              <button 
                onClick={() => setShowPasswordForm(true)}
                className="w-full px-4 py-3.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg"
              >
                Change Password
              </button>
            </>
          ) : (
            <div className="space-y-5">
              <div className="group">
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">Current Password</label>
                <input 
                  type="password"
                  value={passwords.current}
                  onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                  className="w-full px-4 py-3.5 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-200 text-gray-100"
                  placeholder="Enter current password"
                />
              </div>
              <div className="group">
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">New Password</label>
                <input 
                  type="password"
                  value={passwords.new}
                  onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                  className="w-full px-4 py-3.5 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-200 text-gray-100"
                  placeholder="Enter new password"
                />
              </div>
              <div className="group">
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">Confirm New Password</label>
                <input 
                  type="password"
                  value={passwords.confirm}
                  onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                  className="w-full px-4 py-3.5 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-200 text-gray-100"
                  placeholder="Confirm new password"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handlePasswordChange}
                  disabled={loading}
                  className="flex-1 px-4 py-3.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-800 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg"
                >
                  {loading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Updating...</span>
                    </div>
                  ) : "Update Password"}
                </button>
                <button
                  onClick={() => {
                    setShowPasswordForm(false);
                    setPasswords({ current: "", new: "", confirm: "" });
                  }}
                  className="flex-1 px-4 py-3.5 border border-gray-600 text-gray-300 hover:bg-gray-700/50 hover:border-gray-500 rounded-xl font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Session Management */}
        <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-gray-700 to-gray-800 flex items-center justify-center">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </div>
            <span>Active Session</span>
          </h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-gray-800 to-gray-900/50 rounded-xl border border-gray-700/50">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-900/30 to-blue-900/30 flex items-center justify-center">
                <span className="text-cyan-400 font-semibold text-sm">{(auth.username || username || "U").charAt(0).toUpperCase()}</span>
              </div>
              <div>
                <p className="font-medium text-gray-100">{auth.username || username}</p>
                <p className="text-sm text-gray-400">Currently active</p>
              </div>
            </div>
            <button 
              onClick={onLogout}
              className="w-full px-4 py-3.5 border border-red-500/20 text-red-400 hover:bg-red-500/10 hover:border-red-400/30 rounded-xl font-medium transition-all duration-300 hover:shadow-md hover:shadow-red-500/10"
            >
              Sign Out All Sessions
            </button>
          </div>
        </div>
      </div>

      {/* Security Status */}
      <div className="bg-gradient-to-br from-emerald-900/20 to-green-900/20 backdrop-blur-sm rounded-2xl border border-emerald-500/30 p-6 shadow-lg hover:shadow-xl transition-all duration-300">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-r from-emerald-900/30 to-green-900/30 flex items-center justify-center shadow-md">
            <svg className="w-7 h-7 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-100">Account Secure</h3>
            <p className="text-sm text-gray-400 mt-1">Your account is protected with strong security measures</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
