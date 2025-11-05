import React from "react";

const StockModal = ({ stock, onClose }) => {
  if (!stock) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-[500px] p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
        <h2 className="text-2xl font-bold mb-2">{stock.company_name}</h2>
        <p className="text-gray-500 mb-4">{stock.symbol}</p>

        <div className="space-y-2">
          <p><span className="font-semibold">Sector:</span> {stock.sector}</p>
          <p><span className="font-semibold">Price:</span> ${stock.price ? stock.price.toFixed(2) : "N/A"}</p>
          <p><span className="font-semibold">Volume:</span> {stock.volume?.toLocaleString() || "N/A"}</p>
          <p>
            <span className="font-semibold">Change:</span>{" "}
            {stock.change_percent ? stock.change_percent.toFixed(2) + "%" : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
};

export default StockModal;
