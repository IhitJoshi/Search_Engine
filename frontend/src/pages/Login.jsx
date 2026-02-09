import React, { useState, useEffect } from 'react';
import api from "../services/api";

const Login = ({ onLoginSuccess, onNavigateToSignup }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    const savedUsername = localStorage.getItem('rememberedUsername');
    if (savedUsername) {
      setFormData(prev => ({ ...prev, username: savedUsername }));
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { username, password } = formData;

    if (!username || !password) {
      setMessage({ text: 'Please fill in all fields.', type: 'error' });
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post("/api/login", { 
        username: username.trim(), 
        password: password.trim() 
      });

      const data = response.data;

      if (response.status === 200) {
        if (rememberMe) {
          localStorage.setItem('rememberedUsername', username);
        } else {
          localStorage.removeItem('rememberedUsername');
        }
        
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('username', username);
        
        setMessage({ text: 'Login successful!', type: 'success' });
        onLoginSuccess(username);
      } else {
        setMessage({ text: data.error || "Invalid credentials", type: 'error' });
      }
    } catch (error) {
      console.error("Login error:", error);
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

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    
    if (!resetEmail) {
      setResetMessage({ text: 'Please enter your email address.', type: 'error' });
      return;
    }

    setResetLoading(true);
    setResetMessage({ text: '', type: '' });

    try {
      await api.post("/api/forgot-password", { email: resetEmail.trim() });

      // Optimistic UX: Treat non-200 as success in development to avoid blocking users
      setResetMessage({ 
        text: 'If that email exists, password reset instructions have been sent.', 
        type: 'success' 
      });
      setTimeout(() => {
        setShowForgotPassword(false);
        setResetEmail('');
        setResetMessage({ text: '', type: '' });
      }, 2000);
    } catch (error) {
      console.error("Forgot password error:", error);
      // Network issues: still show success message to keep flow unblocked
      setResetMessage({ 
        text: 'If that email exists, password reset instructions have been sent.', 
        type: 'success' 
      });
      setTimeout(() => {
        setShowForgotPassword(false);
        setResetEmail('');
        setResetMessage({ text: '', type: '' });
      }, 2000);
    } finally {
      setResetLoading(false);
    }
  };

  const closeForgotPasswordModal = () => {
    setShowForgotPassword(false);
    setResetEmail('');
    setResetMessage({ text: '', type: '' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black flex items-center justify-center px-4 py-8 relative overflow-hidden">
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
              <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                StockSearch
              </h1>
              <p className="text-gray-400 text-lg mt-1">Professional Trading Terminal</p>
            </div>
          </div>
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800/50 backdrop-blur-sm rounded-full border border-cyan-500/20 mb-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-cyan-400">SECURE TRADING ACCESS</span>
          </div>
        </div>

        {/* Login Card */}
        <div className="bg-gray-800/40 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-700/50 overflow-hidden transform transition-all duration-500 hover:shadow-cyan-500/10">
          <div className="p-10">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-gray-100 mb-3">Welcome Back</h2>
              <p className="text-gray-400 text-lg">Access your portfolio and market insights</p>
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
                    className="w-full px-5 py-4 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 text-gray-100 placeholder-gray-500 hover:bg-gray-900/70 hover:border-gray-600"
                    placeholder="Enter your username"
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
                    className="w-full px-5 py-4 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 text-gray-100 placeholder-gray-500 hover:bg-gray-900/70 hover:border-gray-600"
                    placeholder="Enter your password"
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
              </div>

              {/* Options Row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <input 
                    type="checkbox" 
                    id="rememberMe"
                    checked={rememberMe} 
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-5 h-5 accent-cyan-500 cursor-pointer"
                  />
                  <label htmlFor="rememberMe" className="text-sm font-medium text-gray-300 cursor-pointer hover:text-cyan-300 transition-colors">
                    Remember me
                  </label>
                </div>
                <button 
                  type="button" 
                  onClick={() => setShowForgotPassword(true)}
                  className="text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-all duration-300 hover:underline underline-offset-2"
                >
                  Forgot password?
                </button>
              </div>

              {/* Submit Button */}
              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-4 rounded-xl font-semibold hover:from-cyan-700 hover:to-blue-700 transition-all duration-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-1 active:translate-y-0 group"
              >
                <div className="flex items-center justify-center space-x-3">
                  {isLoading ? (
                    <>
                      <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span className="text-lg">Accessing Terminal...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-6 h-6 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                      </svg>
                      <span className="text-lg">Access Trading Dashboard</span>
                    </>
                  )}
                </div>
              </button>

              {/* Google Sign-In Button */}
              <button 
                type="button"
                onClick={() => {
                  const apiUrl = import.meta.env.VITE_API_URL || window.location.origin;
                  window.location.href = `${apiUrl}/api/auth/google/login`;
                }}
                className="w-full bg-white hover:bg-gray-100 text-gray-800 py-4 rounded-xl font-semibold transition-all duration-500 shadow-lg hover:shadow-xl transform hover:-translate-y-1 active:translate-y-0 flex items-center justify-center space-x-3 group"
              >
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span className="text-lg">Sign in with Google</span>
              </button>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-700/50"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-gray-800/40 text-gray-400">New to trading platform?</span>
                </div>
              </div>

              {/* Signup Link */}
              <div className="text-center">
                <button 
                  type="button"
                  onClick={onNavigateToSignup}
                  className="inline-flex items-center space-x-2 px-6 py-3.5 border-2 border-gray-700 rounded-xl font-semibold text-gray-300 hover:border-cyan-500 hover:text-cyan-300 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                  </svg>
                  <span>Create Trading Account</span>
                </button>
              </div>
            </form>

            {/* Message Alert */}
            {message.text && (
              <div className={`mt-8 p-5 rounded-xl border backdrop-blur-sm animate-fade-in ${
                message.type === 'success' 
                  ? 'bg-gradient-to-r from-emerald-900/20 to-green-900/20 border-emerald-700/30 text-emerald-300' 
                  : 'bg-gradient-to-r from-red-900/20 to-rose-900/20 border-red-700/30 text-red-300'
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    message.type === 'success' ? 'bg-emerald-900/30' : 'bg-red-900/30'
                  }`}>
                    <svg className={`w-5 h-5 ${message.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {message.type === 'success' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.342 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      )}
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold">{message.type === 'success' ? 'Access Granted!' : 'Authentication Error'}</p>
                    <p className="text-sm mt-1">{message.text}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-2 gap-4 pt-6">
          <div className="text-center p-4 bg-gray-800/30 backdrop-blur-sm rounded-xl border border-gray-700/30 hover:border-cyan-500/30 transition-colors">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-900/30 to-blue-900/30 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-300">Real-time Data</p>
          </div>
          <div className="text-center p-4 bg-gray-800/30 backdrop-blur-sm rounded-xl border border-gray-700/30 hover:border-emerald-500/30 transition-colors">
            <div className="w-8 h-8 bg-gradient-to-r from-emerald-900/30 to-green-900/30 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-300">Secure Access</p>
          </div>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotPassword && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center px-4 z-50 animate-fade-in" onClick={closeForgotPasswordModal}>
          <div className="bg-gray-800/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-md w-full p-10 transform transition-all duration-300 scale-100" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="text-2xl font-bold text-gray-100">Reset Password</h3>
                <p className="text-gray-400 mt-2">Get back to your trading terminal</p>
              </div>
              <button 
                onClick={closeForgotPasswordModal}
                className="w-10 h-10 rounded-full hover:bg-gray-700/50 flex items-center justify-center transition-colors"
              >
                <svg className="w-6 h-6 text-gray-400 hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleForgotPassword} className="space-y-6">
              <div className="group">
                <label htmlFor="resetEmail" className="block text-sm font-medium text-gray-300 mb-3 ml-1">
                  Email Address
                </label>
                <input 
                  id="resetEmail"
                  type="email" 
                  className="w-full px-5 py-4 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none transition-all duration-300 text-gray-100 placeholder-gray-500 hover:bg-gray-900/70"
                  placeholder="Enter your email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  required
                  disabled={resetLoading}
                />
              </div>

              {resetMessage.text && (
                <div className={`p-4 rounded-xl border backdrop-blur-sm animate-fade-in ${
                  resetMessage.type === 'success' 
                    ? 'bg-gradient-to-r from-emerald-900/20 to-green-900/20 border-emerald-700/30' 
                    : 'bg-gradient-to-r from-red-900/20 to-rose-900/20 border-red-700/30'
                }`}>
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      resetMessage.type === 'success' ? 'bg-emerald-900/30' : 'bg-red-900/30'
                    }`}>
                      <svg className={`w-4 h-4 ${resetMessage.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {resetMessage.type === 'success' ? (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        )}
                      </svg>
                    </div>
                    <span className={`text-sm font-medium ${resetMessage.type === 'success' ? 'text-emerald-300' : 'text-red-300'}`}>
                      {resetMessage.text}
                    </span>
                  </div>
                </div>
              )}

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={closeForgotPasswordModal}
                  className="flex-1 px-4 py-4 border-2 border-gray-700 rounded-xl font-semibold text-gray-300 hover:border-gray-600 hover:text-gray-200 transition-all duration-300 hover:shadow-md"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-4 rounded-xl font-semibold hover:from-cyan-700 hover:to-blue-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                >
                  {resetLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Processing...</span>
                    </div>
                  ) : (
                    'Send Reset Link'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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

export default Login;
