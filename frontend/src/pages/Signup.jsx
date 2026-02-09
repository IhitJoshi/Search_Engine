import React, { useState } from 'react';
import api from "../services/api";

const Signup = ({ onSignupSuccess, onNavigateToLogin }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { username, email, password, confirmPassword } = formData;

    if (!username || !email || !password) {
      setMessage({ text: 'Please fill in all fields.', type: 'error' });
      return;
    }

    if (password !== confirmPassword) {
      setMessage({ text: 'Passwords do not match.', type: 'error' });
      return;
    }

    if (password.length < 3) {
      setMessage({ text: 'Password must be at least 3 characters.', type: 'error' });
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post("/api/signup", { 
        username: username.trim(), 
        email: email.trim(),
        password: password.trim() 
      });

      const data = response.data;

      if (response.status === 200 || response.status === 201) {
        setMessage({ text: 'Account created successfully! Please login.', type: 'success' });
        setTimeout(() => {
          onSignupSuccess();
        }, 2000);
      } else {
        setMessage({ text: data.error || "Registration failed", type: 'error' });
      }
    } catch (error) {
      console.error("Signup error:", error);
      const errorMsg = error.response?.data?.error || 'Cannot connect to server. Please try again later.';
      setMessage({ text: errorMsg, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black flex items-center justify-center px-4 py-6 overflow-hidden relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                          linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}></div>
        
        {/* Animated trading chart lines */}
        <div className="absolute top-1/3 left-0 w-full h-48">
          <svg width="100%" height="100%" className="opacity-10">
            <path d="M0,80 Q150,40 300,100 T600,60 T900,120 L1200,80" 
                  stroke="#3b82f6" strokeWidth="2" fill="none" className="animate-pulse"/>
            <path d="M0,140 Q150,100 300,160 T600,120 T900,180 L1200,140" 
                  stroke="#10b981" strokeWidth="2" fill="none" className="animate-pulse delay-300"/>
          </svg>
        </div>

        {/* Glowing orbs */}
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="max-w-md w-full space-y-8 relative z-10">
        {/* Header Section */}
        <div className="text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="relative w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <span className="text-white font-bold text-xl">S</span>
              <div className="absolute inset-0 rounded-xl border border-cyan-400/30"></div>
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">StockSearch</h1>
              <p className="text-gray-400 text-lg mt-1">Start your trading journey today</p>
            </div>
          </div>
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800/50 backdrop-blur-sm rounded-full border border-cyan-500/20 mb-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-cyan-400">SECURE REGISTRATION</span>
          </div>
        </div>

        {/* Signup Card */}
        <div className="bg-gray-800/40 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-700/50 overflow-hidden transform transition-all duration-500 hover:shadow-cyan-500/10">
          <div className="p-10">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-gray-100 mb-3">Create Account</h2>
              <p className="text-gray-400 text-lg">Join thousands of traders using our platform</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Username Field */}
              <div className="group">
                <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-3 ml-1">
                  Username
                </label>
                <div className="relative">
                  <input 
                    id="username"
                    type="text" 
                    name="username"
                    className="w-full px-5 py-4 border border-gray-600/50 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 bg-gray-700/50 text-gray-100 placeholder-gray-500 hover:bg-gray-700/70 shadow-sm group-hover:shadow-md"
                    placeholder="Choose a username"
                    value={formData.username}
                    onChange={handleInputChange}
                    required
                    disabled={isLoading}
                  />
                  <div className="absolute right-4 top-4 text-gray-500 group-hover:text-cyan-400 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Email Field */}
              <div className="group">
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-3 ml-1">
                  Email Address
                </label>
                <div className="relative">
                  <input 
                    id="email"
                    type="email" 
                    name="email"
                    className="w-full px-5 py-4 border border-gray-600/50 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 bg-gray-700/50 text-gray-100 placeholder-gray-500 hover:bg-gray-700/70 shadow-sm group-hover:shadow-md"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    disabled={isLoading}
                  />
                  <div className="absolute right-4 top-4 text-gray-500 group-hover:text-cyan-400 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Password Field */}
              <div className="group">
                <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-3 ml-1">
                  Password
                </label>
                <div className="relative">
                  <input 
                    id="password"
                    type="password" 
                    name="password"
                    className="w-full px-5 py-4 border border-gray-600/50 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 bg-gray-700/50 text-gray-100 placeholder-gray-500 hover:bg-gray-700/70 shadow-sm group-hover:shadow-md"
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                    disabled={isLoading}
                  />
                  <div className="absolute right-4 top-4 text-gray-500 group-hover:text-cyan-400 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2 ml-1">Minimum 3 characters required</p>
              </div>

              {/* Confirm Password Field */}
              <div className="group">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-3 ml-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <input 
                    id="confirmPassword"
                    type="password" 
                    name="confirmPassword"
                    className="w-full px-5 py-4 border border-gray-600/50 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 bg-gray-700/50 text-gray-100 placeholder-gray-500 hover:bg-gray-700/70 shadow-sm group-hover:shadow-md"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    required
                    disabled={isLoading}
                  />
                  <div className="absolute right-4 top-4 text-gray-500 group-hover:text-cyan-400 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white py-4 rounded-xl font-semibold hover:from-cyan-600 hover:to-blue-700 transition-all duration-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20 hover:shadow-xl hover:shadow-cyan-500/30 transform hover:-translate-y-1 active:translate-y-0 group mt-6"
              >
                <div className="flex items-center justify-center space-x-3">
                  {isLoading ? (
                    <>
                      <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span className="text-lg">Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-6 h-6 transform group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                      </svg>
                      <span className="text-lg">Create Trading Account</span>
                    </>
                  )}
                </div>
              </button>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-700/50"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-gray-800/40 text-gray-400">Already have an account?</span>
                </div>
              </div>

              {/* Login Link */}
              <div className="text-center">
                <button 
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onNavigateToLogin();
                  }}
                  className="inline-flex items-center space-x-2 px-6 py-3.5 border-2 border-gray-600/50 rounded-xl font-semibold text-gray-300 hover:border-cyan-500/50 hover:text-cyan-400 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  <span>Sign In to Existing Account</span>
                </button>
              </div>
            </form>

            {/* Message Alert */}
            {message.text && (
              <div className={`mt-8 p-5 rounded-xl border backdrop-blur-sm animate-fade-in ${
                message.type === 'success' 
                  ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300' 
                  : 'bg-red-900/20 border-red-500/30 text-red-300'
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    message.type === 'success' ? 'bg-emerald-900/30' : 'bg-red-900/30'
                  }`}>
                    <svg className={`w-5 h-5 ${message.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {message.type === 'success' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      )}
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold">{message.type === 'success' ? 'Success!' : 'Error'}</p>
                    <p className="text-sm mt-1">{message.text}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Security Features */}
        <div className="grid grid-cols-3 gap-4 pt-6">
          <div className="text-center p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/30">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-900/50 to-blue-900/50 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <p className="text-xs font-medium text-gray-400">Secure Data</p>
          </div>
          <div className="text-center p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/30">
            <div className="w-8 h-8 bg-gradient-to-r from-emerald-900/50 to-green-900/50 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-xs font-medium text-gray-400">Real-time Data</p>
          </div>
          <div className="text-center p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/30">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <p className="text-xs font-medium text-gray-400">Verified</p>
          </div>
        </div>
      </div>

      {/* Add custom animation styles */}
      <style>{`
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
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default Signup;
