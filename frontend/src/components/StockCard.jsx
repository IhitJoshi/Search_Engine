import React from "react";

const StockCard = ({ stock }) => {
  const isPositive = stock.change_percent >= 0;
  const isNegative = stock.change_percent < 0;
  
  return (
    <div className="group cursor-pointer">
      <div
        className={`relative rounded-2xl p-6 border-2 transition-all duration-500 transform group-hover:-translate-y-2 group-hover:shadow-2xl backdrop-blur-sm overflow-hidden ${
          stock.changed === "up"
            ? "bg-gradient-to-br from-white/90 via-emerald-50/30 to-white/90 border-emerald-200/70 group-hover:border-emerald-300/80 group-hover:shadow-emerald-500/10"
            : stock.changed === "down"
            ? "bg-gradient-to-br from-white/90 via-rose-50/30 to-white/90 border-red-200/70 group-hover:border-red-300/80 group-hover:shadow-red-500/10"
            : "bg-gradient-to-br from-white/90 via-blue-50/20 to-white/90 border-gray-200/70 group-hover:border-blue-300/80 group-hover:shadow-blue-500/10"
        }`}
      >
        {/* Background Glow Effect */}
        <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 ${
          stock.changed === "up" 
            ? "bg-gradient-to-br from-emerald-100/30 via-emerald-50/20 to-emerald-100/10" 
            : stock.changed === "down" 
            ? "bg-gradient-to-br from-red-100/30 via-rose-50/20 to-red-100/10" 
            : "bg-gradient-to-br from-blue-100/30 via-blue-50/20 to-indigo-100/10"
        }`}></div>
        
        {/* Animated border on hover */}
        <div className={`absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 ${
          stock.changed === "up" 
            ? "via-emerald-400/10" 
            : stock.changed === "down" 
            ? "via-red-400/10" 
            : "via-blue-400/10"
        }`}></div>
        
        {/* Header */}
        <div className="relative flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0">
            <h3 className="text-xl font-bold text-gray-900 truncate group-hover:text-gray-800 transition-colors duration-300">
              {stock.company_name}
            </h3>
            <div className="flex items-center space-x-2 mt-2">
              <span className="text-sm font-semibold text-gray-700 px-3 py-1 bg-gradient-to-r from-gray-100 to-gray-50 rounded-lg border border-gray-200/50">
                {stock.symbol}
              </span>
              {stock.sector && (
                <span className="text-xs text-gray-500 px-2 py-1 bg-white/50 rounded-lg border border-gray-200/30">
                  {stock.sector}
                </span>
              )}
            </div>
          </div>
          
          {/* Change Percentage Badge */}
          <div className={`flex-shrink-0 ml-3 px-4 py-2 rounded-xl border-2 transition-all duration-300 transform group-hover:scale-105 ${
            isPositive 
              ? "bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200/80 text-emerald-700 group-hover:border-emerald-300 group-hover:shadow-emerald-200/50" 
              : "bg-gradient-to-br from-red-50 to-rose-50 border-red-200/80 text-red-700 group-hover:border-red-300 group-hover:shadow-red-200/50"
          }`}>
            <div className="flex items-center space-x-1">
              {stock.change_percent ? (
                <>
                  <svg className={`w-4 h-4 ${isPositive ? 'text-emerald-500' : 'text-red-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isPositive ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    )}
                  </svg>
                  <span className="text-sm font-bold whitespace-nowrap">
                    {Math.abs(stock.change_percent).toFixed(2)}%
                  </span>
                </>
              ) : (
                <span className="text-sm font-semibold">—</span>
              )}
            </div>
          </div>
        </div>

        {/* Price Section */}
        <div className="relative mb-6">
          <div className="flex items-end space-x-2">
            <p className={`text-3xl font-bold transition-all duration-300 group-hover:scale-105 ${
              isPositive 
                ? "text-emerald-600 group-hover:text-emerald-700" 
                : "text-red-600 group-hover:text-red-700"
            }`}>
              ${stock.price ? stock.price.toFixed(2) : "N/A"}
            </p>
            <span className="text-sm text-gray-500 mb-1">USD</span>
          </div>
          <div className={`h-1.5 w-12 mt-3 rounded-full transition-all duration-700 group-hover:w-16 ${
            isPositive 
              ? "bg-gradient-to-r from-emerald-400 to-emerald-500 group-hover:from-emerald-500 group-hover:to-emerald-600" 
              : "bg-gradient-to-r from-red-400 to-red-500 group-hover:from-red-500 group-hover:to-red-600"
          }`}></div>
        </div>

        {/* Details Grid */}
        <div className="relative">
          <div className="grid grid-cols-2 gap-4 p-4 bg-gradient-to-br from-gray-50/50 to-white/30 rounded-xl border border-gray-200/30 backdrop-blur-sm">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 rounded-md bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
                  <svg className="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <span className="text-xs font-medium text-gray-500">Volume</span>
              </div>
              <p className="text-sm font-semibold text-gray-700 pl-8">
                {stock.volume ? (
                  <span className="font-bold">{stock.volume.toLocaleString()}</span>
                ) : (
                  "N/A"
                )}
              </p>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 rounded-md bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                  <svg className="w-3 h-3 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <span className="text-xs font-medium text-gray-500">Market Cap</span>
              </div>
              <p className="text-sm font-semibold text-gray-700 pl-8">
                {stock.market_cap ? (
                  <span className="font-bold">${(stock.market_cap / 1000000).toFixed(1)}M</span>
                ) : (
                  "—"
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Hover Action Indicator */}
        <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-500 transform translate-x-4 group-hover:translate-x-0">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
            stock.changed === "up" 
              ? "bg-gradient-to-br from-emerald-500 to-green-500 shadow-emerald-500/30" 
              : stock.changed === "down" 
              ? "bg-gradient-to-br from-red-500 to-rose-500 shadow-red-500/30" 
              : "bg-gradient-to-br from-blue-500 to-indigo-500 shadow-blue-500/30"
          }`}>
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </div>
        </div>

        {/* Live Pulse Indicator */}
        {(stock.changed === "up" || stock.changed === "down") && (
          <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
            stock.changed === "up" ? "bg-emerald-500" : "bg-red-500"
          } animate-pulse`}>
            <div className={`absolute inset-0 rounded-full ${
              stock.changed === "up" ? "bg-emerald-400" : "bg-red-400"
            } animate-ping`}></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockCard;