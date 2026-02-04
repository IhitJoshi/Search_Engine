import React from "react";

const StockModal = ({ stock, onClose }) => {
  if (!stock) return null;

  const isPositive = stock.change_percent >= 0;

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-900/50 via-gray-900/40 to-black/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div className="bg-gray-800/95 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-md p-8 relative border border-gray-700 animate-fade-in">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gray-700/50 hover:bg-gray-600 flex items-center justify-center text-gray-400 hover:text-gray-200 transition-all duration-300 hover:scale-110 border border-gray-600"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-100 mb-2">{stock.company_name}</h2>
          <div className="flex items-center space-x-3">
            <span className="text-lg font-semibold text-cyan-400 bg-cyan-900/20 px-3 py-1 rounded-lg border border-cyan-700/30">
              {stock.symbol}
            </span>
            {stock.sector && (
              <span className="text-sm text-gray-400 bg-gray-700/50 px-3 py-1 rounded-lg border border-gray-600">
                {stock.sector}
              </span>
            )}
          </div>
        </div>

        {/* Price Section */}
        <div className={`mb-6 p-4 rounded-xl border-2 backdrop-blur-sm ${
          isPositive 
            ? "bg-gradient-to-br from-emerald-900/20 to-green-900/20 border-emerald-700/30" 
            : "bg-gradient-to-br from-red-900/20 to-rose-900/20 border-red-700/30"
        }`}>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-400 font-medium mb-1">Current Price</p>
              <p className={`text-2xl font-bold ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                ${stock.price ? stock.price.toFixed(2) : "N/A"}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400 font-medium mb-1">24h Change</p>
              <div className={`flex items-center space-x-1 ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                {stock.change_percent !== undefined ? (
                  <>
                    <svg className={`w-4 h-4 ${isPositive ? "text-emerald-400" : "text-red-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {isPositive ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      )}
                    </svg>
                    <span className="text-lg font-bold">
                      {Math.abs(stock.change_percent).toFixed(2)}%
                    </span>
                  </>
                ) : (
                  <span className="text-lg font-semibold text-gray-400">N/A</span>
                )}
              </div>
            </div>
          </div>
          {/* Price indicator bar */}
          <div className={`h-1.5 w-full mt-4 rounded-full ${
            isPositive 
              ? "bg-gradient-to-r from-emerald-900/50 to-emerald-600/50" 
              : "bg-gradient-to-r from-red-900/50 to-red-600/50"
          }`}>
            <div className={`h-full rounded-full transition-all duration-1000 ${
              isPositive ? "bg-gradient-to-r from-emerald-400 to-emerald-500" : "bg-gradient-to-r from-red-400 to-red-500"
            }`} style={{ width: `${Math.min(Math.abs(stock.change_percent || 0) * 10, 100)}%` }}></div>
          </div>
        </div>

        {/* Details Grid */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-900/50 to-cyan-900/50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <span className="text-sm font-medium text-gray-400">Volume</span>
              </div>
              <p className="text-lg font-bold text-gray-100">
                {stock.volume ? (
                  <span className="text-xl">{stock.volume.toLocaleString()}</span>
                ) : (
                  "N/A"
                )}
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-900/50 to-pink-900/50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <span className="text-sm font-medium text-gray-400">Market Cap</span>
              </div>
              <p className="text-lg font-bold text-gray-100">
                {stock.market_cap ? (
                  <span className="text-xl">${(stock.market_cap / 1000000).toFixed(1)}M</span>
                ) : (
                  "N/A"
                )}
              </p>
            </div>
          </div>

          {/* Additional Info */}
          <div className="bg-gradient-to-br from-gray-700/30 to-gray-800/30 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center">
              <svg className="w-4 h-4 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Stock Information
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-gray-700/50">
                <span className="text-gray-400">Ticker Symbol</span>
                <span className="font-medium text-gray-100">{stock.symbol}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-gray-700/50">
                <span className="text-gray-400">Company</span>
                <span className="font-medium text-gray-100 truncate ml-4">{stock.company_name}</span>
              </div>
              {stock.sector && (
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-400">Sector</span>
                  <span className="font-medium text-gray-100">{stock.sector}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={onClose}
          className="w-full mt-6 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white py-3 rounded-xl font-semibold transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 hover:scale-[1.02]"
        >
          Close Details
        </button>
      </div>

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

export default StockModal;