import React, { useEffect, useRef, useState } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale } from "chart.js";

Chart.register(LineController, LineElement, PointElement, LinearScale, Title, CategoryScale);

const StockDetails = ({ symbol, onClose }) => {
  const [details, setDetails] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [range, setRange] = useState("1D"); // 👈 selected range
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  // 🟢 Fetch Stock Details (basic info)
  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await fetch(`http://localhost:5000/api/stocks/${symbol}`);
        const data = await res.json();
        if (data.error) console.error("Error fetching stock details:", data.error);
        else setDetails(data.details);
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, [symbol]);

  // 🟡 Fetch Chart Data based on range
  useEffect(() => {
    const fetchChartData = async () => {
      setChartLoading(true);
      try {
        const res = await fetch(`http://localhost:5000/api/stocks/${symbol}?range=${range}`);
        const data = await res.json();
        if (data.chart) setChartData(data.chart);
      } catch (err) {
        console.error("Chart fetch error:", err);
      } finally {
        setChartLoading(false);
      }
    };

    fetchChartData();
  }, [symbol, range]);

  // 🧠 Draw Chart
  useEffect(() => {
    if (!chartData.length || !chartRef.current) return;

    if (chartInstance.current) chartInstance.current.destroy();

    const ctx = chartRef.current.getContext("2d");
    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.map((d) => d.date),
        datasets: [
          {
            label: `${symbol} (${range})`,
            data: chartData.map((d) => d.price),
            borderColor: "rgba(99, 102, 241, 1)",
            backgroundColor: "rgba(99, 102, 241, 0.2)",
            fill: true,
            tension: 0.3,
            pointRadius: 1.5,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            ticks: {
              callback: (value) => "$" + value.toFixed(2),
            },
          },
          x: {
            ticks: { maxTicksLimit: 8 },
          },
        },
      },
    });
  }, [chartData, symbol, range]);

  if (loading)
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );

  if (!details) return <div className="p-8 text-center text-red-500">Failed to load stock details.</div>;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>

        <h2 className="text-2xl font-bold mb-2">{details.name}</h2>
        <p className="text-gray-600 mb-4">{details.symbol} • {details.sector}</p>

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-500">Current Price</p>
            <p className="text-lg font-semibold">${details.currentPrice?.toFixed(2) || "N/A"}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Market Cap</p>
            <p className="text-lg font-semibold">
              {details.marketCap ? `$${(details.marketCap / 1e9).toFixed(2)}B` : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Volume</p>
            <p className="text-lg font-semibold">{details.volume?.toLocaleString() || "N/A"}</p>
          </div>
        </div>

        {/* 🕐 Range Buttons */}
        <div className="flex space-x-3 mb-3">
          {["1D", "5D", "1M", "3M", "1Y"].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                range === r
                  ? "bg-indigo-600 text-white shadow-md"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="h-64 relative">
          {chartLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 rounded animate-pulse">
              <p className="text-gray-400 text-sm">Loading chart...</p>
            </div>
          )}
          <canvas
            ref={chartRef}
            className={chartLoading ? "opacity-0" : "opacity-100 transition-opacity duration-300"}
          ></canvas>
        </div>
      </div>
    </div>
  );
};

export default StockDetails;
