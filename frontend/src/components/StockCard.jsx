import React from "react";

const StockCard = ({ stock }) => {
  const isPositive = stock.change_percent >= 0;
  const isNegative = stock.change_percent < 0;
  
  return (
    <div className="group cursor-pointer">
      <div
        className={`relative rounded-xl p-6 border-2 transition-all duration-300 transform group-hover:-translate-y-1 group-hover:shadow-xl backdrop-blur-sm overflow-hidden ${
          stock.changed === "up"
            ? "bg-gradient-to-br from-green-50/80 to-emerald-50/60 border-green-200/80 group-hover:border-green-300"
            : stock.changed === "down"
            ? "bg-gradient-to-br from-red-50/80 to-rose-50/60 border-red-200/80 group-hover:border-red-300"
            : "bg-gradient-to-br from-white/80 to-gray-50/60 border-gray-200/80 group-hover:border-blue-300"
        }`}
      >
        {/* Background Glow Effect */}
        <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
          stock.changed === "up" ? "bg-gradient-to-br from-green-100/20 to-emerald-100/10" :
          stock.changed === "down" ? "bg-gradient-to-br from-red-100/20 to-rose-100/10" :
          "bg-gradient-to-br from-blue-100/20 to-indigo-100/10"
        }`}></div>
        
        {/* Header */}
        <div className="relative flex justify-between items-start mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold text-gray-900 truncate group-hover:text-gray-800 transition-colors">
              {stock.company_name}
            </h3>
            <p className="text-sm text-gray-500 font-medium mt-1">{stock.symbol}</p>
          </div>
          
          {/* Change Percentage Badge */}
          <div className={`flex-shrink-0 ml-3 px-3 py-1.5 rounded-full border transition-all duration-300 ${
            isPositive 
              ? "bg-green-50 border-green-200 text-green-700 group-hover:bg-green-100 group-hover:border-green-300" 
              : "bg-red-50 border-red-200 text-red-700 group-hover:bg-red-100 group-hover:border-red-300"
          }`}>
            <span className="text-sm font-semibold whitespace-nowrap">
              {stock.change_percent ? (
                <>
                  {isPositive ? "↗" : "↘"}
                  {Math.abs(stock.change_percent).toFixed(2)}%
                </>
              ) : (
                "—"
              )}
            </span>
          </div>
        </div>

        {/* Price */}
        <div className="relative mb-4">
          <p className={`text-2xl font-bold transition-all duration-300 ${
            isPositive ? "text-green-600" : "text-red-600"
          }`}>
            ${stock.price ? stock.price.toFixed(2) : "N/A"}
          </p>
          <div className={`h-1 w-8 mt-2 rounded-full transition-all duration-500 ${
            isPositive ? "bg-green-400" : "bg-red-400"
          }`}></div>
        </div>

        {/* Details */}
        <div className="relative space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500 font-medium">Volume</span>
            <span className="text-sm font-semibold text-gray-700">
              {stock.volume?.toLocaleString() || "N/A"}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500 font-medium">Sector</span>
            <span className="text-sm font-semibold text-gray-700 truncate ml-2 max-w-[120px] text-right">
              {stock.sector || "—"}
            </span>
          </div>
        </div>

        {/* Hover Indicator */}
        <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
          <svg className={`w-5 h-5 ${
            stock.changed === "up" ? "text-green-400" :
            stock.changed === "down" ? "text-red-400" :
            "text-blue-400"
          }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default StockCard;