import React from "react";

const StockCard = ({ stock }) => {
  return (
    <div
      className={`rounded-xl p-6 shadow-sm border transition-all duration-700 transform hover:-translate-y-1 hover:shadow-md backdrop-blur-sm ${
        stock.changed === "up"
          ? "bg-green-50/70 border-green-300"
          : stock.changed === "down"
          ? "bg-red-50/70 border-red-300"
          : "bg-white/70 border-gray-200"
      }`}
    >
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-bold text-gray-800">
          {stock.company_name}
        </h3>
        <span
          className={`px-2 py-1 text-sm font-semibold rounded-full transition-colors duration-500 ${
            stock.change_percent >= 0
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {stock.change_percent
            ? `${stock.change_percent.toFixed(2)}%`
            : "—"}
        </span>
      </div>

      <p className="text-sm text-gray-500 mb-1">{stock.symbol}</p>
      <p
        className={`text-xl font-semibold mb-1 transition-all duration-500 ${
          stock.change_percent >= 0 ? "text-green-600" : "text-red-600"
        }`}
      >
        ${stock.price.toFixed(2)}
      </p>

      <p className="text-sm text-gray-600 mb-1">
        Volume: {stock.volume?.toLocaleString() || "N/A"}
      </p>
      <p className="text-sm text-gray-500">
        <span className="font-medium">Sector:</span>{" "}
        {stock.sector || "—"}
      </p>
    </div>
  );
};

export default StockCard;
