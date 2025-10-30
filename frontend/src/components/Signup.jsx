import React, { useState } from 'react';

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
      const response = await fetch("http://localhost:5000/api/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ 
          username: username.trim(), 
          email: email.trim(),
          password: password.trim() 
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ text: 'Account created successfully! Please login.', type: 'success' });
        setTimeout(() => {
          onSignupSuccess();
        }, 2000);
      } else {
        setMessage({ text: data.error || "Registration failed", type: 'error' });
      }
    } catch (error) {
      console.error("Signup error:", error);
      setMessage({ text: 'Cannot connect to server.', type: 'error' });
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
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
            SearchPro
          </h1>
          <p className="text-gray-600 mt-2">Your gateway to intelligent search</p>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-gray-800">Create Account</h2>
          <p className="text-gray-600 mt-2">Join thousands of users discovering smarter search</p>
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
    type="email" 
    name="email"
    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent outline-none transition-all"
    placeholder="Email"
    value={formData.email || ''}
    onChange={handleInputChange}
    required
    disabled={isLoading}
  />
  <span className="absolute right-3 top-3 text-gray-400">📧</span>
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

          <div className="relative">
            <input 
              type="password" 
              name="confirmPassword"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent outline-none transition-all"
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              disabled={isLoading}
            />
            <span className="absolute right-3 top-3 text-gray-400">🔒</span>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-gray-800 to-gray-700 text-white py-3 rounded-lg font-semibold hover:from-gray-700 hover:to-gray-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                Creating Account...
              </div>
            ) : (
              'Create Account'
            )}
          </button>

          <div className="text-center text-gray-600">
            <p>Already have an account? <button 
              type="button"
              onClick={onNavigateToLogin}
              className="text-gray-800 font-semibold hover:underline"
            >
              Sign in here
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

export default Signup;