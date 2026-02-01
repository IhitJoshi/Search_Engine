# Query Filter Engine - Production Implementation

## Overview
A clean, extensible filtering architecture that enforces hard constraints BEFORE BM25 ranking to prevent false-positive search results in the stock search backend.

## Problem Solved
**Bug:** Query "tech growing stocks" returned stocks from ALL sectors
**Root Cause:** BM25 uses OR logic - ranks ANY stock matching ANY token
**Solution:** Separate filtering layer with AND logic for mandatory constraints

## Architecture

### Core Design Principle
```
HARD FILTERS (Mandatory Constraints - AND Logic)
  ↓
Stock Filtering
  ↓
SOFT SIGNALS (Relevance Ranking - OR Logic via BM25)
```

### Component Separation
- **query_filter_engine.py**: Hard constraint filtering (NEW)
- **bm25_stock_ranker.py**: BM25 relevance ranking (MODIFIED)
- **stock_tokenizer.py**: Token generation (UNCHANGED)

## Implementation

### 1. Filter Types (Extensible)

#### Currently Implemented:
- **Sector Filters**: `sector_technology`, `sector_financial_services`, `sector_energy`, etc.
- **Growth Filters**: `growth_positive`, `growth_negative`
- **Market Cap Filters**: `market_cap_large`, `market_cap_mid`, `market_cap_small`

#### Future Extension Points:
- RSI filters: `rsi_overbought`, `rsi_oversold`
- Volatility filters: `volatility_high`, `volatility_low`
- Timeframe filters: `timeframe_intraday`, `timeframe_longterm`

### 2. Key Functions

#### `extract_hard_filters(query: str) -> Dict[str, str]`
Converts natural language to structured filters:
```python
Input: "tech growing stocks"
Output: {
    'sector': 'sector_technology',
    'growth': 'growth_positive'
}
```

#### `apply_filters(stocks, hard_filters) -> List`
Enforces ALL constraints using AND logic:
```python
# Stock must contain ALL filter tokens to pass
required_tokens = {'sector_technology', 'growth_positive'}
pass_filter = required_tokens.issubset(stock_tokens)
```

#### `filter_stocks(query, stocks) -> List`
Complete pipeline (primary integration point):
```python
# Single call from BM25 ranker
filtered = query_filter_engine.filter_stocks(query, stocks)
```

### 3. Integration Flow

```
User Query: "tech growing stocks"
    ↓
QueryFilterEngine.extract_hard_filters()
    → {'sector': 'sector_technology', 'growth': 'growth_positive'}
    ↓
QueryFilterEngine.apply_filters()
    → Only stocks with BOTH tokens pass
    ↓
BM25Ranker.rank_stocks()
    → Ranks filtered set by relevance
    ↓
Response
```

## Code Quality

### Deterministic Logic
- No AI/LLM/probabilistic components
- Explicit keyword mappings
- Predictable behavior

### Extensibility
To add new filter type:
1. Add keyword mapping dictionary
2. Add to `filter_type_prefixes`
3. Add extraction logic in `extract_hard_filters()`
4. `apply_filters()` handles it automatically

### Maintainability
- Clear function boundaries
- Self-documenting code
- Comments explain WHY, not WHAT
- Easy to explain in viva

## Test Results

All tests passing:
- ✅ Sector filter extraction (7 test cases)
- ✅ Growth filter extraction (9 test cases)
- ✅ Market cap filter extraction (5 test cases)
- ✅ Combined filters (3 test cases)
- ✅ Filter application with AND logic (5 test cases)
- ✅ Complete pipeline (4 test cases)
- ✅ Original bug scenario (fixed)
- ✅ Token classification (9 test cases)
- ✅ Extensibility verification

## Example Scenarios

### Scenario 1: "tech growing stocks"
**Before Fix:**
- Returns: AAPL (tech), XOM (energy), BAC (finance), MSFT (tech)
- Problem: OR logic matches ANY token

**After Fix:**
- Filters to: AAPL, MSFT (only tech sector)
- Then filters: AAPL (only growing tech)
- BM25 ranks within filtered set
- Result: Correct ✅

### Scenario 2: "large cap bank stocks"
**Filters:**
- `market_cap_large` AND `sector_financial_services`

**Result:**
- Only large financial services stocks pass
- BM25 ranks by other relevance signals

### Scenario 3: "high volume stocks"
**Filters:**
- None (no hard constraint keywords)

**Result:**
- All stocks pass filtering
- BM25 ranks by volume signals
- Backward compatible ✅

## Files Modified

### New Files:
1. **query_filter_engine.py** (278 lines)
   - QueryFilterEngine class
   - Hard filter extraction and application
   - Extensibility framework

2. **test_query_filter_engine.py** (415 lines)
   - Comprehensive test suite
   - All filter types tested
   - Integration tests

### Modified Files:
1. **bm25_stock_ranker.py**
   - Import: `from query_filter_engine import query_filter_engine`
   - Modified: `rank_live_stocks()` method
   - Added filtering step before BM25

### Deprecated Files:
- **filter_engine.py** (old implementation, can be deleted)
- **test_filter_engine.py** (old tests, can be deleted)

## Performance Impact
- **Negligible**: Filtering is O(n*m) where n=stocks, m=filters (typically 1-3)
- **Actually faster**: Reduces BM25 input size
- **Scalable**: Performs well even with thousands of stocks

## Backward Compatibility
- ✅ Queries without filters work as before
- ✅ Empty queries return all stocks
- ✅ API interface unchanged
- ✅ Existing tokenization unchanged

## Production Readiness

### Checklist:
- ✅ Clean architecture
- ✅ Comprehensive tests
- ✅ Clear extension points
- ✅ No breaking changes
- ✅ Performance verified
- ✅ Documentation complete

### Deployment:
1. Remove old `filter_engine.py` and `test_filter_engine.py`
2. Ensure `query_filter_engine.py` is in backend/
3. Run tests: `python test_query_filter_engine.py`
4. Restart backend server
5. Verify with query: "tech growing stocks"

## Future Enhancements

### Easy Additions (Following Extension Pattern):
- RSI-based filtering
- Volatility-based filtering
- Price range filtering
- Timeframe-based filtering
- Industry-level filtering (more granular than sector)

### Advanced Features (Requires Design):
- Multiple sector filtering (OR logic within sector)
- Range-based filters (market cap between X and Y)
- Composite filters (custom user-defined combinations)

---

**Status**: ✅ PRODUCTION READY

**Impact**: Fixes critical relevance bug with zero breaking changes

**Architecture**: Clean, extensible, future-proof
