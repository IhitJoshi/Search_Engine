import React, { useState, useEffect } from 'react';

const Login = ({ onLoginSuccess, onNavigateToSignup }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

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
      const response = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ 
          username: username.trim(), 
          password: password.trim() 
        })
      });

      const data = await response.json();

      if (response.ok) {
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
      setMessage({ text: 'Cannot connect to server. Make sure Flask is running on port 5000.', type: 'error' });
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
            SearchPro
          </h1>
          <p className="text-gray-600 mt-2">Your gateway to intelligent search</p>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-gray-800">Welcome Back</h2>
          <p className="text-gray-600 mt-2">Sign in to continue your search journey</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <input 
              type="text" 
              name="username"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent outline-none transition-all"
              placeholder="Username"
              value={formData.username}
              onChange={handleInputChange}
              required
              disabled={isLoading}
            />
            <span className="absolute right-3 top-3 text-gray-400">👤</span>
          </div>
          
          <div className="relative">
            <input 
              type="password" 
              name="password"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent outline-none transition-all"
              placeholder="Password"
              value={formData.password}
              onChange={handleInputChange}
              required
              disabled={isLoading}
            />
            <span className="absolute right-3 top-3 text-gray-400">🔒</span>
          </div>

          <div className="flex justify-between items-center">
            <label className="flex items-center space-x-2 text-gray-700 cursor-pointer">
              <input 
                type="checkbox" 
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
                className="rounded border-gray-300 text-gray-600 focus:ring-gray-500"
              />
              <span>Remember me</span>
            </label>
            <a href="#" className="text-gray-600 hover:text-gray-800 text-sm">
              Forgot Password?
            </a>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-gray-800 to-gray-700 text-white py-3 rounded-lg font-semibold hover:from-gray-700 hover:to-gray-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                Signing In...
              </div>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="text-center text-gray-600">
            <p>Don't have an account? <button 
              type="button"
              onClick={onNavigateToSignup}
              className="text-gray-800 font-semibold hover:underline"
            >
              Create one now
            </button></p>
          </div>
        </form>

        {message.text && (
          <div className={`mt-4 p-3 rounded-lg text-center ${
            message.type === 'success' 
              ? 'bg-green-100 text-green-700 border border-green-200' 
              : 'bg-red-100 text-red-700 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;