import React, { useEffect, useRef, useState } from "react";
import { Chart, LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Tooltip, Filler } from "chart.js";

Chart.register(LineController, LineElement, PointElement, LinearScale, Title, CategoryScale, Tooltip, Filler);

const StockDetails = ({ symbol, onClose }) => {
  const [details, setDetails] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [range, setRange] = useState("1D");
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
    const isPositive = chartData[chartData.length - 1]?.price >= chartData[0]?.price;
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, isPositive ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)");
    gradient.addColorStop(1, isPositive ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)");

    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.map((d) => d.date),
        datasets: [
          {
            label: `${symbol} Price`,
            data: chartData.map((d) => d.price),
            borderColor: isPositive ? "rgb(34, 197, 94)" : "rgb(239, 68, 68)",
            backgroundColor: gradient,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointBackgroundColor: isPositive ? "rgb(34, 197, 94)" : "rgb(239, 68, 68)",
            borderWidth: 3,
            pointBorderWidth: 2,
            pointHoverBorderWidth: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1f2937',
            bodyColor: '#1f2937',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              label: function(context) {
                return `$${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          y: {
            grid: {
              color: 'rgba(0, 0, 0, 0.05)',
              drawBorder: false,
            },
            ticks: {
              callback: (value) => "$" + value.toFixed(2),
              color: '#6b7280',
              font: {
                size: 11,
              }
            },
          },
          x: {
            grid: {
              display: false,
            },
            ticks: { 
              maxTicksLimit: 8,
              color: '#6b7280',
              font: {
                size: 11,
              }
            },
          },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
        elements: {
          point: {
            hoverBackgroundColor: '#ffffff',
            hoverBorderColor: isPositive ? "rgb(34, 197, 94)" : "rgb(239, 68, 68)",
          }
        }
      },
    });
  }, [chartData, symbol, range]);

  if (loading)
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-900 to-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800/90 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-4xl p-8 border border-gray-700">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="space-y-2">
                  <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                  <div className="h-6 bg-gray-700 rounded w-1/2"></div>
                </div>
              ))}
            </div>
            <div className="h-80 bg-gray-700 rounded-xl"></div>
          </div>
        </div>
      </div>
    );

  if (!details) return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-900 to-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 max-w-md text-center border border-gray-700">
        <div className="w-16 h-16 mx-auto mb-4 text-red-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-gray-100 mb-2">Failed to Load Data</h3>
        <p className="text-gray-400 mb-6">Unable to fetch stock details for {symbol}</p>
        <button
          onClick={onClose}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20"
        >
          Close
        </button>
      </div>
    </div>
  );

  const isPositive = details.change_percent >= 0;

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-900 to-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800/95 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="p-8 border-b border-gray-700">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-100 mb-2">{details.name}</h2>
              <div className="flex items-center space-x-4">
                <span className="text-xl font-semibold text-gray-300">{details.symbol}</span>
                <span className="text-sm text-gray-400 bg-gray-700/50 px-3 py-1 rounded-full backdrop-blur-sm border border-gray-600">
                  {details.sector}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700/50 hover:bg-gray-600 flex items-center justify-center transition-all duration-300 group hover:scale-110 border border-gray-600"
            >
              <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
              <p className="text-sm text-gray-400 font-medium mb-2">Current Price</p>
              <p className="text-2xl font-bold text-gray-100">
                ${details.currentPrice?.toFixed(2) || "N/A"}
              </p>
            </div>
            <div className="bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
              <p className="text-sm text-gray-400 font-medium mb-2">Market Cap</p>
              <p className="text-2xl font-bold text-gray-100">
                {details.marketCap ? `$${(details.marketCap / 1e9).toFixed(2)}B` : "N/A"}
              </p>
            </div>
            <div className="bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-xl p-4 border border-gray-600 backdrop-blur-sm">
              <p className="text-sm text-gray-400 font-medium mb-2">Volume</p>
              <p className="text-2xl font-bold text-gray-100">
                {details.volume?.toLocaleString() || "N/A"}
              </p>
            </div>
            <div className={`bg-gradient-to-br rounded-xl p-4 border backdrop-blur-sm ${
              isPositive 
                ? "from-emerald-900/30 to-green-900/30 border-emerald-700/50" 
                : "from-red-900/30 to-rose-900/30 border-red-700/50"
            }`}>
              <p className="text-sm text-gray-400 font-medium mb-2">Change</p>
              <p className={`text-2xl font-bold ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                {details.change_percent ? `${isPositive ? "+" : ""}${details.change_percent.toFixed(2)}%` : "N/A"}
              </p>
            </div>
          </div>
        </div>

        {/* Chart Section */}
        <div className="p-8">
          {/* Range Selector */}
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-100">Price Chart</h3>
            <div className="flex space-x-2 bg-gray-700/50 p-1 rounded-xl backdrop-blur-sm border border-gray-600">
              {["1D", "5D", "1M", "3M", "1Y"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    range === r
                      ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/30"
                      : "text-gray-400 hover:text-gray-100 hover:bg-gray-600/50"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Chart Container */}
          <div className="h-80 relative bg-gradient-to-br from-gray-800/50 to-gray-900/30 rounded-2xl border border-gray-600 backdrop-blur-sm p-4">
            {chartLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-800/80 backdrop-blur-sm rounded-2xl">
                <div className="text-center">
                  <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                  <p className="text-gray-400 text-sm">Loading chart data...</p>
                </div>
              </div>
            )}
            <canvas
              ref={chartRef}
              className={chartLoading ? "opacity-0" : "opacity-100 transition-opacity duration-500"}
            ></canvas>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetails;