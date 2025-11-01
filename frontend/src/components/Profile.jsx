import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const menuItems = [
  { key: "overview", label: "Overview" },
  { key: "account", label: "Account" },
  { key: "security", label: "Security" },
  { key: "notifications", label: "Notifications" },
];

const Profile = ({ username = "User", onLogout }) => {
  const [active, setActive] = useState("overview");
  const [auth, setAuth] = useState({ logged_in: false, username, email: "" });
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState({ auth: true, stocks: true });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Fetch auth info and stock stats
  useEffect(() => {
    const fetchAuth = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/auth/check", {
          credentials: "include",
        });
        const data = await res.json();
        setAuth(data);
      } catch (e) {
        setError("Failed to load profile info");
      } finally {
        setLoading((s) => ({ ...s, auth: false }));
      }
    };

    const fetchStocks = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/stocks");
        const data = await res.json();
        setStocks(Array.isArray(data) ? data : []);
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">StockSearch</h1>
              <p className="text-sm text-gray-500">Profile Management</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate("/home")}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 px-4 py-2 rounded-lg transition-all duration-200 border border-gray-200"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span className="font-medium">Dashboard</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-80 flex-shrink-0">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              {/* User Profile Card */}
              <div className="text-center mb-8">
                <div className="w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
                  {(auth.username || username || "U").charAt(0).toUpperCase()}
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">{auth.username || username}</h2>
                <p className="text-gray-500 text-sm">{auth.email || "Premium Account"}</p>
                <div className="inline-flex items-center space-x-1 bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-medium mt-2">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
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
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
                      active === item.key
                        ? "bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 text-blue-700"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${
                      active === item.key ? "bg-blue-500" : "bg-gray-300"
                    }`}></div>
                    <span className="font-medium">{item.label}</span>
                  </button>
                ))}
              </nav>

              {/* Logout Button */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={onLogout}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl border border-red-200 transition-all duration-200 font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          </aside>

          {/* Main Content Panel */}
          <main className="flex-1">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              {error && (
                <div className="mb-6 p-4 rounded-lg border border-amber-300 bg-amber-50 text-amber-800 text-sm flex items-center space-x-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              {active === "overview" && (
                <div className="space-y-8">
                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Account Card */}
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-6">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white font-semibold text-lg">
                          {(auth.username || username || "U").charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm text-blue-600 font-medium">Account</p>
                          <p className="text-lg font-bold text-gray-900">{auth.username || username}</p>
                        </div>
                      </div>
                    </div>

                    {/* Stocks Summary */}
                    <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-500 font-medium">Tracked Stocks</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {loading.stocks ? (
                              <div className="w-8 h-6 bg-gray-200 rounded animate-pulse"></div>
                            ) : (
                              stocks.length.toLocaleString()
                            )}
                          </p>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">Last updated: {lastUpdated}</p>
                    </div>

                    {/* Sectors Summary */}
                    <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
                      <p className="text-sm text-gray-500 font-medium mb-3">Top Sectors</p>
                      <div className="space-y-2">
                        {(loading.stocks ? Array(3).fill(null) : sectorBreakdown.slice(0, 3)).map((sector, index) => (
                          <div key={sector?.[0] || index} className="flex items-center justify-between">
                            <span className="text-sm text-gray-700 truncate flex-1">
                              {loading.stocks ? (
                                <div className="w-20 h-4 bg-gray-200 rounded animate-pulse"></div>
                              ) : (
                                sector[0]
                              )}
                            </span>
                            <span className="text-sm font-semibold text-gray-900 bg-gray-100 px-2 py-1 rounded">
                              {loading.stocks ? (
                                <div className="w-6 h-4 bg-gray-200 rounded animate-pulse"></div>
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
                  <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-xl font-bold text-gray-900">Market Overview</h3>
                      <button
                        onClick={async () => {
                          setLoading((s) => ({ ...s, stocks: true }));
                          try {
                            const res = await fetch("http://localhost:5000/api/stocks");
                            const data = await res.json();
                            setStocks(Array.isArray(data) ? data : []);
                          } finally {
                            setLoading((s) => ({ ...s, stocks: false }));
                          }
                        }}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Refresh Data</span>
                      </button>
                    </div>
                    
                    <div className="overflow-hidden rounded-xl border border-gray-200">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Symbol</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Company</th>
                            <th className="px-4 py-3 text-right font-semibold text-gray-700">Price</th>
                            <th className="px-4 py-3 text-right font-semibold text-gray-700">Change</th>
                            <th className="px-4 py-3 text-left font-semibold text-gray-700">Sector</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {(loading.stocks ? Array(5).fill(null) : stocks.slice(0, 10)).map((stock, index) => (
                            <tr key={stock?.symbol || index} className="hover:bg-gray-50 transition-colors">
                              <td className="px-4 py-3 font-semibold text-gray-900">
                                {loading.stocks ? (
                                  <div className="w-12 h-4 bg-gray-200 rounded animate-pulse"></div>
                                ) : (
                                  stock.symbol
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-700 max-w-[200px] truncate">
                                {loading.stocks ? (
                                  <div className="w-32 h-4 bg-gray-200 rounded animate-pulse"></div>
                                ) : (
                                  stock.company_name
                                )}
                              </td>
                              <td className="px-4 py-3 text-right font-semibold text-gray-900">
                                {loading.stocks ? (
                                  <div className="w-16 h-4 bg-gray-200 rounded animate-pulse ml-auto"></div>
                                ) : (
                                  stock.price != null ? `$${Number(stock.price).toFixed(2)}` : "—"
                                )}
                              </td>
                              <td className={`px-4 py-3 text-right font-semibold ${
                                stock?.change_percent >= 0 ? "text-green-600" : "text-red-600"
                              }`}>
                                {loading.stocks ? (
                                  <div className="w-12 h-4 bg-gray-200 rounded animate-pulse ml-auto"></div>
                                ) : (
                                  stock.change_percent != null ? `${Number(stock.change_percent).toFixed(2)}%` : "—"
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {loading.stocks ? (
                                  <div className="w-20 h-4 bg-gray-200 rounded animate-pulse"></div>
                                ) : (
                                  stock.sector || "—"
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

              {active === "notifications" && (
                <NotificationsPanel />
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

// Account Panel Component
function AccountPanel({ auth, username, onLogout }) {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Account Settings</h2>
        <p className="text-gray-600">Manage your account information and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Profile Information */}
        <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
              <input 
                disabled 
                value={auth.username || username || ""} 
                className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
              <input 
                disabled 
                value={auth.email || ""} 
                className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-600"
              />
            </div>
          </div>
        </div>

        {/* Account Type */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Type</h3>
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-gray-900">Premium Trader</p>
              <p className="text-sm text-gray-600">Full market access</p>
            </div>
          </div>
          <button className="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium">
            Upgrade Plan
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-gradient-to-br from-red-50 to-white rounded-2xl border border-red-200 p-6">
        <h3 className="text-lg font-semibold text-red-700 mb-4">Danger Zone</h3>
        <p className="text-red-600 mb-4">Once you sign out, you'll need to sign in again to access your account.</p>
        <button 
          onClick={onLogout}
          className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Security Settings</h2>
        <p className="text-gray-600">Manage your account security and session settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Password Security */}
        <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Password</h3>
          <p className="text-sm text-gray-600 mb-4">Password changes are managed via the authentication service.</p>
          <button disabled className="w-full px-4 py-3 bg-gray-100 text-gray-400 rounded-lg font-medium cursor-not-allowed">
            Change Password
          </button>
        </div>

        {/* Session Management */}
        <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Session</h3>
          <p className="text-sm text-gray-600 mb-4">You're signed in as <span className="font-semibold text-gray-900">{auth.username || username}</span>.</p>
          <button 
            onClick={onLogout}
            className="w-full px-4 py-3 border border-red-200 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors"
          >
            Sign Out All Sessions
          </button>
        </div>
      </div>

      {/* Security Status */}
      <div className="bg-gradient-to-br from-green-50 to-white rounded-2xl border border-green-200 p-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Account Secure</h3>
            <p className="text-sm text-gray-600">Your account is protected and up to date</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Notifications Panel Component
function NotificationsPanel() {
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(false);
  const [newsletter, setNewsletter] = useState(false);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Notification Preferences</h2>
        <p className="text-gray-600">Choose what updates you want to receive</p>
      </div>

      <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 p-6">
        <div className="space-y-6">
          <ToggleRow 
            label="Email Alerts" 
            checked={emailAlerts} 
            onChange={setEmailAlerts} 
            description="Important account and system notifications"
          />
          <ToggleRow 
            label="Price Change Alerts" 
            checked={priceAlerts} 
            onChange={setPriceAlerts} 
            description="Get notified on significant price movements"
          />
          <ToggleRow 
            label="Weekly Newsletter" 
            checked={newsletter} 
            onChange={setNewsletter} 
            description="A weekly summary of market highlights"
          />
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors">
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
}

// Toggle Row Component
function ToggleRow({ label, description, checked, onChange }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex-1">
        <p className="font-semibold text-gray-900">{label}</p>
        {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`w-14 h-8 rounded-full relative transition-colors duration-300 ${
          checked ? "bg-blue-600" : "bg-gray-300"
        }`}
        role="switch"
        aria-checked={checked}
      >
        <span
          className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-lg transition-transform duration-300 ${
            checked ? "translate-x-7" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}

export default Profile;