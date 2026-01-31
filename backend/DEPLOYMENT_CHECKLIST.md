# BM25 Stock Ranking - Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. File Verification
- [x] `stock_tokenizer.py` created
- [x] `bm25_stock_ranker.py` created
- [x] `test_bm25_ranker.py` created
- [x] `api.py` modified with BM25 integration
- [x] `app.py` enhanced with new database fields
- [x] All documentation files created

### 2. Code Quality
- [x] No syntax errors (verified with py_compile)
- [x] Type hints added
- [x] Docstrings present
- [x] Error handling implemented
- [x] Logging configured

### 3. Testing
- [x] Stock tokenization tests pass
- [x] Query tokenization tests pass
- [x] BM25 ranking tests pass
- [x] Edge cases handled
- [x] Integration tests work

### 4. Documentation
- [x] README with architecture
- [x] Integration guide
- [x] Architecture diagrams
- [x] Implementation summary
- [x] Inline code comments

---

## 🚀 Deployment Steps

### Step 1: Backup Current System
```bash
# Backup database
cp backend/stocks.db backend/stocks.db.backup

# Backup code (if not using git)
cp backend/api.py backend/api.py.backup
cp backend/app.py backend/app.py.backup
```

### Step 2: Verify Environment
```bash
cd backend

# Check Python version (3.7+)
python --version

# Verify required packages
pip list | grep -E "flask|yfinance|pandas"
```

### Step 3: Run Tests
```bash
# Run BM25 test suite
python test_bm25_ranker.py

# Expected: All tests pass ✓
```

### Step 4: Database Migration
```bash
# The enhanced schema will be created automatically
# when you start the server (app.py drops and recreates table)

# To preserve old data, export first:
# python export_db.py  # (create this if needed)
```

### Step 5: Start Server
```bash
# Start backend server
python api.py

# Expected output:
# - "Database tables created with enhanced schema"
# - "Stock system initialization completed"
# - "Starting Flask application..."
# - "Running on http://0.0.0.0:5000"
```

### Step 6: Wait for Data Population
```bash
# Background fetcher runs every 60 seconds
# Wait 1-2 minutes for initial stock data

# Check database has data
python -c "import sqlite3; conn = sqlite3.connect('stocks.db'); print(conn.execute('SELECT COUNT(*) FROM stocks').fetchone()[0]); conn.close()"

# Expected: Number > 0
```

### Step 7: Test Search Endpoint
```bash
# Test 1: Basic query
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rising tech stocks", "limit": 5}'

# Expected: JSON response with BM25 scores

# Test 2: Sector filter
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "high volume", "sector": "Technology", "limit": 3}'

# Expected: Filtered results

# Test 3: Company search
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "apple", "limit": 1}'

# Expected: AAPL in results
```

### Step 8: Monitor Logs
```bash
# Check application logs
tail -f backend/app.log

# Look for:
# - Stock fetch updates
# - BM25 ranking logs
# - No errors
```

### Step 9: Frontend Integration (Optional)
```bash
# If frontend needs updates:
# 1. Response format unchanged (backward compatible)
# 2. New field: "_score" (BM25 relevance)
# 3. New field: "ranking_method" ("bm25")
# 4. Frontend can display scores if desired
```

### Step 10: Performance Check
```bash
# Monitor query response times
# Check CPU/memory usage
# Verify <50ms query latency

# If needed, tune parameters in api.py:
# - k1 (term frequency)
# - b (length normalization)
```

---

## 🔍 Verification Checklist

### Functional Tests

- [ ] Empty query returns all stocks
- [ ] "rising stocks" returns bullish stocks
- [ ] "high volume" returns active stocks
- [ ] "tech stocks" filters by Technology sector
- [ ] Company name search works (e.g., "apple")
- [ ] Sector filter works correctly
- [ ] Scores are reasonable (>0, descending)
- [ ] Results include all required fields

### Performance Tests

- [ ] Query response < 100ms
- [ ] Database queries are fast
- [ ] No memory leaks
- [ ] Concurrent requests handled
- [ ] Background fetcher runs smoothly

### Error Handling

- [ ] Invalid query returns error message
- [ ] Empty database handled gracefully
- [ ] Missing auth returns 401
- [ ] Malformed JSON handled
- [ ] Database errors logged

---

## 📊 Monitoring

### Key Metrics to Track

1. **Query Latency**
   - Target: <50ms
   - Monitor: p50, p95, p99

2. **Database Size**
   - Current: ~50 stocks
   - Growth: Minimal (updates in place)

3. **Memory Usage**
   - Expected: ~50-100MB
   - Monitor: No leaks

4. **CPU Usage**
   - Expected: <5% per query
   - Monitor: Spikes indicate issues

5. **Error Rate**
   - Target: <1%
   - Monitor: Application logs

---

## 🐛 Troubleshooting Guide

### Issue: No Results Returned

**Symptoms**: Search returns empty results

**Solutions**:
1. Check database has data: `SELECT COUNT(*) FROM stocks`
2. Wait 60s for initial data fetch
3. Verify background fetcher is running
4. Check logs for errors

### Issue: Low Relevance Scores

**Symptoms**: Results don't match query intent

**Solutions**:
1. Review token generation logs
2. Check query tokenization output
3. Adjust keyword mappings in `stock_tokenizer.py`
4. Tune tokenizer thresholds

### Issue: Slow Queries

**Symptoms**: Response time >100ms

**Solutions**:
1. Check database indexes exist
2. Verify tokenization is fast
3. Profile BM25 scoring
4. Consider caching popular queries

### Issue: Import Errors

**Symptoms**: `ModuleNotFoundError`

**Solutions**:
1. Verify all files in `backend/` directory
2. Check Python path
3. Restart server
4. Verify file permissions

### Issue: Database Errors

**Symptoms**: SQLite errors in logs

**Solutions**:
1. Check database file exists
2. Verify schema is correct
3. Drop and recreate tables
4. Check file permissions

---

## 🔄 Rollback Plan

If issues occur, rollback:

### 1. Stop Server
```bash
# Ctrl+C or:
pkill -f "python api.py"
```

### 2. Restore Backups
```bash
# Restore code
mv backend/api.py.backup backend/api.py
mv backend/app.py.backup backend/app.py

# Restore database
mv backend/stocks.db.backup backend/stocks.db
```

### 3. Remove New Files
```bash
# Optional: Remove BM25 files
rm backend/stock_tokenizer.py
rm backend/bm25_stock_ranker.py
rm backend/test_bm25_ranker.py
```

### 4. Restart Old System
```bash
python api.py
```

---

## 📈 Success Criteria

Deployment is successful when:

- ✅ Server starts without errors
- ✅ Stock data populates within 2 minutes
- ✅ Search queries return relevant results
- ✅ Response times <50ms
- ✅ BM25 scores make sense
- ✅ No errors in logs
- ✅ Frontend works (if integrated)

---

## 🎯 Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Monitor logs for errors
- [ ] Verify stock data updates
- [ ] Test key user queries
- [ ] Check performance metrics

### Short-term (Week 1)
- [ ] Analyze query patterns
- [ ] Fine-tune BM25 parameters
- [ ] Adjust tokenizer thresholds
- [ ] Gather user feedback

### Long-term (Month 1)
- [ ] Add new market indicators
- [ ] Implement query caching
- [ ] Optimize performance
- [ ] Expand documentation

---

## 📞 Support Resources

### Documentation
- `BM25_RANKING_README.md` - Complete guide
- `INTEGRATION_GUIDE.md` - Quick start
- `ARCHITECTURE.md` - System design
- Code comments - Implementation details

### Testing
- `test_bm25_ranker.py` - Test suite
- Run tests to verify functionality

### Logs
- `backend/app.log` - Application logs
- Console output - Real-time info

---

## ✅ Final Checklist

Before considering deployment complete:

- [ ] All tests pass
- [ ] Documentation reviewed
- [ ] Backups created
- [ ] Server running stable
- [ ] Stock data populating
- [ ] Search queries working
- [ ] Performance acceptable
- [ ] No errors in logs
- [ ] Team notified
- [ ] Monitoring in place

---

**Deployment Status**: Ready ✅

**Last Verified**: 2026-02-01

**Next Review**: After first production queries
