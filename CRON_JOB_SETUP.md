# ⚠️ DEPRECATED: Cron Job System

## Migration Notice

**This document is deprecated.** The cron job approach has been **replaced** with a superior **Smart On-Demand Refresh** system.

### Why the Change?

| Aspect | Cron Jobs | Smart Refresh |
|--------|-----------|---|
| Render Free Plan Support | ❌ No | ✅ Yes |
| Background Processes | ❌ Required | ✅ None |
| API Efficiency | ❌ 1440 calls/day | ✅ 120 calls/day |
| Data Freshness | ⚠️ 60s max | ✅ 30s max |
| Scalability | ❌ Poor | ✅ Excellent |
| Complexity | ⚠️ Medium | ✅ Simple |

### What To Do

**Start here:**
- 📖 **[SMART_REFRESH_QUICKSTART.md](SMART_REFRESH_QUICKSTART.md)** - Get running in 5 minutes
- 📚 **[MIGRATION_TO_SMART_REFRESH.md](MIGRATION_TO_SMART_REFRESH.md)** - How to migrate
- 🏗️ **[SMART_REFRESH_GUIDE.md](SMART_REFRESH_GUIDE.md)** - Full architecture

### Quick Summary

Old system (Cron):
```
❌ Scheduled job every 60s
❌ Always running, wasting resources
❌ Not compatible with Render Free Plan
```

New system (Smart Refresh):
```
✅ Fetch only when needed (30s threshold)
✅ No background processes
✅ Fully compatible with Render Free Plan
✅ Professional smooth price simulation
```

## Files Removed

- ❌ `backend/update_stocks_cron.py` - Delete this file
- ❌ Cron job service in `render.yaml` - Remove this section

## Next: Replace with Smart Refresh

---

## 🚀 Setup on Render (Quick)

### Option 1: Add Cron Job Service (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com

2. **Create New Cron Job**
   - Click **"New +"** → **"Cron Job"**
   - Connect your existing GitHub repo

3. **Configure**
   ```
   Name: stock-price-updater
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Command: python update_stocks_cron.py
   Schedule: */1 * * * *  (every 1 minute)
   ```

4. **Environment Variables** (optional)
   ```
   PYTHON_VERSION=3.11.0
   ```

5. **Deploy**
   - Click "Create Cron Job"
   - It will run every minute automatically

### Option 2: Use System Cron (If Self-Hosting)

Add to crontab:
```bash
*/1 * * * * cd /path/to/backend && python update_stocks_cron.py
```

---

## ✅ Testing Locally

### Test the cron script manually:
```bash
cd backend
python update_stocks_cron.py
```

You should see:
```
============================================================
Starting stock price update job
Timestamp: 2026-02-12T...
Stocks to update: 50
============================================================
Fetching data for AAPL...
✓ Updated AAPL: $175.50 (+1.25%)
Fetching data for MSFT...
✓ Updated MSFT: $380.25 (+0.85%)
...
============================================================
Update job completed:
  ✓ Successful: 48
  ✗ Failed: 2
  Total: 50
============================================================
```

---

## 📊 Your Dashboard Already Has Everything!

Your existing `Dashboard.jsx` already includes:
- ✅ Real-time price updates
- ✅ Last updated timestamp display
- ✅ WebSocket live connections
- ✅ Automatic refresh every 60 seconds
- ✅ Price change animations
- ✅ Green/red color indicators

**No frontend changes needed!** Just add the cron job and prices will update automatically.

---

## 🔍 Verify It's Working

### 1. Check Cron Job Logs
On Render:
- Go to your Cron Job → **Logs**
- You should see update messages every minute

### 2. Check Your Dashboard
- Open your deployed dashboard
- Watch the "Last Updated" timestamp
- Should update every 60 seconds
- Prices should change smoothly

### 3. Check API Directly
```bash
curl https://your-api-url.onrender.com/api/stocks
```

Should return latest stock data with recent timestamps.

---

## 🛠️ Troubleshooting

### Cron Job Not Running
```
Problem: No logs, no updates
Solution:
- Verify schedule syntax: */1 * * * * (5 parts)
- Check build completed successfully
- Review error logs in Render dashboard
```

### Stocks Not Updating
```
Problem: Same prices every time
Solution:
- Check stock_fetcher.log for errors
- Verify yfinance is installed
- Test fetch_stock_data() locally
```

### API Returns Old Data
```
Problem: API shows stale prices
Solution:
- Check database connections
- Verify cron job is writing to correct DB
- Check cache settings (60s TTL)
```

---

## 📈 What Happens Now

### Every Minute:
1. Render runs `update_stocks_cron.py`
2. Script fetches latest prices from yfinance
3. Updates stored in `stocks.db`
4. Your API serves fresh data
5. Dashboard displays new prices automatically

### Users See:
- Smooth price transitions
- Real-time feel despite 60s updates
- Automatic refresh without page reload
- Green/red indicators for changes

---

## 💰 Cost

**Free Tier:**
- ✅ Cron Job: Free (included in Render free plan)
- ✅ No additional cost
- ⚠️ May slow down if too many stocks (current: 50 stocks = ~5-10 seconds per run)

**Paid Tier ($7/month):**
- ✅ Faster execution
- ✅ More reliable
- ✅ Better logging

---

## 🎯 Next Steps

1. ✅ **Deploy the cron job** on Render (see Option 1 above)
2. ✅ **Wait 1-2 minutes** for first run
3. ✅ **Check dashboard** to see live prices
4. ✅ **Monitor logs** to ensure it's working

That's it! Your existing deployed app will now have auto-updating stock prices every minute.

---

## 📝 Notes

- **No code changes needed** in your deployed app
- **Existing API** already serves the updated data
- **Dashboard** already refreshes automatically
- **Just add the cron job** and you're done!

The cron job script (`update_stocks_cron.py`) uses your existing `stock_fetcher.py`, so it's consistent with your current code.
