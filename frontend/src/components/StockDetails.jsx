import React, { useEffect, useRef, useState } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale } from "chart.js";

Chart.register(LineController, LineElement, PointElement, LinearScale, Title, CategoryScale);

const StockDetails = ({ symbol, onClose }) => {
  const [details, setDetails] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await fetch(`http://localhost:5000/api/stocks/${symbol}`);
        const data = await res.json();

        if (data.error) {
          console.error("Error fetching stock details:", data.error);
        } else {
          setDetails(data.details);
          setChartData(data.chart);
        }
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();

    // Cleanup chart when unmounting
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [symbol]);

  // 🟢 Draw Chart
  useEffect(() => {
    if (!chartData.length || !chartRef.current) return;

    // Destroy previous chart before creating new
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext("2d");
    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.map((d) => d.date),
        datasets: [
          {
            label: `${symbol} Price`,
            data: chartData.map((d) => d.price),
            borderColor: "rgba(99, 102, 241, 1)",
            backgroundColor: "rgba(99, 102, 241, 0.2)",
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: false },
        },
      },
    });
  }, [chartData, symbol]);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading stock details...</div>;
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

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-500">Current Price</p>
            <p className="text-lg font-semibold">${details.currentPrice?.toFixed(2) || "N/A"}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Market Cap</p>
            <p className="text-lg font-semibold">{details.marketCap ? `$${(details.marketCap / 1e9).toFixed(2)}B` : "N/A"}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Volume</p>
            <p className="text-lg font-semibold">{details.volume?.toLocaleString() || "N/A"}</p>
          </div>
        </div>

        <div className="h-64">
          <canvas ref={chartRef}></canvas>
        </div>
      </div>
    </div>
  );
};

export default StockDetails;
