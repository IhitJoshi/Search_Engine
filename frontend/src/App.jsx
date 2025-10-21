import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Signup from './components/Signup';
import Search from './components/Search';

const App = () => {
  const [currentPage, setCurrentPage] = useState('login');
  const [username, setUsername] = useState('');

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/auth/check", {
        method: "GET",
        credentials: "include"
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.logged_in) {
          setUsername(data.username);
          setCurrentPage('search');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  };

  const handleLoginSuccess = (username) => {
    setUsername(username);
    setCurrentPage('search');
  };

  const handleLogout = () => {
    setUsername('');
    setCurrentPage('login');
  };

  const navigateTo = (page) => {
    setCurrentPage(page);
  };

  return (
    <>
      {currentPage === 'login' && (
        <Login 
          onLoginSuccess={handleLoginSuccess}
          onNavigateToSignup={() => navigateTo('signup')}
        />
      )}
      
      {currentPage === 'signup' && (
        <Signup 
          onSignupSuccess={() => navigateTo('login')}
          onNavigateToLogin={() => navigateTo('login')}
        />
      )}
      
      {currentPage === 'search' && (
        <Search 
          username={username}
          onLogout={handleLogout}
        />
      )}
    </>
  );
};

export default App;