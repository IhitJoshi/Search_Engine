import React from "react";

const StockCard = ({ stock }) => {
  const isPositive = stock.change_percent >= 0;
  
  return (
    <div className="group cursor-pointer h-full">
      <div
        className={`relative h-full rounded-xl p-5 border transition-all duration-300 transform group-hover:-translate-y-1 group-hover:shadow-xl backdrop-blur-sm ${
          stock.changed === "up"
            ? "bg-gray-800/80 border-emerald-500/40 group-hover:border-emerald-400 ring-1 ring-emerald-400/40 shadow-[0_0_20px_rgba(16,185,129,0.35)] scale-[1.02]"
            : stock.changed === "down"
            ? "bg-gray-800/80 border-red-500/40 group-hover:border-red-400 ring-1 ring-red-400/40 shadow-[0_0_20px_rgba(239,68,68,0.35)] scale-[0.98]"
            : "bg-gray-800/80 border-gray-700 group-hover:border-cyan-500/50"
        }`}
      >
        {/* Live Pulse Indicator */}
        {(stock.changed === "up" || stock.changed === "down") && (
          <div className={`absolute top-3 right-3 w-2 h-2 rounded-full ${
            stock.changed === "up" ? "bg-emerald-400" : "bg-red-400"
          } animate-pulse`}></div>
        )}

        {/* Symbol & Change Row */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-bold text-cyan-400 tracking-wide">
            {stock.symbol}
          </span>
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-semibold ${
            isPositive 
              ? "bg-emerald-900/40 text-emerald-400" 
              : "bg-red-900/40 text-red-400"
          }`}>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isPositive ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              )}
            </svg>
            <span>{stock.change_percent ? `${Math.abs(stock.change_percent).toFixed(2)}%` : "—"}</span>
          </div>
        </div>

        {/* Company Name */}
        <h3 className="text-base font-semibold text-gray-100 truncate mb-4 group-hover:text-white transition-colors">
          {stock.company_name}
        </h3>

        {/* Price */}
        <div className="flex items-baseline justify-between">
          <p className={`text-2xl font-bold ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}>
            ${stock.price ? stock.price.toFixed(2) : "N/A"}
          </p>
          {stock.volume && (
            <span className="text-xs text-gray-500">
              Vol: {(stock.volume / 1000).toFixed(0)}K
            </span>
          )}
        </div>

        {/* Sector Badge */}
        {stock.sector && (
          <div className="mt-3 pt-3 border-t border-gray-700/50">
            <span className="text-xs text-gray-500">{stock.sector}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockCard;
