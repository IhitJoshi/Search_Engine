import React, { useEffect, useRef, useState } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale } from "chart.js";

Chart.register(LineController, LineElement, PointElement, LinearScale, Title, CategoryScale);

const StockDetails = ({ symbol, onClose }) => {
  const [details, setDetails] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    const fetchDetails = async () => {
      const startTime = performance.now();
      try {
        const res = await fetch(`http://localhost:5000/api/stocks/${symbol}`);
        const data = await res.json();

        if (data.error) {
          console.error("Error fetching stock details:", data.error);
        } else {
          // Show details immediately
          setDetails(data.details);
          setLoading(false);
          
          // Load chart data separately for progressive rendering
          setTimeout(() => {
            setChartData(data.chart);
            setChartLoading(false);
            const loadTime = performance.now() - startTime;
            console.log(`✅ Stock details loaded in ${loadTime.toFixed(0)}ms`);
          }, 0);
        }
      } catch (err) {
        console.error("Fetch error:", err);
        setLoading(false);
        setChartLoading(false);
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

  // 🟢 Draw Chart (optimized)
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
            pointRadius: 2, // Smaller points for faster rendering
            pointHoverRadius: 5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 400, // Faster animation
        },
        plugins: {
          legend: {
            display: false, // Hide legend for cleaner look
          },
        },
        scales: {
          y: { 
            beginAtZero: false,
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(2);
              }
            }
          },
          x: {
            ticks: {
              maxTicksLimit: 8, // Limit ticks for performance
            }
          }
        },
      },
    });
  }, [chartData, symbol]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="h-16 bg-gray-200 rounded"></div>
              <div className="h-16 bg-gray-200 rounded"></div>
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }
  
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

        <div className="h-64 relative">
          {chartLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 rounded animate-pulse">
              <div className="text-gray-400">
                <svg className="animate-spin h-8 w-8 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-sm">Loading chart...</p>
              </div>
            </div>
          ) : null}
          <canvas ref={chartRef} className={chartLoading ? 'opacity-0' : 'opacity-100 transition-opacity duration-300'}></canvas>
        </div>
      </div>
    </div>
  );
};

export default StockDetails;
