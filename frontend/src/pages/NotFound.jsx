import React from "react";
import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black flex items-center justify-center text-white px-6">
      <div className="text-center max-w-xl">
        <h1 className="text-5xl font-bold mb-4">404</h1>
        <p className="text-lg text-gray-400 mb-8">
          The page you are looking for does not exist.
        </p>
        <Link
          to="/home"
          className="inline-flex items-center px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
