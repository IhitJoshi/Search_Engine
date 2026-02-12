/**
 * Smart On-Demand Refresh - Frontend Implementation
 * 
 * Architecture:
 * 1. Poll backend every 5 seconds for fresh data
 * 2. Smart refresh on backend: only fetches if data > 30s old
 * 3. Simulate smooth prices every 2.5 seconds
 * 4. Update chart every 2-3 seconds
 * 5. Smooth transitions when real data arrives
 */

// ==========================================
// Configuration
// ==========================================

const API_BASE = 'http://localhost:5000/api'; // Update to your Render URL
const POLLING_INTERVAL = 5000; // 5 seconds
const SIMULATION_INTERVAL = 2500; // 2.5 seconds
const CHART_UPDATE_INTERVAL = 2500; // 2.5 seconds
const CHART_HISTORY_SIZE = 20; // Keep last 20 data points

// ==========================================
// State Management
// ==========================================

let stocksState = {
  // Real prices from API
  realPrices: {},
  // Displayed prices (simulated between updates)
  displayedPrices: {},
  // Chart history
  chartHistory: {},
  // Last update timestamp
  lastApiUpdate: Date.now(),
  // Refresh metrics
  refreshMetrics: {}
};

// ==========================================
// Timers Reference
// ==========================================

let pollingTimer = null;
let simulationTimer = null;
let chartUpdateTimer = null;
let chartInstance = null;

// ==========================================
// API Functions
// ==========================================

/**
 * Fetch stocks from backend with smart refresh
 * Backend decides whether to fetch fresh data or return cache
 */
async function fetchStocks() {
  try {
    const response = await fetch(`${API_BASE}/stocks`);
    const result = await response.json();

    if (!result.data) {
      console.error('Error fetching stocks:', result.error);
      return [];
    }

    // Update real prices from API
    const stocks = result.data;
    for (const stock of stocks) {
      stocksState.realPrices[stock.symbol] = stock.price;
      
      // Initialize displayed prices if not set
      if (!stocksState.displayedPrices[stock.symbol]) {
        stocksState.displayedPrices[stock.symbol] = stock.price;
      }

      // Initialize chart history
      if (!stocksState.chartHistory[stock.symbol]) {
        stocksState.chartHistory[stock.symbol] = [];
      }
    }

    // Update metrics
    if (result.meta) {
      stocksState.refreshMetrics = result.meta;
      updateRefreshStatus();
    }

    stocksState.lastApiUpdate = Date.now();
    return stocks;

  } catch (error) {
    console.error('API Error:', error);
    return [];
  }
}

/**
 * Simulate smooth price movements between API updates
 * This creates the professional "real-time" feel
 */
function simulatePrices(stocks) {
  for (const stock of stocks) {
    const symbol = stock.symbol;
    const realPrice = stocksState.realPrices[symbol] || stock.price;
    const displayedPrice = stocksState.displayedPrices[symbol] || stock.price;

    // If we're very close to real price, snap to it
    const diff = Math.abs(realPrice - displayedPrice);
    if (diff < 0.01) {
      stocksState.displayedPrices[symbol] = realPrice;
      continue;
    }

    // Smooth transition: move 30% of the way toward real price
    const newDisplayedPrice = displayedPrice + (realPrice - displayedPrice) * 0.3;

    // Add micro-fluctuation (+/- 0.15%) for realism
    const microFluctuation = realPrice * (Math.random() - 0.5) * 0.003;
    const finalPrice = newDisplayedPrice + microFluctuation;

    stocksState.displayedPrices[symbol] = finalPrice;
  }
}

/**
 * Update chart data with history window (last 20 points)
 */
function updateChartHistory(stocks) {
  const timeLabel = new Date().toLocaleTimeString();

  for (const stock of stocks) {
    const symbol = stock.symbol;
    const displayedPrice = stocksState.displayedPrices[symbol] || stock.price;

    // Add to history
    if (!stocksState.chartHistory[symbol]) {
      stocksState.chartHistory[symbol] = [];
    }

    stocksState.chartHistory[symbol].push({
      time: timeLabel,
      price: Math.round(displayedPrice * 100) / 100 // Round to 2 decimals
    });

    // Keep only last 20 points
    if (stocksState.chartHistory[symbol].length > CHART_HISTORY_SIZE) {
      stocksState.chartHistory[symbol].shift();
    }
  }
}

// ==========================================
// UI Functions
// ==========================================

/**
 * Render stocks grid with simulated prices
 */
function renderStocks(stocks) {
  const grid = document.getElementById('stocksGrid');

  if (!stocks || stocks.length === 0) {
    grid.innerHTML = '<div class="loading">No stocks found</div>';
    return;
  }

  grid.innerHTML = stocks.map(stock => {
    const displayedPrice = stocksState.displayedPrices[stock.symbol] || stock.price;
    const change = stock.change_percent || 0;
    const changeClass = change >= 0 ? 'positive' : 'negative';
    const changeSymbol = change >= 0 ? '📈' : '📉';

    return `
      <div class="stock-card" onclick="openModal('${stock.symbol}', ${JSON.stringify(stock).replace(/'/g, '&#39;')})">
        <div class="stock-header">
          <span class="stock-symbol">${stock.symbol}</span>
          <span class="stock-sector">${stock.sector}</span>
        </div>
        <div class="stock-name">${stock.company_name}</div>
        <span class="price">$${displayedPrice.toFixed(2)}</span>
        <div class="stock-info-row">
          <span class="info-label">Change</span>
          <span class="info-value change ${changeClass}">${changeSymbol} ${change > 0 ? '+' : ''}${change.toFixed(2)}%</span>
        </div>
        <div class="stock-info-row">
          <span class="info-label">Volume</span>
          <span class="info-value">${(stock.volume / 1000000).toFixed(1)}M</span>
        </div>
      </div>
    `;
  }).join('');

  // Update stock count
  document.getElementById('stockCount').textContent = stocks.length;
}

/**
 * Update refresh status header
 */
function updateRefreshStatus() {
  const metrics = stocksState.refreshMetrics;

  if (metrics.last_refresh_seconds_ago !== undefined) {
    const seconds = Math.round(metrics.last_refresh_seconds_ago);
    document.getElementById('lastRefresh').textContent = 
      `⏱️ Last Refresh: ${seconds}s ago`;

    // Show if data needs refresh
    if (metrics.needs_refresh) {
      document.getElementById('dataFreshness').textContent = '🟡 Data Stale (will refresh)';
      document.getElementById('dataFreshness').style.color = '#ffa500';
    } else {
      document.getElementById('dataFreshness').textContent = '🟢 Data Fresh';
      document.getElementById('dataFreshness').style.color = '#00ff88';
    }
  }
}

/**
 * Open stock detail modal
 */
function openModal(symbol, stock) {
  const modal = document.getElementById('detailModal');
  const chartHistory = stocksState.chartHistory[symbol] || [];

  document.getElementById('modalTitle').textContent = `${symbol} - ${stock.company_name}`;
  document.getElementById('modalPrice').textContent = 
    `$${(stocksState.displayedPrices[symbol] || stock.price).toFixed(2)}`;
  document.getElementById('modalChange').textContent = 
    `${stock.change_percent > 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%`;
  document.getElementById('modalChange').className = 
    stock.change_percent >= 0 ? 'change positive' : 'change negative';
  document.getElementById('modalVolume').textContent = 
    `${(stock.volume / 1000000).toFixed(2)}M`;
  document.getElementById('modalUpdated').textContent = 
    new Date(stock.last_updated).toLocaleTimeString();

  modal.style.display = 'flex';

  // Update chart
  updateChart(symbol, chartHistory, stock.price);
}

/**
 * Close modal
 */
function closeModal() {
  document.getElementById('detailModal').style.display = 'none';
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

/**
 * Update or create chart
 */
function updateChart(symbol, history, currentPrice) {
  const canvas = document.getElementById('stockChart');
  const ctx = canvas.getContext('2d');

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy();
  }

  // Prepare data
  const labels = history.map(h => h.time);
  const data = history.map(h => h.price);
  const isPositive = data.length > 0 && data[data.length - 1] >= data[0];

  // Create gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, isPositive ? 'rgba(0, 255, 136, 0.3)' : 'rgba(255, 51, 51, 0.3)');
  gradient.addColorStop(1, isPositive ? 'rgba(0, 255, 136, 0.05)' : 'rgba(255, 51, 51, 0.05)');

  // Create chart
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `${symbol} Price`,
        data: data,
        borderColor: isPositive ? 'rgb(0, 255, 136)' : 'rgb(255, 51, 51)',
        backgroundColor: gradient,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: isPositive ? 'rgb(0, 255, 136)' : 'rgb(255, 51, 51)',
        borderWidth: 2,
        pointHoverRadius: 6,
      }]
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
          titleColor: '#000',
          bodyColor: '#000',
          borderColor: '#e0e0e0',
          borderWidth: 1,
          padding: 10,
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
          grid: { color: 'rgba(0, 0, 0, 0.1)' },
          ticks: {
            callback: (value) => '$' + value.toFixed(2),
            color: '#888'
          }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#888',
            maxTicksLimit: 5
          }
        }
      }
    }
  });
}

// ==========================================
// Main Update Loop
// ==========================================

/**
 * Main update function - orchestrates all updates
 */
async function runUpdateCycle() {
  try {
    // Step 1: Fetch fresh data from smart refresh API
    const stocks = await fetchStocks();

    if (stocks.length === 0) return;

    // Step 2: Simulate prices between updates
    simulatePrices(stocks);

    // Step 3: Update chart history
    updateChartHistory(stocks);

    // Step 4: Render UI with simulated prices
    renderStocks(stocks);

  } catch (error) {
    console.error('Update cycle error:', error);
  }
}

/**
 * Separate chart update timer (every 2-3 seconds)
 */
function startChartUpdater() {
  chartUpdateTimer = setInterval(() => {
    // If modal is open, update the chart
    const modal = document.getElementById('detailModal');
    if (modal && modal.style.display === 'flex') {
      // Chart is already being updated by the modal
      // This just ensures continuous smooth updates
    }
  }, CHART_UPDATE_INTERVAL);
}

/**
 * Start polling for new data (every 5 seconds)
 */
function startPolling() {
  pollingTimer = setInterval(runUpdateCycle, POLLING_INTERVAL);
  // Run immediately on start
  runUpdateCycle();
}

/**
 * Start simulation loop (every 2.5 seconds)
 */
function startSimulation() {
  simulationTimer = setInterval(async () => {
    // Get current stocks displayed
    const stocks = document.querySelectorAll('.stock-card');
    const stockList = [];

    // Get stock data from API response
    try {
      const response = await fetch(`${API_BASE}/stocks`);
      const result = await response.json();
      if (result.data) {
        // Simulate prices
        simulatePrices(result.data);
        // Re-render with simulated prices
        renderStocks(result.data);
      }
    } catch (error) {
      console.error('Simulation error:', error);
    }
  }, SIMULATION_INTERVAL);
}

/**
 * Cleanup all timers
 */
function cleanup() {
  if (pollingTimer) clearInterval(pollingTimer);
  if (simulationTimer) clearInterval(simulationTimer);
  if (chartUpdateTimer) clearInterval(chartUpdateTimer);
  if (chartInstance) chartInstance.destroy();
}

// ==========================================
// Event Listeners
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Smart On-Demand Refresh Dashboard Started');
  console.log('📊 Polling: 5s | Simulation: 2.5s | Chart: 2.5s');

  // Start polling immediately
  startPolling();

  // Manual refresh button
  document.getElementById('refreshBtn').addEventListener('click', async () => {
    const btn = document.getElementById('refreshBtn');
    btn.classList.add('refreshing');
    await runUpdateCycle();
    btn.classList.remove('refreshing');
  });

  // Search functionality
  document.getElementById('searchInput').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.stock-card');
    
    cards.forEach(card => {
      const symbol = card.querySelector('.stock-symbol').textContent.toLowerCase();
      const name = card.querySelector('.stock-name').textContent.toLowerCase();
      
      card.style.display = 
        symbol.includes(query) || name.includes(query) ? 'block' : 'none';
    });
  });

  // Close modal on outside click
  document.getElementById('detailModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('detailModal')) {
      closeModal();
    }
  });
});

// Cleanup on page unload
window.addEventListener('beforeunload', cleanup);

// ==========================================
// Expose functions globally for debugging
// ==========================================

window.getStocks = () => stocksState;
window.getMetrics = () => stocksState.refreshMetrics;
window.forceRefresh = runUpdateCycle;
